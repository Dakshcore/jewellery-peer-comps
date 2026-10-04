# Four-Week Plan

Budget: 8 to 10 hours a week. Each week below adds up to about 9 hours. Tick items as you go.

Suggested start: Monday 5 Oct 2026. Q2 FY27 results are due Oct to Nov 2026 and dates are not announced. Week 3 is built to flex around that.

Rule for every week: finish the "done" list before moving on. If you are 2 hours behind, drop the items marked (stretch).

---

## Week 1: Data and loaders (about 9 h)

Goal: all raw files in place, and Python can read each one into a clean table.

Detailed tasks:

- [ ] 0:30 Read `docs/DATA_GUIDE.md` end to end. Create or sign in to your Screener account.
- [ ] 0:45 Download the six Excel files. Rename exactly. Fill `data/raw/MANIFEST.csv`.
- [ ] 0:30 Download the NSE bhavcopy for 25 Sep 2026 and for the latest trading day. Save the format readme.
- [ ] 0:30 Open each Excel file by hand. Write down in a short note: sheet names, which rows hold sales, EBITDA inputs, borrowings, cash, equity capital, inventory. Note any line that is missing for a company.
- [ ] 0:30 Check `.gitignore` covers `data/raw/`. Run `git status` and confirm no raw file shows. Set up the virtual environment and run the tests once.
- [ ] 1:00 Write down the input schema in plain words: the list of fields each loader must return (period end, sales, operating profit, depreciation, interest, net profit, equity capital, reserves, borrowings, other assets, inventory days, and so on). One page. Match the code agent's names.
- [ ] 1:00 Run the Screener loader on TITAN. Compare 5 numbers by eye against the Screener web page. Fix mismatches or log them.
- [ ] 1:00 Run the loader on the other five. Log every company where a field is blank or labelled differently.
- [ ] 0:45 Run the bhavcopy loader. Check you get one close price per symbol for both dates. Check the 25 Sep 2026 Titan close equals the Rs 4,884 in your DCF.
- [ ] 0:45 Write tests for the loaders using a small fake fixture (no real files). Aim for: wrong filename, missing sheet, blank cell, wrong units.
- [ ] 0:30 Write a `data/raw/README` line or note listing known data gaps (for example Thangamayil standalone).
- [ ] 0:30 Commit with a clear message. Update the week log below.

Total about 8.5 h plus 0:30 slack.

Definition of done, Week 1:

- Six Screener files and two bhavcopy files are in `data/raw/`, none committed.
- MANIFEST has a row for every file.
- Loaders return a clean table for all six companies and both dates.
- Titan 25 Sep 2026 close matches your DCF input.
- Tests pass without real data.
- Known gaps are written down.

---

## Week 2: Prices, EV bridge, multiples (about 9 h)

Goal: one table of multiples per company, with every input traceable.

- [ ] 1:00 Fix the EV bridge on paper. Equity value + borrowings (decide how to treat gold metal loans and lease liabilities) - cash and liquid investments + minorities. Write the rule in `docs/` or in the code docstring.
- [ ] 1:00 Compute shares outstanding and market cap per company from bhavcopy price and Screener share data. Compare to Screener's market cap as a sanity check. Explain any gap above a small tolerance.
- [ ] 1:30 Build the EV bridge function. Add unit tests with a hand-worked example.
- [ ] 1:00 Compute LTM figures (last four quarters) for sales, EBITDA, net profit. Use the quarterly block. Print the LTM end date.
- [ ] 1:00 Compute EV/EBITDA, P/E, EV/Sales. Handle negative or tiny EBITDA by showing "n/m".
- [ ] 1:00 Compute growth (sales and profit, 3 year CAGR and LTM), EBITDA margin, ROCE, inventory days.
- [ ] 1:00 Review each company's numbers for outliers. Check at least one by hand against a company filing.
- [ ] 0:45 Decide treatment rules and write them down: Titan target, Trent separate, Thangamayil standalone.
- [ ] 0:45 Export the raw multiples table to CSV and print a readable version.

Definition of done, Week 2:

- Multiples table for all six companies on 25 Sep 2026 and on the latest date.
- Every input traces to a file, a date and a line.
- EV bridge rule is written down and tested.
- Any number you cannot explain is listed in a "to check" list.

---

## Week 3: Medians, football field, Q2 FY27 refresh (about 9 h)

Goal: the comps range, the chart, and a refresh with new results.

- [ ] 1:00 Compute peer medians, low and high for the four jewellery peers. Keep Trent out of the jewellery median. Show Trent as its own row.
- [ ] 1:00 Implied Titan value per share from each multiple (EV/EBITDA, P/E, EV/Sales). Use low to high and median. Show the math in a table.
- [ ] 1:30 Build the football-field chart: each multiple as a bar, plus a line for your DCF (Rs 4,052) and a line for the 25 Sep 2026 close (Rs 4,884). Label dates and units.
- [ ] 0:45 Check the chart reads clearly at A4 print size and in grayscale.
- [ ] 0:30 Check each company's BSE/NSE announcements for Q2 FY27 board meeting dates. Update the table in `DATA_GUIDE.md`.
- [ ] 2:00 Refresh (do when at least Titan and three peers have reported): re-download the Screener files and a new bhavcopy. Update MANIFEST. Re-run. Compare old and new in a short change log.
- [ ] 0:45 Check how Titan itself moved: LTM, margin, inventory days. Does the story change?
- [ ] 0:30 Write 5 to 8 lines on why comps and DCF differ (use your own words, with real numbers from the run).
- [ ] 0:30 (stretch) Add a sensitivity: treat gold metal loans as debt versus as working capital.

If results are late: do everything except the refresh line, then come back for 2 hours in Week 4. Move the PDF drafting up instead.

Definition of done, Week 3:

- Medians, low and high computed and tested.
- Football-field chart saved as PNG and SVG with dates on it.
- Refresh done, or a dated plan for it, with old versus new change log.
- A written list of reasons comps and DCF differ.

---

## Week 4: PDF note, README, CI, publish (about 9 h)

Goal: a public repo and a one to two page note you are proud to share.

- [ ] 2:00 Write the note from `docs/NOTE_TEMPLATE.md`. Fill every placeholder with a number from the run, or delete the sentence.
- [ ] 1:00 Build the PDF. Check it is at most two pages. Check dates, units and the disclaimer.
- [ ] 1:30 Write the README: what it does, what it does not do, how to get data (link to `DATA_GUIDE.md`), how to run, a screenshot of the chart, limitations, licence.
- [ ] 1:00 Set up CI: install, lint, run tests on fixtures only. No real data in CI.
- [ ] 0:45 Clean the repo. Confirm no raw data or secrets in history. Search for "xlsx", "password", "token".
- [ ] 0:45 Tag a release. Attach the PDF.
- [ ] 1:00 Ask one friend or senior to read the note cold. Fix what confuses them.
- [ ] 0:30 Draft the three LinkedIn posts from `docs/LINKEDIN_POSTS.md`. Post one at a time, a few days apart.
- [ ] 0:30 Read `docs/INTERVIEW_NOTES.md` and say each answer out loud once.

Definition of done, Week 4:

- Public repo with README, CI green, release tagged.
- PDF note, at most two pages, with disclaimer.
- No raw data committed.
- Three post drafts ready. Interview answers practised.

---

## Weekly log (copy each week)

```
Week N
Hours spent:
Done:
Blocked by:
Numbers I still cannot explain:
Next week first task:
```
