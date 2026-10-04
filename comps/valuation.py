"""Peer statistics and the value per share they imply for the target."""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from .metrics import CompanyMetrics

MULTIPLES = {"ev_ebitda": "EV/EBITDA", "pe": "P/E", "ev_sales": "EV/Sales"}
# The target metric each multiple is applied to.
_METRIC = {"ev_ebitda": "ebitda", "pe": "net_profit", "ev_sales": "sales"}


@dataclass(frozen=True)
class PeerStats:
    """Distribution of one multiple across peers. All None when n == 0."""
    n: int
    minimum: float | None
    p25: float | None
    median: float | None
    p75: float | None
    maximum: float | None


@dataclass(frozen=True)
class ImpliedRange:
    """Implied value per share (rupees) for the football field. low/high are the 25th/75th percentile."""
    label: str
    minimum: float
    low: float
    mid: float
    high: float
    maximum: float

    @property
    def is_point(self) -> bool:
        return self.minimum == self.maximum


def peer_stats(values: Iterable[float | None]) -> PeerStats:
    """Min, 25th percentile, median, 75th percentile and max, ignoring None and non-finite values.

    Percentiles use linear interpolation (numpy's default), so [1, 2, 3, 4] has a 25th percentile of 1.75.
    """
    clean = [float(v) for v in values if v is not None and math.isfinite(v)]
    if not clean:
        return PeerStats(0, None, None, None, None, None)
    p25, median, p75 = (float(x) for x in np.percentile(clean, [25, 50, 75]))
    return PeerStats(len(clean), min(clean), p25, median, p75, max(clean))


def peer_multiple_stats(peers: Sequence[CompanyMetrics], basis: str = "fy") -> dict[str, PeerStats]:
    """PeerStats for EV/EBITDA, P/E and EV/Sales (keys ev_ebitda, pe, ev_sales) on the 'fy' or 'ltm' basis."""
    return {key: peer_stats(peer.basis_value(key, basis) for peer in peers) for key in MULTIPLES}


def implied_per_share(multiple_key: str, multiple: float, target: CompanyMetrics, basis: str = "fy") -> float | None:
    """Value per share (rupees) the multiple implies for the target, or None if its metric is not positive.

    EV multiples: (multiple x metric - net debt) / shares. P/E: multiple x net profit / shares.
    Money is in crore and shares in crore, so the quotient is rupees per share.
    """
    metric = target.basis_value(_METRIC[multiple_key], basis)
    if metric is None or metric <= 0:
        return None
    equity = multiple * metric if multiple_key == "pe" else multiple * metric - target.net_debt
    return equity / target.shares_cr


def implied_ranges(target: CompanyMetrics, stats: dict[str, PeerStats], basis: str = "fy") -> list[ImpliedRange]:
    """One ImpliedRange per multiple that has peer data and a usable target metric."""
    ranges = []
    for key, label in MULTIPLES.items():
        s = stats[key]
        if s.n == 0:
            continue
        values = [implied_per_share(key, m, target, basis)
                  for m in (s.minimum, s.p25, s.median, s.p75, s.maximum)]
        if any(v is None for v in values):
            continue
        ranges.append(ImpliedRange(f"{label} (peers)", *values))
    return ranges


def point_range(label: str, value: float) -> ImpliedRange:
    """A single value shown as a zero-width range, e.g. my own valuation."""
    return ImpliedRange(label, value, value, value, value, value)
