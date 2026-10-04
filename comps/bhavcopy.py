"""Close prices from NSE's capital-market bhavcopy (UDiFF layout), a .csv or a .zip holding one csv.

Download by hand from NSE's reports page; the file is named like BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv(.zip).
Columns used: TckrSymb (symbol), SctySrs (series), ClsPric (close), TradDt (trade date).
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import IO

import pandas as pd

REQUIRED_COLUMNS = ("TckrSymb", "SctySrs", "ClsPric")


def read_bhavcopy(source: str | Path | IO) -> pd.DataFrame:
    """Read a bhavcopy (path to .csv/.zip, or a file-like object) with every column as text."""
    frame = pd.read_csv(source, dtype=str)
    frame.columns = [str(column).strip() for column in frame.columns]
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"bhavcopy is missing column(s) {', '.join(missing)}; found {', '.join(frame.columns)}")
    return frame


def trade_date(frame: pd.DataFrame) -> str | None:
    """The trade date (TradDt) of the first row, as written in the file, or None if there is no such column."""
    if "TradDt" not in frame.columns or frame.empty:
        return None
    return str(frame["TradDt"].iloc[0]).strip()


def closing_prices(source: str | Path | IO | pd.DataFrame, symbols: Iterable[str],
                   series: str = "EQ") -> dict[str, float]:
    """{symbol: close} for the requested symbols in `series`. Symbols not found are simply absent."""
    frame = source if isinstance(source, pd.DataFrame) else read_bhavcopy(source)
    wanted = {symbol.strip().upper() for symbol in symbols}
    symbol_col = frame["TckrSymb"].str.strip().str.upper()
    in_series = frame["SctySrs"].str.strip().str.upper() == series.upper()
    close = pd.to_numeric(frame["ClsPric"], errors="coerce")
    keep = symbol_col.isin(wanted) & in_series & close.notna()
    return {symbol: float(price) for symbol, price in zip(symbol_col[keep], close[keep])}
