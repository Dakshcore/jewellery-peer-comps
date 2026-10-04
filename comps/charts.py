"""Football-field chart of implied value per share."""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw to files only; no window needed
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from .valuation import ImpliedRange  # noqa: E402

LIGHT, DARK, DCF, LINE = "#bcd0e8", "#2f5d8c", "#d98f1f", "#b22222"


def football_field(ranges: Sequence[ImpliedRange], reference_price: float, reference_date: str,
                   path: str | Path, target: str = "TITAN") -> Path:
    """Draw one horizontal bar per range and a vertical line at the reference price; save a PNG.

    Light bar = min to max across peers, dark bar = 25th to 75th percentile, white tick = median.
    A zero-width range (the DCF) is drawn as a diamond. Returns the path written.
    """
    if not ranges:
        raise ValueError("no ranges to plot")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 1.0 * len(ranges) + 2.2))
    positions = list(range(len(ranges)))[::-1]  # first range at the top
    for y, r in zip(positions, ranges):
        if r.is_point:
            ax.plot(r.mid, y, marker="D", markersize=11, color=DCF, zorder=3)
            ax.annotate(f"₹{r.mid:,.0f}", (r.mid, y + 0.1), xytext=(0, 8), textcoords="offset points",
                        ha="center", va="bottom", fontsize=9)
            continue
        ax.barh(y, r.maximum - r.minimum, left=r.minimum, height=0.55, color=LIGHT, zorder=2)
        ax.barh(y, r.high - r.low, left=r.low, height=0.55, color=DARK, zorder=3)
        ax.plot([r.mid, r.mid], [y - 0.275, y + 0.275], color="white", linewidth=2, zorder=4)
        ax.annotate(f"₹{r.minimum:,.0f}", (r.minimum, y), xytext=(-4, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=8)
        ax.annotate(f"₹{r.maximum:,.0f}", (r.maximum, y), xytext=(4, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=8)
        ax.annotate(f"₹{r.mid:,.0f}", (r.mid, y + 0.275), xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8)

    ax.axvline(reference_price, color=LINE, linestyle="--", linewidth=1.5, zorder=1)
    ax.set_yticks(positions)
    ax.set_yticklabels([r.label for r in ranges])
    low = min([r.minimum for r in ranges] + [reference_price])
    high = max([r.maximum for r in ranges] + [reference_price])
    pad = (high - low) * 0.15 or 1.0
    ax.set_xlim(low - pad, high + pad)
    ax.set_ylim(-0.6, len(ranges) - 0.3)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"₹{v:,.0f}"))
    ax.set_xlabel("Implied value per share (₹)")
    ax.set_title(f"{target}: implied value per share from peer multiples and DCF")
    ax.grid(axis="x", alpha=0.3, zorder=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(handles=[Patch(color=LIGHT, label="Peer min to max"), Patch(color=DARK, label="25th to 75th percentile"),
                       Line2D([], [], color=DCF, marker="D", linestyle="", label="DCF"),
                       Line2D([], [], color=LINE, linestyle="--", label=f"Price ₹{reference_price:,.1f} ({reference_date})")],
              loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=8, frameon=False)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
