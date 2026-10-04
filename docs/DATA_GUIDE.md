# Data Guide

How to collect the inputs for jewellery-peer-comps. You do every download by hand. The code never scrapes anything.

Facts in the table below were checked on 3 Oct 2026 against the public Screener.in company pages and the NSE All Reports page. Re-check if something looks off.

## Rules

1. No scraping and no automated downloads. NSE terms prohibit automated collection. Screener is a manual export too.
2. Sign up and sign in to Screener yourself. Never paste your password into code, chat, or a config file.
3. Raw files stay on your laptop. Do not commit them. Check `.gitignore` has `data/raw/` before your first `git add`.
4. Check Screener's terms before sharing any raw export or any table that is mostly raw Screener data. Share your own computed outputs, not their files.
5. Every file gets an as-of date in `data/raw/MANIFEST.csv` (see below).

## Company table

| Company | NSE symbol | Screener URL | Consolidated? | FY end | Notes |
|---|---|---|---|---|---|
| Titan Company | TITAN | https://www.screener.in/company/TITAN/consolidated/ | Yes. Use consolidated. | 31 March | Target company. Jewellery is the bulk of sales, but watches, eyecare and CaratLane are also in the consolidated numbers. Borrowings likely include gold-on-lease (a gold metal loan). Check the annual report note. |
| Kalyan Jewellers | KALYANKJIL | https://www.screener.in/company/KALYANKJIL/consolidated/ | Yes. Use consolidated. | 31 March | Has Middle East and US operations. Franchise-owned-company-operated (FOCO) stores exist. Watch gold metal loans and leases. |
| Senco Gold | SENCO | https://www.screener.in/company/SENCO/consolidated/ | Yes. Use consolidated. | 31 March | Strong in Eastern India. Announced an acquisition (AJPL / Melorra) with paperwork due by 31 Oct 2026. Could change consolidation in the Q2 FY27 refresh. |
| Thangamayil Jewellery | THANGAMAYL | https://www.screener.in/company/THANGAMAYL/ | No. The consolidated page was empty when checked. Use the standalone page. | 31 March | Tamil Nadu focus. Confirm the Export to Excel button shows on the standalone page. If a consolidated page appears later, switch and note it. |
| P N Gadgil Jewellers | PNGJL | https://www.screener.in/company/PNGJL/consolidated/ | Yes. Use consolidated. | 31 March | Maharashtra focus. Recently listed (2024 RHP). Completed a 100% acquisition of Silvostyle Jewellers on 1 Oct 2026, so group scope may change. Screener flags possible interest capitalisation. |
| Trent | TRENT | https://www.screener.in/company/TRENT/consolidated/ | Yes. Use consolidated. | 31 March | Lifestyle reference only. Not a jewellery peer. Screener files it under Speciality Retail, not jewellery. Excluded from the jewellery median. Heavy lease cost, so Ind AS 116 matters most here. |

All six symbols matched the NSE ticker shown on each Screener page. No corrections needed.

## Q2 FY27 results timing

Not announced for any of the six as of 3 Oct 2026. I found no board meeting notice. Trent has closed its trading window from 24 Sep 2026 until 48 hours after Q2/H1 results, so its results are coming, date unknown. Last year the Q2 calls for these companies were in November. Plan for Oct to Nov 2026 and check each company's BSE/NSE announcements page for the board meeting notice.

Latest quarter on all six Screener pages today is June 2026 (Q1 FY27).

## Step 1: Screener account (you do this)

1. Open https://www.screener.in/ in your browser.
2. Create a free account yourself, or sign in if you have one.
3. Use a password you do not use anywhere else.
4. Do not share the login with any tool or agent.

## Step 2: Export each company

Do this for all six companies, one at a time.

1. Open the Screener URL from the table. Use the exact URL, including `/consolidated/` where the table says so.
2. Check the page says "Consolidated" above the Quarterly Results table (except Thangamayil).
3. Check the latest quarter column says Jun 2026.
4. Click **Export to Excel** near the top right, next to the share price.
5. If Screener asks you to sign in, sign in and click the button again.
6. Move the downloaded file to `data/raw/screener/` and rename it exactly:

| Company | Filename |
|---|---|
| Titan | `data/raw/screener/TITAN.xlsx` |
| Kalyan | `data/raw/screener/KALYANKJIL.xlsx` |
| Senco | `data/raw/screener/SENCO.xlsx` |
| Thangamayil | `data/raw/screener/THANGAMAYL.xlsx` |
| P N Gadgil | `data/raw/screener/PNGJL.xlsx` |
| Trent | `data/raw/screener/TRENT.xlsx` |

7. Open the file once. Confirm there is a "Data Sheet" tab with profit and loss, balance sheet and cash flow blocks. Confirm the company name matches.
8. Note whether the sheet shows number of shares, face value and current price. If not, the code must derive shares from equity capital and face value. Tell the code agent which one you saw.

Screener's own price in the file is the price at download time. Do not use it for the comps. Use the bhavcopy close instead (Step 3), so every company has the same date.

## Step 3: NSE bhavcopy (prices)

Why: one official closing price per company on one date.

1. Open https://www.nseindia.com/all-reports in your browser.
2. Find the section for the date you want.
3. Download **CM-UDiFF Common Bhavcopy Final (zip)**.
4. The file is named `BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`. Example for 1 Oct 2026: `BhavCopy_NSE_CM_0_0_0_20261001_F_0000.csv.zip`.
5. Save it as is into `data/raw/nse/`. Do not rename it. The date is in the name.
6. You can unzip it, or let the code read the zip.
7. The page also links a format readme (`new_bhavcopy_format_readme.xlsx`). Save it to `data/raw/nse/` and use it to confirm the column names. Expect symbol, series and close price columns. Keep only series EQ.

Which date to use:

- Main date: use one date for all six companies. Prefer the latest trading day when you run the comps.
- Valuation date: both Titan models (titan-valuation) now use the NSE close of 1 Oct 2026 (Rs 4,515.70), the same date as the comps, so one bhavcopy covers both.
- Refresh date: after most peers report Q2 FY27, download a new bhavcopy and re-run.
- If a date was a market holiday, there is no file. Use the previous trading day and say so.

## Step 4: Record as-of dates

Keep `data/raw/MANIFEST.csv` by hand. One row per file.

| Column | Meaning |
|---|---|
| file | Path under `data/raw/` |
| source | Screener or NSE |
| symbol | NSE symbol, blank for the zip |
| downloaded_on | Date you downloaded (YYYY-MM-DD) |
| as_of | For Screener: latest quarter in the file (for example 2026-06-30). For NSE: trade date |
| basis | consolidated or standalone |
| notes | Anything odd, like a missing line item |

Your note and chart must print: price date, latest balance sheet date, LTM period end, and download date.

## Step 5: Do not commit raw files

- `.gitignore` should contain `data/raw/`.
- Keep one tiny fake sample file in `tests/fixtures/` so tests and CI run without real data.
- Before each commit, run `git status` and check no `.xlsx`, bhavcopy `.csv` or `.zip` is staged.
- If you committed one by mistake, stop and fix the history before you push.

## What to check when data looks wrong

- A number is 100x off: Screener shows Rs crore, NSE shows rupees per share. Keep units straight.
- Shares changed: splits and bonus issues. Check face value in the file.
- Missing inventory days or payables for a year: Screener leaves blanks on some pages. Mark as n/a. Do not fill with zero.
- Thangamayil standalone versus others consolidated: say this in the note.
- Senco and PN Gadgil acquisitions: the Jun 2026 balance sheet will not include them. State this in limitations.
