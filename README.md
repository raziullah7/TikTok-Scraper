# TikTok Metadata Scraper

An educational **Python/Selenium** CLI that collects public profile video URLs and displayed engagement counts, then exports JSON.

**Live compatibility has not been recently verified.** Historical outputs do not establish that current TikTok pages remain compatible.

## Features

Explicit waits, profile scrolling, URL deduplication, abbreviated-count parsing, configurable browser options, and per-video error reporting. Helper tests cover parsing, CLI options, and browser configuration.

## Run

Requires Python 3.10+, Chrome/Chromium or Brave, and Selenium 4.20+. Create and activate a virtual environment, then:

```bash
cd tiktok_selenium_scraper
python -m pip install -r requirements.txt
python tiktok_scraper.py @username 5 --no-headless -o posts.json
```

Replace `@username` with an accessible public profile. The requested count is an upper bound; unavailable counts are `null`, and returned posts may contain errors.

See the [detailed guide](tiktok_selenium_scraper/README.md) for environment activation, CLI options, Brave mode, and troubleshooting.

## Checks

From `tiktok_selenium_scraper/`:

```bash
python -m unittest discover -s tests
python -m py_compile tiktok_scraper.py
```

These checks were not rerun for this documentation update and do not validate live target pages.

[Implementation](tiktok_selenium_scraper/tiktok_scraper.py) · [Other scraping projects](https://github.com/raziullah7/raziullah7/blob/main/docs/web-scraping.md)

