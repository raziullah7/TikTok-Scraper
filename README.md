# TikTok Metadata Scraper

A Python and Selenium browser automation project that collects public video metadata from a TikTok profile and exports it as JSON. It gathers video links from the profile grid, visits each video, and parses displayed engagement counts.

**Verification status: Not recently verified.** The source and documentation have been reviewed; compatibility with the current TikTok website has not been checked in a recent live run.

## Implemented features

- Browser automation with explicit waits, profile scrolling, and duplicate URL filtering.
- Parsing displayed counts such as `1.2K` and `3M` into integers.
- A configurable CLI with headless and visible Chrome modes, timeouts, and JSON export.
- Per-video error reporting and helper tests for parsing, CLI options, and browser configuration.

## Architecture and workflow

The CLI opens a profile, scrolls its video grid, deduplicates video URLs, visits each video, parses displayed counts, and returns structured JSON. A failure on an individual video is recorded with that post so other collected results can still be returned.

## Setup and usage

Requirements: **Python 3.10+**, **Chrome/Chromium or Brave**, and **Selenium 4.20+**.

```bash
git clone https://github.com/raziullah7/TikTok-Scraper.git
cd TikTok-Scraper/tiktok_selenium_scraper
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Then install the dependency and run the scraper. Replace `@username` with a public profile you are allowed to access:

```bash
python -m pip install -r requirements.txt
python tiktok_scraper.py @username 5 --no-headless -o posts.json
```

Omit `--no-headless` to use the default headless mode. Omit `-o posts.json` to print JSON to the terminal. The requested count is an upper limit; the number of collected posts may be lower.

For the complete CLI reference, Brave attachment mode, selectors, and troubleshooting, see the [detailed guide](tiktok_selenium_scraper/README.md).

## Output

The JSON result contains `platform`, `username`, `requested_count`, `scraped_count`, and a `posts` array. Each post contains:

| Field | Meaning |
| --- | --- |
| `index`, `video_url` | Position in the collected results and canonical video URL |
| `views` | View count read from the profile grid |
| `likes`, `comments`, `saved`, `shares` | Engagement counts read from the video page |
| `error` | Included when a video could not be scraped successfully |

Unavailable counts are `null`. Displayed abbreviations are converted to integers, so values reflect the website's displayed precision. `scraped_count` includes collected posts with an `error` entry; it is not a count of fully populated records.

## Existing checks

From `tiktok_selenium_scraper/`:

```bash
python -m unittest discover -s tests
python -m py_compile tiktok_scraper.py
```

The [helper tests](tiktok_selenium_scraper/tests/test_tiktok_scraper.py) cover username normalization, count parsing, CLI options, selector lists, and browser configuration. They do not validate live TikTok pages. These commands are provided for local verification; no current passing result is claimed here.

## Project files

- [Scraper implementation](tiktok_selenium_scraper/tiktok_scraper.py)
- [Setup, CLI reference, and troubleshooting](tiktok_selenium_scraper/README.md)
- [Python dependency](tiktok_selenium_scraper/requirements.txt)
- [Helper tests](tiktok_selenium_scraper/tests/test_tiktok_scraper.py)

## Current status

This is an educational browser automation project. TikTok's markup and access requirements can change, so selectors and browser behavior may need updating. Live-site operation has not been recently verified.

For my other Selenium, Scrapy, and Beautiful Soup projects, see the [web scraping collection](https://github.com/raziullah7/raziullah7/blob/main/docs/web-scraping.md).
