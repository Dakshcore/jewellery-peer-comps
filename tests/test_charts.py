from comps.charts import football_field
from comps.valuation import ImpliedRange, point_range
from tests.synthetic import TempDirCase


class FootballField(TempDirCase):
    def test_saves_a_png_with_ranges_dcf_and_price_line(self):
        ranges = [ImpliedRange("EV/EBITDA (peers)", 3000, 3800, 4200, 4900, 5600),
                  ImpliedRange("P/E (peers)", 2500, 3300, 3900, 4600, 5200), point_range("DCF", 4052)]
        path = football_field(ranges, 4884, "25-Sep-2026", self.dir / "nested" / "chart.png")
        self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_no_ranges_is_an_error(self):
        with self.assertRaises(ValueError):
            football_field([], 4884, "25-Sep-2026", self.dir / "chart.png")
