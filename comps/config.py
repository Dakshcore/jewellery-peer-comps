"""Default peer groups, reference values and method notes. Edit here, or override on the command line."""

TARGET = "TITAN"
CORE_PEERS = ("KALYANKJIL", "SENCO", "THANGAMAYL", "PNGJL")
REFERENCE_PEERS = ("TRENT",)  # lifestyle retail: shown separately, excluded from core medians by default

NAMES = {
    "TITAN": "Titan Company",
    "KALYANKJIL": "Kalyan Jewellers India",
    "SENCO": "Senco Gold",
    "THANGAMAYL": "Thangamayil Jewellery",
    "PNGJL": "P N Gadgil Jewellers",
    "TRENT": "Trent",
}

# Which Screener page the export comes from. Informational only: it is printed in the notes sheet.
# All six companies have a March fiscal year-end.
BASIS = {
    "TITAN": "consolidated",
    "KALYANKJIL": "consolidated",
    "SENCO": "consolidated",
    "THANGAMAYL": "standalone",  # no consolidated Screener page: its export is a standalone one
    "PNGJL": "consolidated",
    "TRENT": "consolidated",
}

DCF_VALUE = 4052.0          # Titan DCF, rupees per share
# Reference price (the vertical line in the chart). By default it is read from the data: the target's price
# (Screener "Current Price", or the bhavcopy close). Set REFERENCE_PRICE / REFERENCE_DATE to override, or pass
# --ref-price / --ref-date on the command line.
REFERENCE_PRICE = None
REFERENCE_DATE = None
# Screener does not record when an export was downloaded. The date below is the close the current exports
# reflect (Titan 4,515.7 on 1 Oct 2026); update it whenever the exports are refreshed.
SCREENER_AS_OF = "01-Oct-2026"

DATA_DIR = "data/raw/screener"
OUT_DIR = "outputs"

NOTES = (
    "EBITDA = Profit before tax + Interest + Depreciation - Other income. EBIT = EBITDA - Depreciation.",
    "Net debt = Borrowings - Cash & Bank, from the latest fiscal-year balance sheet. Screener's Borrowings "
    "may include lease liabilities, and jewellers may carry gold metal loans there; Cash & Bank excludes "
    "investments. Net debt is not adjusted for any of this.",
    "Market cap = price x shares in crore. Enterprise value (EV) = market cap + net debt. All money is in rupees crore.",
    "LTM (last twelve months) = the sum of the last 4 consecutive quarters in the Quarters block, for Sales, "
    "EBITDA (same formula as annual) and Net profit. LTM multiples use the latest fiscal-year net debt.",
    "ROCE = EBIT / (Equity share capital + Reserves + Borrowings). ROE = Net profit / (Equity share capital + "
    "Reserves). Both use year-end balances, not averages. Inventory days = Inventory / Sales x 365.",
    "Multiples are trailing (no consensus estimates). A multiple with a zero or negative denominator is shown as n/a.",
    "Peer statistics use linear-interpolation percentiles. Reference peers (Trent) are shown but excluded from "
    "the statistics unless --include-reference is passed.",
    "Implied value per share: EV multiples x target metric - target net debt, divided by shares; P/E x target "
    "net profit divided by shares.",
    "Thangamayil's Screener export is standalone (no consolidated page); the others are consolidated.",
    "Not investment advice.",
)
