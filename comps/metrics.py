"""Per-company metrics from a loaded Screener workbook.

Latest fiscal year (FY) figures come from the annual columns. LTM (last twelve months) figures are the sum
of the last 4 consecutive quarters in the Quarters block: Sales, EBITDA and Net profit. Anything with a
zero or negative denominator, or missing input, is None rather than an error.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from .screener import ScreenerData

REQUIRED_ANNUAL = ("sales", "other_income", "depreciation", "interest", "pbt", "net_profit",
                   "equity_capital", "reserves", "borrowings", "cash")
LTM_ITEMS = ("sales", "other_income", "depreciation", "interest", "pbt", "net_profit")
MAX_QUARTER_SPAN_DAYS = 290  # 4 consecutive quarters span about 273-276 days from first to last


@dataclass(frozen=True)
class CompanyMetrics:
    """All figures in rupees crore except price (rupees), shares (crore), ratios and days."""
    symbol: str
    name: str
    fy: int
    price: float
    shares_cr: float
    market_cap: float
    net_debt: float
    ev: float
    sales: float
    ebitda: float
    ebit: float
    net_profit: float
    ev_sales: float | None = None
    ev_ebitda: float | None = None
    pe: float | None = None
    rev_growth_1y: float | None = None
    rev_cagr_3y: float | None = None
    ebitda_growth_1y: float | None = None
    ebitda_cagr_3y: float | None = None
    ebitda_margin: float | None = None
    net_margin: float | None = None
    roce: float | None = None
    roe: float | None = None
    inventory_days: float | None = None
    ltm_end: dt.date | None = None
    ltm_sales: float | None = None
    ltm_ebitda: float | None = None
    ltm_net_profit: float | None = None
    ltm_ev_sales: float | None = None
    ltm_ev_ebitda: float | None = None
    ltm_pe: float | None = None

    def basis_value(self, name: str, basis: str = "fy") -> float | None:
        """`name` (sales, ebitda, net_profit, ev_sales, ev_ebitda, pe) on the 'fy' or 'ltm' basis."""
        return getattr(self, f"ltm_{name}" if basis == "ltm" else name)


# (header, attribute, kind) for tables: kind is text, price, crore, x, pct or days
TABLE_COLUMNS = (
    ("Symbol", "symbol", "text"), ("Company", "name", "text"), ("FY", "fy", "text"),
    ("Price (₹)", "price", "price"), ("Market cap (₹cr)", "market_cap", "crore"),
    ("Net debt (₹cr)", "net_debt", "crore"), ("EV (₹cr)", "ev", "crore"),
    ("Sales (₹cr)", "sales", "crore"), ("EBITDA (₹cr)", "ebitda", "crore"),
    ("Net profit (₹cr)", "net_profit", "crore"),
    ("EV/Sales", "ev_sales", "x"), ("EV/EBITDA", "ev_ebitda", "x"), ("P/E", "pe", "x"),
    ("LTM EV/Sales", "ltm_ev_sales", "x"), ("LTM EV/EBITDA", "ltm_ev_ebitda", "x"), ("LTM P/E", "ltm_pe", "x"),
    ("Revenue growth 1y", "rev_growth_1y", "pct"), ("Revenue CAGR 3y", "rev_cagr_3y", "pct"),
    ("EBITDA growth 1y", "ebitda_growth_1y", "pct"), ("EBITDA CAGR 3y", "ebitda_cagr_3y", "pct"),
    ("EBITDA margin", "ebitda_margin", "pct"), ("Net margin", "net_margin", "pct"),
    ("ROCE", "roce", "pct"), ("ROE", "roe", "pct"), ("Inventory days", "inventory_days", "days"),
    ("LTM sales (₹cr)", "ltm_sales", "crore"), ("LTM EBITDA (₹cr)", "ltm_ebitda", "crore"),
    ("LTM net profit (₹cr)", "ltm_net_profit", "crore"),
)

_TEXT_FORMATS = {"price": "{:,.2f}", "crore": "{:,.0f}", "x": "{:.1f}x", "pct": "{:.1%}", "days": "{:.0f}"}


def format_value(value: object, kind: str) -> str:
    """Display text for a table cell; None becomes 'n/a'."""
    if value is None:
        return "n/a"
    if kind == "text":
        return str(value)
    return _TEXT_FORMATS[kind].format(value)


def _div(numerator: float | None, denominator: float | None) -> float | None:
    """numerator / denominator, or None if either is missing or the denominator is not positive."""
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _growth(current: float | None, previous: float | None) -> float | None:
    """Simple growth rate; needs a positive previous value."""
    if current is None or previous is None or previous <= 0:
        return None
    return current / previous - 1


def _cagr(current: float | None, base: float | None, years: int) -> float | None:
    """Compound annual growth rate; needs positive start and end values."""
    if current is None or base is None or current <= 0 or base <= 0:
        return None
    return (current / base) ** (1 / years) - 1


def _ebitda(annual: dict[str, dict], year: int) -> float | None:
    """PBT + Interest + Depreciation - Other income for `year`, or None if any input is missing."""
    try:
        return (annual["pbt"][year] + annual["interest"][year] + annual["depreciation"][year]
                - annual["other_income"][year])
    except KeyError:
        return None


def _latest_year(data: ScreenerData) -> int:
    years = set.intersection(*(set(data.annual.get(key, {})) for key in REQUIRED_ANNUAL))
    if not years:
        raise ValueError(f"{data.symbol}: no fiscal year has all of {', '.join(REQUIRED_ANNUAL)}")
    return max(years)


def ltm(data: ScreenerData) -> tuple[dt.date, float, float, float] | None:
    """(last quarter end, Sales, EBITDA, Net profit) summed over the last 4 consecutive quarters, or None.

    Needs 4 quarters that all have the six P&L items, spanning no more than about 9.5 months (so a missing
    quarter in between returns None instead of silently summing a longer period).
    """
    quarters = data.quarterly
    if any(item not in quarters for item in LTM_ITEMS):
        return None
    dates = sorted(set.intersection(*(set(quarters[item]) for item in LTM_ITEMS)))
    if len(dates) < 4:
        return None
    last4 = dates[-4:]
    if (last4[-1] - last4[0]).days > MAX_QUARTER_SPAN_DAYS:
        return None

    def total(item: str) -> float:
        return sum(quarters[item][d] for d in last4)

    ebitda = total("pbt") + total("interest") + total("depreciation") - total("other_income")
    return last4[-1], total("sales"), ebitda, total("net_profit")


def compute_metrics(data: ScreenerData, price: float | None = None, name: str | None = None) -> CompanyMetrics:
    """Metrics for one company. `price` (rupees) overrides the Screener Current Price, e.g. a bhavcopy close."""
    px = data.price if price is None else price
    if px is None or px <= 0:
        raise ValueError(f"{data.symbol}: no usable price (neither supplied nor in the Screener META block)")
    if not data.shares_cr or data.shares_cr <= 0:
        raise ValueError(f"{data.symbol}: no share count (neither META 'Number of shares' nor 'No. of Equity Shares')")

    annual = data.annual
    fy = _latest_year(data)
    ebitda = _ebitda(annual, fy)
    depreciation = annual["depreciation"][fy]
    ebit = ebitda - depreciation
    sales = annual["sales"][fy]
    net_profit = annual["net_profit"][fy]
    equity = annual["equity_capital"][fy] + annual["reserves"][fy]
    borrowings = annual["borrowings"][fy]

    market_cap = px * data.shares_cr   # rupees x crore shares = rupees crore
    net_debt = borrowings - annual["cash"][fy]
    ev = market_cap + net_debt

    ebitda_by_year = {year: _ebitda(annual, year) for year in annual["sales"]}
    inventory = annual.get("inventory", {}).get(fy)
    inventory_days = _div(inventory, sales)

    ltm_data = ltm(data)
    ltm_end = ltm_sales = ltm_ebitda = ltm_np = None
    if ltm_data:
        ltm_end, ltm_sales, ltm_ebitda, ltm_np = ltm_data

    return CompanyMetrics(
        symbol=data.symbol,
        name=name or data.name or data.symbol,
        fy=fy, price=px, shares_cr=data.shares_cr, market_cap=market_cap, net_debt=net_debt, ev=ev,
        sales=sales, ebitda=ebitda, ebit=ebit, net_profit=net_profit,
        ev_sales=_div(ev, sales), ev_ebitda=_div(ev, ebitda), pe=_div(market_cap, net_profit),
        rev_growth_1y=_growth(sales, annual["sales"].get(fy - 1)),
        rev_cagr_3y=_cagr(sales, annual["sales"].get(fy - 3), 3),
        ebitda_growth_1y=_growth(ebitda, ebitda_by_year.get(fy - 1)),
        ebitda_cagr_3y=_cagr(ebitda, ebitda_by_year.get(fy - 3), 3),
        ebitda_margin=_div(ebitda, sales), net_margin=_div(net_profit, sales),
        roce=_div(ebit, equity + borrowings), roe=_div(net_profit, equity),
        inventory_days=None if inventory_days is None else inventory_days * 365,
        ltm_end=ltm_end, ltm_sales=ltm_sales, ltm_ebitda=ltm_ebitda, ltm_net_profit=ltm_np,
        ltm_ev_sales=_div(ev, ltm_sales), ltm_ev_ebitda=_div(ev, ltm_ebitda), ltm_pe=_div(market_cap, ltm_np),
    )
