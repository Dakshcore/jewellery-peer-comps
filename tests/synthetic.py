"""Small synthetic Screener-style workbooks for the tests. No real data.

Default company (all rupees crore, March year-ends 2023-2026, 1e8 shares = 10 crore, price 100):
  FY2026: Sales 1331, PBT 135, Interest 10, Depreciation 20, Other income 5 -> EBITDA 160, EBIT 140,
  Net profit 100, Equity capital 50 + Reserves 450, Borrowings 200, Cash 100, Inventory 250.
  Five quarters Jun-25 .. Jun-26; the last four give LTM Sales 1380, EBITDA 164, Net profit 103.

The layout mirrors a real Screener export (version 2.1): version rows, a META block whose "Number of shares"
is a formula with no cached value (reads as None), section headers "CASH FLOW:" / "PRICE:" / "DERIVED:" with
trailing colons, PRICE carrying its data on the header row, a DERIVED "Adjusted Equity Shares in Cr" row, and
nil Other Income left as an empty cell (the oldest quarter below).
"""
from __future__ import annotations

import datetime as dt
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

YEARS = [dt.datetime(y, 3, 31) for y in (2023, 2024, 2025, 2026)]
QUARTERS = [dt.datetime(2025, 6, 30), dt.datetime(2025, 9, 30), dt.datetime(2025, 12, 31),
            dt.datetime(2026, 3, 31), dt.datetime(2026, 6, 30)]

PNL = {
    "Sales": [1000, 1100, 1210, 1331],
    "Raw Material Cost": [500, 550, 600, 650],
    "Employee Cost": [100, 100, 100, 100],
    "Other Income": [5, 5, 5, 5],
    "Depreciation": [20, 20, 20, 20],
    "Interest": [10, 10, 10, 10],
    "Profit before tax": [100, 110, 120, 135],
    "Tax": [25, 28, 30, 35],
    "Net profit": [75, 82, 90, 100],
    "Dividend Amount": [10, 10, 10, 10],
}
QUARTER_ROWS = {
    "Sales": [300, 320, 330, 350, 380],
    "Expenses": [250, 260, 270, 280, 300],
    "Other Income": [None, 1, 1, 1, 1],
    "Depreciation": [5, 5, 5, 5, 5],
    "Interest": [2.5, 2.5, 2.5, 2.5, 2.5],
    "Profit before tax": [30, 32, 33, 35, 38],
    "Tax": [8, 8, 8, 9, 10],
    "Net profit": [22, 24, 25, 26, 28],
}
BALANCE = {
    "Equity Share Capital": [50, 50, 50, 50],
    "Reserves": [300, 350, 400, 450],
    "Borrowings": [200, 200, 200, 200],
    "Other Liabilities": [100, 100, 100, 100],
    "Net Block": [300, 300, 300, 300],
    "Investments": [0, 0, 0, 0],
    "Receivables": [50, 50, 50, 50],
    "Inventory": [200, 220, 240, 250],
    "Cash & Bank": [80, 90, 95, 100],
    "No. of Equity Shares": [1e8, 1e8, 1e8, 1e8],
}


SHARES_FORMULA = "=IF(B9>0, B9/B8, 0)"   # what a real export holds in META "Number of shares"


def make_workbook(path: Path, *, name: str = "Alpha Ltd", shares: float | str | None = SHARES_FORMULA,
                  price: float | None = 100.0, mcap: float | None | str = "auto", derived_shares: float | None = 10.0, scale: float = 1.0, pnl: dict | None = None, balance: dict | None = None,
                  quarters: dict | bool | None = None, quarter_dates: list | None = None,
                  drop: set[str] = frozenset(), style=lambda label: label, sheet_title: str = "Data Sheet",
                  with_balance_sheet: bool = True) -> Path:
    """Write a Screener-like 'Data Sheet'. `pnl`/`balance`/`quarters` replace rows by label; quarters=False
    leaves the Quarters block out; `drop` omits labels everywhere; `style` rewrites every label cell.
    `shares` is a number, None (row omitted) or the default uncached formula; None for `mcap` / `derived_shares`
    omits that row. `mcap` defaults to price x 10 crore shares (1000 if there is no price), as in a real file."""
    if mcap == "auto":
        mcap = price * 10 if price is not None else 1000.0
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title

    def add(*cells) -> None:
        sheet.append(list(cells))

    def block(title: str, dates: list, rows: dict) -> None:
        add(style(title))
        add(style("Report Date"), *dates)
        for label, values in rows.items():
            if label not in drop:
                add(style(label), *[v if v is None or label == "No. of Equity Shares" else v * scale for v in values])
        add(None)

    add(style("COMPANY NAME"), name)
    add(style("LATEST VERSION"), 2.1)
    add(style("CURRENT VERSION"), 2.1)
    add(None)
    add(style("META"))
    if shares is not None:
        add(style("Number of shares"), shares)
    add(style("Face Value"), 10)
    if price is not None:
        add(style("Current Price"), price)
    if mcap is not None:
        add(style("Market Capitalization"), mcap)
    add(None)
    block("PROFIT & LOSS", YEARS, {**PNL, **(pnl or {})})
    if quarters is not False:
        dates = quarter_dates or QUARTERS
        rows = {**QUARTER_ROWS, **(quarters or {})}
        block("Quarters", dates, {label: values[:len(dates)] for label, values in rows.items()})
    if with_balance_sheet:
        block("BALANCE SHEET", YEARS, {**BALANCE, **(balance or {})})
    block("CASH FLOW:", YEARS, {"Cash from Operating Activity": [90, 95, 100, 110]})
    add(style("PRICE:"), 60, 70, 80, 90)   # real exports put the price history on the header row itself
    add(None)
    add(style("DERIVED:"))
    if derived_shares is not None:
        add(style("Adjusted Equity Shares in Cr"), *[derived_shares] * len(YEARS))
    workbook.save(path)
    return path


class TempDirCase(unittest.TestCase):
    """A test case with a temporary folder (self.dir) and a helper to write synthetic workbooks into it."""

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)

    def workbook(self, symbol: str = "ALPHA", folder: Path | None = None, **kwargs) -> Path:
        folder = folder or self.dir
        folder.mkdir(parents=True, exist_ok=True)
        return make_workbook(folder / f"{symbol}.xlsx", **kwargs)
