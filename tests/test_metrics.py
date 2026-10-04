import datetime as dt

from comps.metrics import compute_metrics, format_value
from comps.screener import load_screener
from tests.synthetic import TempDirCase


class Metrics(TempDirCase):
    def metrics(self, price=None, **kwargs):
        return compute_metrics(load_screener(self.workbook(**kwargs)), price)

    def test_ebitda_and_ebit(self):
        m = self.metrics()
        self.assertEqual(m.fy, 2026)
        self.assertAlmostEqual(m.ebitda, 135 + 10 + 20 - 5)    # PBT + interest + depreciation - other income
        self.assertAlmostEqual(m.ebit, 160 - 20)

    def test_market_cap_net_debt_and_ev(self):
        m = self.metrics()
        self.assertAlmostEqual(m.shares_cr, 10.0)
        self.assertAlmostEqual(m.market_cap, 1000.0)           # 100 rupees x 10 crore shares
        self.assertAlmostEqual(m.net_debt, 100.0)              # borrowings 200 - cash 100
        self.assertAlmostEqual(m.ev, 1100.0)

    def test_multiples(self):
        m = self.metrics()
        self.assertAlmostEqual(m.ev_sales, 1100 / 1331)
        self.assertAlmostEqual(m.ev_ebitda, 6.875)
        self.assertAlmostEqual(m.pe, 10.0)

    def test_margins_returns_and_inventory_days(self):
        m = self.metrics()
        self.assertAlmostEqual(m.ebitda_margin, 160 / 1331)
        self.assertAlmostEqual(m.net_margin, 100 / 1331)
        self.assertAlmostEqual(m.roce, 140 / 700)              # EBIT / (50 + 450 + 200)
        self.assertAlmostEqual(m.roe, 100 / 500)
        self.assertAlmostEqual(m.inventory_days, 250 / 1331 * 365)

    def test_growth_and_cagr(self):
        m = self.metrics()
        self.assertAlmostEqual(m.rev_growth_1y, 1331 / 1210 - 1)
        self.assertAlmostEqual(m.rev_cagr_3y, 0.10)
        self.assertAlmostEqual(m.ebitda_growth_1y, 160 / 145 - 1)
        self.assertAlmostEqual(m.ebitda_cagr_3y, (160 / 125) ** (1 / 3) - 1)

    def test_ltm_sums_the_last_four_quarters(self):
        m = self.metrics()
        self.assertEqual(m.ltm_end, dt.date(2026, 6, 30))
        self.assertAlmostEqual(m.ltm_sales, 320 + 330 + 350 + 380)
        self.assertAlmostEqual(m.ltm_ebitda, (32 + 33 + 35 + 38) + 4 * (2.5 + 5 - 1))
        self.assertAlmostEqual(m.ltm_net_profit, 24 + 25 + 26 + 28)
        self.assertAlmostEqual(m.ltm_ev_ebitda, 1100 / 164)
        self.assertAlmostEqual(m.ltm_pe, 1000 / 103)

    def test_ltm_is_none_without_four_consecutive_quarters(self):
        three = self.metrics(quarter_dates=[dt.datetime(2025, 12, 31), dt.datetime(2026, 3, 31),
                                            dt.datetime(2026, 6, 30)])
        gap = self.metrics(quarter_dates=[dt.datetime(2025, 6, 30), dt.datetime(2025, 12, 31),
                                          dt.datetime(2026, 3, 31), dt.datetime(2026, 6, 30)])
        none = self.metrics(quarters=False)
        for m in (three, gap, none):
            self.assertIsNone(m.ltm_ebitda)
            self.assertIsNone(m.ltm_ev_ebitda)
            self.assertAlmostEqual(m.ev_ebitda, 6.875)        # fiscal-year figures are unaffected

    def test_negative_ebitda_gives_no_ev_ebitda_or_cagr(self):
        m = self.metrics(pnl={"Profit before tax": [100, 110, 120, -100]})
        self.assertAlmostEqual(m.ebitda, -75)
        self.assertIsNone(m.ev_ebitda)
        self.assertIsNone(m.ebitda_cagr_3y)
        self.assertAlmostEqual(m.ebitda_growth_1y, -75 / 145 - 1)

    def test_negative_profit_gives_no_pe(self):
        m = self.metrics(pnl={"Net profit": [75, 82, 90, -5]})
        self.assertIsNone(m.pe)
        self.assertIsNotNone(m.ev_ebitda)

    def test_zero_denominators_give_none(self):
        m = self.metrics(pnl={"Sales": [0, 1100, 1210, 0]})
        self.assertIsNone(m.ev_sales)
        self.assertIsNone(m.ebitda_margin)
        self.assertIsNone(m.inventory_days)
        self.assertIsNone(m.rev_cagr_3y)                       # base year sales are 0
        no_capital = self.metrics(balance={"Equity Share Capital": [0] * 4, "Reserves": [0] * 4,
                                           "Borrowings": [0] * 4})
        self.assertIsNone(no_capital.roce)
        self.assertIsNone(no_capital.roe)

    def test_net_cash_lowers_ev(self):
        m = self.metrics(balance={"Cash & Bank": [80, 90, 95, 400]})
        self.assertAlmostEqual(m.net_debt, -200)
        self.assertAlmostEqual(m.ev, 800)

    def test_price_can_be_overridden_and_must_exist(self):
        self.assertAlmostEqual(self.metrics(price=200.0).market_cap, 2000.0)
        data = load_screener(self.workbook("NOPRICE", price=None))
        with self.assertRaises(ValueError) as caught:
            compute_metrics(data)
        self.assertIn("NOPRICE", str(caught.exception))

    def test_format_value(self):
        self.assertEqual(format_value(None, "x"), "n/a")
        self.assertEqual(format_value(6.875, "x"), "6.9x")
        self.assertEqual(format_value(0.2, "pct"), "20.0%")
