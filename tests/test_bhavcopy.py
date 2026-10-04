import io
import zipfile

from comps.bhavcopy import closing_prices, read_bhavcopy, trade_date
from tests.synthetic import TempDirCase

CSV = """TradDt,TckrSymb,SctySrs,ClsPric
2026-09-25,TITAN,EQ,4884.50
2026-09-25,TITAN,BE,1.00
2026-09-25, SENCO ,EQ,510.25
2026-09-25,PNGJL,EQ,
2026-09-25,TRENT,EQ,5500
"""


class Bhavcopy(TempDirCase):
    def test_closing_prices_use_series_eq_and_skip_unknown_or_blank(self):
        prices = closing_prices(io.StringIO(CSV), ["TITAN", "SENCO", "KALYANKJIL", "PNGJL"])
        self.assertEqual(prices, {"TITAN": 4884.5, "SENCO": 510.25})

    def test_symbols_are_case_insensitive(self):
        self.assertEqual(closing_prices(io.StringIO(CSV), ["trent"]), {"TRENT": 5500.0})

    def test_trade_date(self):
        self.assertEqual(trade_date(read_bhavcopy(io.StringIO(CSV))), "2026-09-25")

    def test_missing_column_is_named(self):
        with self.assertRaises(ValueError) as caught:
            read_bhavcopy(io.StringIO("TradDt,TckrSymb,SctySrs\n2026-09-25,TITAN,EQ\n"))
        self.assertIn("ClsPric", str(caught.exception))

    def test_reads_csv_and_zip_files(self):
        csv_path = self.dir / "BhavCopy_NSE_CM_0_0_0_20260925_F_0000.csv"
        csv_path.write_text(CSV)
        zip_path = self.dir / "BhavCopy_NSE_CM_0_0_0_20260925_F_0000.csv.zip"
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.write(csv_path, csv_path.name)
        self.assertEqual(closing_prices(csv_path, ["TITAN"]), {"TITAN": 4884.5})
        self.assertEqual(closing_prices(zip_path, ["TITAN"]), {"TITAN": 4884.5})
