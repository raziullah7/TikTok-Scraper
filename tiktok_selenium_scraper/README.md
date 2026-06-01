# TikTok Selenium Metadata Scraper

Python Selenium scraper for collecting public metadata from the latest videos on
a TikTok profile. It is intended for educational use and browser automation
experiments.

The scraper accepts a TikTok username and a post count, opens the profile,
collects the latest video URLs from the profile grid, then visits each video and
returns metadata as JSON.

## Features

- Scrape the latest `N` public posts from a TikTok profile.
- Collect video URL, views, likes, comments, saved/favorite count, and shares.
- Run in a fresh Selenium Chrome session.
- Attach to an existing Brave browser session with `--connect-brave`.
- Export results to JSON with `--output`.
- Includes unit tests for CLI parsing and count parsing helpers.

## Requirements

- Python 3.10 or newer
- Google Chrome, Chromium, or Brave
- Selenium 4

Install the Python dependency with:

```bash
pip install -r requirements.txt
```

For an isolated setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

Run a visible browser session:

```bash
python tiktok_scraper.py @numnumasmr11 5 --no-headless -o posts.json
```

Run headless:

```bash
python tiktok_scraper.py @numnumasmr11 5 -o posts.json
```

Print JSON to the terminal instead of saving it:

```bash
python tiktok_scraper.py @numnumasmr11 5
```

## Using an Existing Brave Session

TikTok may show login, captcha, or verification prompts in automated browsers.
If you want Selenium to use your existing Brave session, start Brave with remote
debugging enabled:

```bash
brave-browser --remote-debugging-port=9222
```

Then run:

```bash
python tiktok_scraper.py @numnumasmr11 5 --connect-brave --timeout 120 -o posts.json
```

`--connect-brave` attaches to `127.0.0.1:9222` by default and opens a new tab in
that browser session. If Brave is installed somewhere unusual, pass the binary
path explicitly:

```bash
python tiktok_scraper.py @numnumasmr11 5 --connect-brave --brave-binary /usr/bin/brave-browser -o posts.json
```

If you used a different debugging port:

```bash
python tiktok_scraper.py @numnumasmr11 5 --connect-brave --brave-debugger-address 127.0.0.1:9333
```

## CLI Options

```text
python tiktok_scraper.py <username> <count> [options]
```

Arguments:

- `username`: TikTok username, with or without `@`.
- `count`: Number of latest posts to scrape.

Options:

- `--headless` / `--no-headless`: run Chrome hidden or visible.
- `--timeout SECONDS`: seconds to wait for TikTok elements.
- `--scroll-pause SECONDS`: delay after scrolling the profile grid.
- `--connect-brave`: attach to a Brave/Chromium session on a debugging port.
- `--brave-debugger-address HOST:PORT`: debugger address for Brave attach mode.
- `--brave-binary PATH`: optional Brave executable path.
- `-o, --output PATH`: write JSON output to a file.

## Output Format

Example:

```json
{
  "platform": "tiktok",
  "username": "numnumasmr11",
  "requested_count": 1,
  "scraped_count": 1,
  "posts": [
    {
      "index": 1,
      "video_url": "https://www.tiktok.com/@numnumasmr11/video/7645112093816999181",
      "views": 105500000,
      "likes": 3000000,
      "comments": 79400,
      "saved": 312400,
      "shares": 121000
    }
  ]
}
```

If a video page loads but one post fails to scrape fully, the post object will
include an `error` field for that item.

## Selectors Used

The scraper currently reads:

- Views: `strong[data-e2e="video-views"]` near the profile-grid video link
- Likes: `strong[data-e2e="like-count"]`
- Comments: `strong[data-e2e="comment-count"]`
- Saved/favorites: `strong[data-e2e="favorite-count"]`
- Shares: `strong[data-e2e="share-count"]`

Fallback selectors are included for some older TikTok markup variants.

## Troubleshooting

If the scraper cannot find videos, try a visible browser:

```bash
python tiktok_scraper.py @username 5 --no-headless --timeout 120
```

If TikTok blocks a fresh Selenium browser, use Brave attach mode and clear any
prompt manually in the opened tab:

```bash
brave-browser --remote-debugging-port=9222
python tiktok_scraper.py @username 5 --connect-brave --timeout 120 -o posts.json
```

If Selenium reports a ChromeDriver version mismatch, make sure `--connect-brave`
can find your Brave binary or pass `--brave-binary` explicitly.

TikTok changes its frontend often. If values become `null`, inspect the current
video page DOM and update the selectors in `tiktok_scraper.py`.

## Tests

```bash
python -m unittest discover -s tests
python -m py_compile tiktok_scraper.py
```

## Responsible Use

Use this only on public pages you are allowed to access. The script does not log
in for you, bypass captchas, evade platform protections, or use stealth plugins.
Respect TikTok's terms, rate limits, robots guidance, and applicable laws.
