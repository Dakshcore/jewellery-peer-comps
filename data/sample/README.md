# Sample data

Raw data is not redistributed in this repository. Screener.in workbooks and NSE bhavcopy files are
third-party data, so `data/raw/` is git-ignored: download your own copies (see the main README) and
save them there.

The unit tests do not need real data. They build small synthetic Screener-style workbooks and a tiny
bhavcopy CSV in a temporary folder (see `tests/synthetic.py`).
