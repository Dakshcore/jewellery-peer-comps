import math

from comps.metrics import compute_metrics
from comps.screener import load_screener
from comps.valuation import (PeerStats, implied_per_share, implied_ranges, peer_multiple_stats, peer_stats,
                             point_range)
from tests.synthetic import TempDirCase


class PeerStatistics(TempDirCase):
    def test_percentiles_of_five_values(self):
        s = peer_stats([5, 1, 3, 2, 4])
        self.assertEqual((s.n, s.minimum, s.p25, s.median, s.p75, s.maximum), (5, 1, 2, 3, 4, 5))

    def test_percentiles_interpolate_linearly(self):
        s = peer_stats([1, 2, 3, 4])
        self.assertAlmostEqual(s.p25, 1.75)
        self.assertAlmostEqual(s.median, 2.5)
        self.assertAlmostEqual(s.p75, 3.25)

    def test_none_and_non_finite_values_are_ignored(self):
        s = peer_stats([None, 2.0, math.nan, 4.0, math.inf])
        self.assertEqual((s.n, s.minimum, s.median, s.maximum), (2, 2.0, 3.0, 4.0))

    def test_no_values_gives_empty_stats(self):
        self.assertEqual(peer_stats([None]), PeerStats(0, None, None, None, None, None))

    def test_stats_across_peer_companies(self):
        # same fundamentals, prices 80/100/120: market cap 800/1000/1200, net debt 100, EBITDA 160, profit 100
        peers = [compute_metrics(load_screener(self.workbook(f"P{price}", price=price))) for price in (80, 100, 120)]
        stats = peer_multiple_stats(peers)
        self.assertAlmostEqual(stats["pe"].median, 10.0)
        self.assertAlmostEqual(stats["pe"].p25, 9.0)
        self.assertAlmostEqual(stats["pe"].p75, 11.0)
        self.assertAlmostEqual(stats["ev_ebitda"].median, 1100 / 160)
        self.assertAlmostEqual(stats["ev_ebitda"].minimum, 900 / 160)
        self.assertAlmostEqual(peer_multiple_stats(peers, "ltm")["pe"].median, 1000 / 103)


class ImpliedValues(TempDirCase):
    def setUp(self):
        super().setUp()
        # EBITDA 160, net profit 100, sales 1331, net debt 100, 10 crore shares
        self.target = compute_metrics(load_screener(self.workbook("TARGET")))

    def test_ev_multiple_less_net_debt_per_share(self):
        self.assertAlmostEqual(implied_per_share("ev_ebitda", 8, self.target), (8 * 160 - 100) / 10)
        self.assertAlmostEqual(implied_per_share("ev_sales", 1, self.target), (1331 - 100) / 10)

    def test_pe_times_earnings_per_share(self):
        self.assertAlmostEqual(implied_per_share("pe", 12, self.target), 12 * 100 / 10)

    def test_ltm_basis_uses_ltm_metrics(self):
        self.assertAlmostEqual(implied_per_share("ev_ebitda", 8, self.target, "ltm"), (8 * 164 - 100) / 10)

    def test_non_positive_metric_gives_none(self):
        loss_making = compute_metrics(load_screener(self.workbook(
            "LOSS", pnl={"Profit before tax": [100, 110, 120, -100]})))
        self.assertIsNone(implied_per_share("ev_ebitda", 8, loss_making))
        self.assertEqual([r.label for r in implied_ranges(loss_making, {
            "ev_ebitda": peer_stats([5, 6]), "pe": peer_stats([8, 10]), "ev_sales": peer_stats([1, 2])})],
            ["P/E (peers)", "EV/Sales (peers)"])

    def test_implied_ranges_follow_the_peer_percentiles(self):
        peers = [compute_metrics(load_screener(self.workbook(f"P{price}", price=price))) for price in (80, 100, 120)]
        ranges = implied_ranges(self.target, peer_multiple_stats(peers))
        self.assertEqual([r.label for r in ranges], ["EV/EBITDA (peers)", "P/E (peers)", "EV/Sales (peers)"])
        pe = ranges[1]   # P/E 8, 9, 10, 11, 12 -> x 100 / 10 shares
        self.assertEqual((pe.minimum, pe.low, pe.mid, pe.high, pe.maximum), (80, 90, 100, 110, 120))

    def test_point_range_for_my_valuation(self):
        own = point_range("My valuation", 4052.0)
        self.assertTrue(own.is_point)
        self.assertEqual((own.low, own.mid, own.high), (4052.0, 4052.0, 4052.0))
