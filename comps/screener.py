"""Load a Screener.in "Export to Excel" workbook into a small dataclass.

Layout, as seen in real exports (version 2.1): the "Data Sheet" has column A labels and section header rows
META, PROFIT & LOSS, Quarters, BALANCE SHEET, "CASH FLOW:", "PRICE:" and "DERIVED:" (note the trailing colons;
PRICE and DERIVED carry data on the header row itself). Each time-series section (P&L, Quarters, Balance
sheet, Cash flow) has a "Report Date" row of dates in columns B onwards, then one labelled row per item;
earlier columns may be blank for young companies. The same labels ("Sales", "Net profit", ...) repeat across
sections, so rows are looked up by label *inside* a section. Labels are matched ignoring case, repeated
spaces and a trailing colon. A missing label raises ValueError. Values are rupees crore, except per-share
data and share counts.

META "Number of shares" is a formula (=IF(B9>0, B9/B8, 0)) that has no cached value in the export, so it
reads as None. The share count is therefore taken, in order, from: a cached META value; Market
Capitalization / Current Price (rupees crore / rupees = crore shares); DERIVED "Adjusted Equity Shares in
Cr"; the latest balance-sheet "No. of Equity Shares" (absolute, and rounded to the nearest 10 lakh).
"""
from __future__ import annotations

import datetime as dt
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException

SECTIONS = {"meta": "META", "profit & loss": "PROFIT & LOSS", "quarters": "Quarters",
            "balance sheet": "BALANCE SHEET", "cash flow": "CASH FLOW", "price": "PRICE", "derived": "DERIVED"}
DATA_ON_HEADER = {"price", "derived"}
HEADER_LABEL = "report date"
BLANK_IS_ZERO = {"other_income"}  # Screener leaves a nil Other Income cell empty (seen in real exports)
ADJUSTED_SHARES_LABEL = "Adjusted Equity Shares in Cr"

# item key -> (accepted labels, required)
PNL_ROWS = {
    "sales": (("Sales",), True),
    "other_income": (("Other Income",), True),
    "depreciation": (("Depreciation",), True),
    "interest": (("Interest",), True),
    "pbt": (("Profit before tax",), True),
    "tax": (("Tax",), False),
    "net_profit": (("Net profit",), True),
    "dividend": (("Dividend Amount",), False),
}
BALANCE_ROWS = {
    "equity_capital": (("Equity Share Capital",), True),
    "reserves": (("Reserves",), True),
    "borrowings": (("Borrowings",), True),
    "cash": (("Cash & Bank", "Cash and Bank"), True),
    "inventory": (("Inventory",), False),
    "receivables": (("Receivables",), False),
    "investments": (("Investments",), False),
    "equity_shares": (("No. of Equity Shares",), False),
}
QUARTER_ROWS = {key: (labels, False) for key, (labels, _) in PNL_ROWS.items()
                if key in ("sales", "other_income", "depreciation", "interest", "pbt", "net_profit")}

META_LABELS = {
    "shares": ("Number of shares", "No. of shares"),
    "face_value": ("Face Value",),
    "price": ("Current Price",),
    "market_cap": ("Market Capitalization",),
}

CRORE = 1e7
SHARES_ABSOLUTE_THRESHOLD = 1e5  # a share count above this is taken to be an absolute number, not crore


@dataclass
class ScreenerData:
    """What the rest of the package needs from one workbook. Money in rupees crore, shares in crore."""
    symbol: str
    name: str | None
    shares_cr: float | None
    face_value: float | None
    price: float | None
    market_cap: float | None
    annual: dict[str, dict[int, float]]            # item -> {fiscal year: value}
    quarterly: dict[str, dict[dt.date, float]]     # item -> {quarter-end date: value}


def to_crore(shares: float) -> float:
    """Share count in crore. Screener reports shares in absolute numbers (e.g. 88,78,00,000) or crore
    (88.78); anything at or above 1e5 is treated as absolute and divided by 1e7. Every company here has
    well under 1e5 crore shares, so the two cases cannot be confused."""
    return shares / CRORE if shares >= SHARES_ABSOLUTE_THRESHOLD else shares


def _norm(text: Any) -> str:
    """Lower-case a label, collapse whitespace and drop a trailing colon."""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().rstrip(":").strip().lower()


