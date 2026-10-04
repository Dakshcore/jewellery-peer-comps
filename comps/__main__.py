"""Command line: python -m comps --target TITAN --price-source screener|bhavcopy [--bhavcopy PATH] [--valuation 4052]."""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

from . import config
from .bhavcopy import closing_prices, read_bhavcopy, trade_date
from .charts import football_field
from .excel import write_workbook
from .metrics import CompanyMetrics, compute_metrics, format_value
from .screener import load_screener
from .valuation import MULTIPLES, implied_ranges, peer_multiple_stats, point_range


def _symbols(text: str) -> list[str]:
    return [part.strip().upper() for part in text.split(",") if part.strip()]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m comps", description="Trading comps from Screener workbooks.")
    parser.add_argument("--target", default=config.TARGET, help="symbol to value (default %(default)s)")
    parser.add_argument("--peers", default=",".join(config.CORE_PEERS), help="comma-separated core peers")
    parser.add_argument("--reference", default=",".join(config.REFERENCE_PEERS),
                        help="comma-separated reference peers, shown separately (use '' for none)")
    parser.add_argument("--include-reference", action="store_true",
                        help="include the reference peers in the peer statistics")
    parser.add_argument("--price-source", choices=("screener", "bhavcopy"), default="screener")
    parser.add_argument("--bhavcopy", help="NSE capital-market bhavcopy (.csv or .zip); needed for --price-source bhavcopy")
    parser.add_argument("--basis", choices=("fy", "ltm"), default="fy", help="multiples on latest fiscal year or LTM")
    parser.add_argument("--valuation", "--dcf", dest="valuation", type=float, default=config.OWN_VALUATION,
                        help="my own Titan valuation per share (discounted earnings, exit P/E), rupees")
    parser.add_argument("--ref-price", type=float, default=config.REFERENCE_PRICE,
                        help="override the reference share price, rupees (the vertical line); "
                             "default: the target's price from the data")
    parser.add_argument("--ref-date", default=config.REFERENCE_DATE, help="date of the reference price")
    parser.add_argument("--as-of", default=config.SCREENER_AS_OF,
                        help="date the Screener exports reflect (not stored in the files); default %(default)s")
    parser.add_argument("--data-dir", default=config.DATA_DIR, help="folder of <SYMBOL>.xlsx Screener exports")
    parser.add_argument("--out-dir", default=config.OUT_DIR)
    args = parser.parse_args(argv)
    if args.price_source == "bhavcopy" and not args.bhavcopy:
        parser.error("--price-source bhavcopy needs --bhavcopy PATH")
    return args