def _num(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if value == value else None
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").replace("%", "").strip())
        except ValueError:
            return None
    return None


def _as_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%b-%y", "%b-%Y", "%b %Y"):
            try:
                return dt.datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None


def _split_sections(rows: list[list[Any]]) -> dict[str, list[list[Any]]]:
    """Group rows by section. A section header is a row whose only filled cell is a known section name.
    Rows before the first header are kept under the key ''."""
    sections: dict[str, list[list[Any]]] = {"": []}
    current = ""
    for row in rows:
        label = _norm(row[0]) if row else ""
        header_only = all(cell in (None, "") for cell in row[1:])
        # PRICE and DERIVED rows carry their data on the header row itself
        if label in SECTIONS and (header_only or label in DATA_ON_HEADER):
            current = label
            sections.setdefault(current, [])
        else:
            sections[current].append(row)
    return sections


def _series(sections: dict[str, list[list[Any]]], section: str, spec: dict, filename: str,
            required_section: bool = True) -> dict[str, dict[dt.date, float]]:
    """Read the labelled rows of one section as {item: {report date: value}}."""
    body = sections.get(section)
    if body is None:
        if required_section:
            raise ValueError(f"{filename}: section '{SECTIONS[section]}' not found in the Data Sheet")
        return {}
    header = next((row for row in body if _norm(row[0]) == HEADER_LABEL), None)
    if header is None:
        raise ValueError(f"{filename}: no 'Report Date' row in section '{SECTIONS[section]}'")
    columns = [(i, _as_date(cell)) for i, cell in enumerate(header) if i > 0]
    columns = [(i, d) for i, d in columns if d is not None]
    out: dict[str, dict[dt.date, float]] = {}
    for key, (labels, required) in spec.items():
        wanted = {_norm(label) for label in labels}
        row = next((r for r in body if _norm(r[0]) in wanted), None)
        if row is None:
            if required:
                raise ValueError(f"{filename}: row '{labels[0]}' not found in section '{SECTIONS[section]}'")
            continue
        values = {d: _num(row[i]) if i < len(row) else None for i, d in columns}
        if key in BLANK_IS_ZERO:
            values = {d: 0.0 if v is None else v for d, v in values.items()}
        out[key] = {d: v for d, v in values.items() if v is not None}
    return out


def _meta(sections: dict[str, list[list[Any]]], labels: tuple[str, ...]) -> float | None:
    wanted = {_norm(label) for label in labels}
    for row in sections.get("meta", []) + sections.get("", []):
        if _norm(row[0]) in wanted:
            for cell in row[1:]:
                value = _num(cell)
                if value is not None:
                    return value
    return None


def _derived_shares(sections: dict[str, list[list[Any]]]) -> float | None:
    """Latest value of the DERIVED 'Adjusted Equity Shares in Cr' row (already in crore)."""
    for row in sections.get("derived", []):
        if _norm(row[0]) == _norm(ADJUSTED_SHARES_LABEL):
            values = [v for v in (_num(cell) for cell in row[1:]) if v is not None]
            if values:
                return values[-1]
    return None


def _company_name(sections: dict[str, list[list[Any]]]) -> str | None:
    for row in sections.get("", []) + sections.get("meta", []):
        if _norm(row[0]) == "company name" and len(row) > 1 and row[1]:
            return str(row[1]).strip()
    return None


def load_screener(path: str | Path, symbol: str | None = None) -> ScreenerData:
    """Read a Screener export. `symbol` defaults to the upper-cased file name (e.g. TITAN.xlsx -> TITAN)."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Screener workbook not found: {path}")
    try:
        workbook = openpyxl.load_workbook(path, data_only=True)
    except (zipfile.BadZipFile, InvalidFileException) as error:
        raise ValueError(f"{path.name}: not a readable .xlsx workbook") from error
    try:
        sheet = next((ws for ws in workbook.worksheets if _norm(ws.title) == "data sheet"), None)
        if sheet is None:
            raise ValueError(f"{path.name}: no 'Data Sheet' sheet (found: {', '.join(workbook.sheetnames)})")
        rows = [list(row) for row in sheet.iter_rows(values_only=True)]
    finally:
        workbook.close()

    sections = _split_sections(rows)
    pnl = _series(sections, "profit & loss", PNL_ROWS, path.name)
    balance = _series(sections, "balance sheet", BALANCE_ROWS, path.name)
    quarters = _series(sections, "quarters", QUARTER_ROWS, path.name, required_section=False)

    annual = {key: {d.year: v for d, v in series.items()} for key, series in {**pnl, **balance}.items()}

    price = _meta(sections, META_LABELS["price"])
    market_cap = _meta(sections, META_LABELS["market_cap"])
    shares_cr = None
    cached = _meta(sections, META_LABELS["shares"])    # None in real exports: the cell is an uncached formula
    if cached:
        shares_cr = to_crore(cached)
    elif market_cap and price and market_cap > 0 and price > 0:
        shares_cr = market_cap / price                 # rupees crore / rupees = crore shares
    else:
        derived = _derived_shares(sections)
        if derived:
            shares_cr = derived
        elif annual.get("equity_shares"):
            shares_cr = to_crore(annual["equity_shares"][max(annual["equity_shares"])])
    return ScreenerData(
        symbol=(symbol or path.stem).upper(),
        name=_company_name(sections),
        shares_cr=shares_cr,
        face_value=_meta(sections, META_LABELS["face_value"]),
        price=price,
        market_cap=market_cap,
        annual=annual,
        quarterly=quarters,
    )