def _table_text(companies: list[CompanyMetrics], basis: str) -> str:
    """A plain-text table of the headline numbers."""
    prefix = "ltm_" if basis == "ltm" else ""
    columns = [("Symbol", "symbol", "text"), ("Price", "price", "price"), ("MktCap cr", "market_cap", "crore"),
               ("EV cr", "ev", "crore"), ("EV/Sales", f"{prefix}ev_sales", "x"),
               ("EV/EBITDA", f"{prefix}ev_ebitda", "x"), ("P/E", f"{prefix}pe", "x"),
               ("EBITDA mgn", "ebitda_margin", "pct"), ("ROCE", "roce", "pct"), ("Inv days", "inventory_days", "days")]
    cells = [[header for header, _, _ in columns]]
    cells += [[format_value(getattr(c, attr), kind) for _, attr, kind in columns] for c in companies]
    widths = [max(len(row[i]) for row in cells) for i in range(len(columns))]
    lines = ["  ".join(text.rjust(width) if i else text.ljust(width) for i, (text, width) in enumerate(zip(row, widths)))
             for row in cells]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = args.target.upper()
    core = [s for s in _symbols(args.peers) if s != target]
    reference = [s for s in _symbols(args.reference) if s != target and s not in core]
    data_dir = Path(args.data_dir)

    bhavcopy_frame = None
    prices: dict[str, float] = {}
    if args.price_source == "bhavcopy":
        try:
            bhavcopy_frame = read_bhavcopy(args.bhavcopy)
        except (OSError, ValueError, zipfile.BadZipFile) as error:
            print(f"error: cannot read bhavcopy {args.bhavcopy}: {error}", file=sys.stderr)
            return 2
        prices = closing_prices(bhavcopy_frame, [target, *core, *reference])

    metrics: dict[str, CompanyMetrics] = {}
    skipped: list[str] = []
    for symbol in [target, *core, *reference]:
        try:
            data = load_screener(data_dir / f"{symbol}.xlsx", symbol)
            price = None
            if bhavcopy_frame is not None:
                if symbol not in prices:
                    raise ValueError(f"{symbol}: no EQ-series close in the bhavcopy")
                price = prices[symbol]
            metrics[symbol] = compute_metrics(data, price, config.NAMES.get(symbol))
        except (FileNotFoundError, ValueError) as error:
            if symbol == target:
                print(f"error: {error}", file=sys.stderr)
                return 2
            print(f"warning: skipping {symbol}: {error}", file=sys.stderr)
            skipped.append(symbol)

    core_metrics = [metrics[s] for s in core if s in metrics]
    reference_metrics = [metrics[s] for s in reference if s in metrics]
    stat_peers = core_metrics + (reference_metrics if args.include_reference else [])
    if not stat_peers:
        print("error: no peers could be loaded", file=sys.stderr)
        return 2

    target_metrics = metrics[target]
    stats = peer_multiple_stats(stat_peers, args.basis)
    ranges = implied_ranges(target_metrics, stats, args.basis) + [point_range("My valuation", args.valuation)]

    if bhavcopy_frame is not None:
        as_of = trade_date(bhavcopy_frame) or "unknown date"
        price_note = f"NSE bhavcopy {Path(args.bhavcopy).name}, trade date {as_of}"
    else:
        as_of = args.as_of
        price_note = f"Screener 'Current Price' in each export, as of {as_of} (the date is not stored in the files)"
    if args.ref_price is not None:
        ref_price, ref_date = args.ref_price, args.ref_date or "user-specified"
    else:
        ref_price, ref_date = target_metrics.price, args.ref_date or as_of
    args.ref_price, args.ref_date = ref_price, ref_date

    out_dir = Path(args.out_dir)
    chart_path = football_field(ranges, ref_price, ref_date, out_dir / "football_field.png", target)
    inputs = [
        ("Target", target), ("Core peers used", ", ".join(c.symbol for c in core_metrics)),
        ("Reference peers", ", ".join(c.symbol for c in reference_metrics) or "none"),
        ("Reference peers in statistics", "yes" if args.include_reference else "no"),
        ("Skipped (could not load)", ", ".join(skipped) or "none"),
        ("Multiple basis", "LTM" if args.basis == "ltm" else "latest fiscal year"),
        ("Price source", price_note), ("Prices as of", as_of), ("My valuation per share (₹)", args.valuation),
        ("Reference price (₹)", ref_price), ("Reference price date", ref_date),
        ("Screener basis", ", ".join(f"{s}: {config.BASIS.get(s, 'unknown')}" for s in metrics)),
    ]
    workbook_path = write_workbook(out_dir / "comps.xlsx", target_metrics, core_metrics, reference_metrics, stats,
                                   ranges, args.ref_price, args.ref_date, inputs, config.NOTES, args.basis)

    print(_table_text([target_metrics, *core_metrics], args.basis))
    if reference_metrics:
        print("\nReference (lifestyle retail), "
              + ("included in" if args.include_reference else "excluded from") + " peer statistics:")
        print(_table_text(reference_metrics, args.basis))
    print(f"\nPeer statistics ({'LTM' if args.basis == 'ltm' else 'latest FY'}, n = {len(stat_peers)} peers):")
    for key, label in MULTIPLES.items():
        s = stats[key]
        parts = [format_value(v, "x") for v in (s.minimum, s.p25, s.median, s.p75, s.maximum)]
        print(f"  {label:<10} min {parts[0]}  p25 {parts[1]}  median {parts[2]}  p75 {parts[3]}  max {parts[4]}")
    print(f"\nImplied value per share for {target} (Rs):")
    for r in ranges:
        if r.is_point:
            print(f"  {r.label:<20} {r.mid:>9,.0f}")
        else:
            print(f"  {r.label:<20} p25 {r.low:>8,.0f}  median {r.mid:>8,.0f}  p75 {r.high:>8,.0f}")
    print(f"  Reference price ({args.ref_date}): {args.ref_price:,.1f}")
    print(f"\nWrote {workbook_path} and {chart_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
