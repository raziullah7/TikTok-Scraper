import argparse
import json
import re
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable


COUNT_RE = re.compile(r"(?P<number>\d+(?:\.\d+)?)\s*(?P<suffix>[KMB])?", re.IGNORECASE)
COUNT_MULTIPLIERS = {
    "": 1,
    "K": 1_000,
    "M": 1_000_000,
    "B": 1_000_000_000,
}
BRAVE_BINARY_CANDIDATES = (
    "brave-browser",
    "brave",
    "brave-browser-stable",
)


@dataclass(frozen=True)
class VideoRef:
    url: str
    views: int | None = None


@dataclass
class PostMetadata:
    index: int
    video_url: str
    views: int | None
    likes: int | None
    comments: int | None
    saved: int | None
    shares: int | None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if data["error"] is None:
            data.pop("error")
        return data


def normalize_username(username: str) -> str:
    normalized = username.strip().lstrip("@")
    if not normalized:
        raise ValueError("Username cannot be empty.")
    return normalized


def parse_display_count(raw_value: Any) -> int | None:
    if raw_value is None:
        return None

    text = str(raw_value).strip().replace(",", "")
    if not text:
        return None

    match = COUNT_RE.search(text)
    if not match:
        return None

    number = float(match.group("number"))
    suffix = (match.group("suffix") or "").upper()
    return int(number * COUNT_MULTIPLIERS[suffix])


def extract_likes_from_aria_label(aria_label: str | None) -> int | None:
    if not aria_label:
        return None

    match = re.search(r"(.+?)\s+Likes\b", aria_label, re.IGNORECASE)
    if not match:
        return None

    return parse_display_count(match.group(1))


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("count must be a positive integer") from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("count must be a positive integer")

    return parsed


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape public TikTok profile video metadata with Selenium."
    )
    parser.add_argument("username", help="TikTok username, with or without @")
    parser.add_argument("count", type=positive_int, help="Number of latest posts to scrape")
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run Chrome in headless mode. Use --no-headless for manual inspection.",
    )
    parser.add_argument(
        "--timeout",
        type=positive_int,
        default=20,
        help="Seconds to wait for TikTok page elements.",
    )
    parser.add_argument(
        "--scroll-pause",
        type=float,
        default=1.0,
        help="Seconds to wait after scrolling the profile page.",
    )
    parser.add_argument(
        "--connect-brave",
        action="store_true",
        help=(
            "Attach to an existing Brave/Chromium session started with "
            "--remote-debugging-port."
        ),
    )
    parser.add_argument(
        "--brave-debugger-address",
        default="127.0.0.1:9222",
        help="Debugger address for --connect-brave. Defaults to 127.0.0.1:9222.",
    )
    parser.add_argument(
        "--brave-binary",
        help="Optional Brave executable path, for example /usr/bin/brave-browser.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional JSON output file. Defaults to printing JSON to stdout.",
    )
    return parser.parse_args(argv)


def find_brave_binary() -> str | None:
    for candidate in BRAVE_BINARY_CANDIDATES:
        path = shutil.which(candidate)
        if path:
            return path

    return None


def configure_chrome_options(
    options: Any,
    headless: bool = True,
    debugger_address: str | None = None,
    browser_binary: str | None = None,
) -> Any:
    if browser_binary:
        options.binary_location = browser_binary

    if debugger_address:
        options.debugger_address = debugger_address
    elif headless:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    return options


def create_driver(
    headless: bool = True,
    debugger_address: str | None = None,
    browser_binary: str | None = None,
):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Selenium is not installed. Run: pip install -r requirements.txt"
        ) from exc

    if debugger_address and not browser_binary:
        browser_binary = find_brave_binary()

    options = configure_chrome_options(
        Options(),
        headless=headless,
        debugger_address=debugger_address,
        browser_binary=browser_binary,
    )

    return webdriver.Chrome(options=options)


def load_selenium_support():
    try:
        from selenium.common.exceptions import TimeoutException
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Selenium is not installed. Run: pip install -r requirements.txt"
        ) from exc

    return By, EC, TimeoutException, WebDriverWait


def element_text(element: Any) -> str:
    return (element.text or element.get_attribute("textContent") or "").strip()


def canonical_video_url(url: str) -> str:
    return url.split("?", 1)[0]


def find_view_count_near_link(link: Any, by: Any) -> int | None:
    view_count_xpaths = [
        ".//ancestor::div[1]//strong[@data-e2e='video-views']",
        ".//ancestor::div[2]//strong[@data-e2e='video-views']",
        ".//ancestor::div[3]//strong[@data-e2e='video-views']",
    ]

    for xpath in view_count_xpaths:
        for element in link.find_elements(by.XPATH, xpath):
            parsed = parse_display_count(element_text(element))
            if parsed is not None:
                return parsed

    return None


def open_new_tab(driver: Any) -> None:
    existing_handles = set(driver.window_handles)
    try:
        driver.switch_to.new_window("tab")
        return
    except Exception:
        driver.execute_script("window.open('about:blank', '_blank');")

    for handle in driver.window_handles:
        if handle not in existing_handles:
            driver.switch_to.window(handle)
            return


def collect_latest_video_refs(
    driver: Any,
    username: str,
    limit: int,
    timeout: int,
    scroll_pause: float,
) -> list[VideoRef]:
    by, ec, timeout_exception, wait_cls = load_selenium_support()
    normalized = normalize_username(username)
    driver.get(f"https://www.tiktok.com/@{normalized}")

    wait = wait_cls(driver, timeout)
    try:
        wait.until(ec.presence_of_element_located((by.CSS_SELECTOR, 'a[href*="/video/"]')))
    except timeout_exception as exc:
        raise RuntimeError(
            "Could not find profile video links. TikTok may have changed its page "
            "markup, the profile may be private/missing, or a login/captcha page may "
            "be blocking the browser."
        ) from exc

    refs_by_url: dict[str, VideoRef] = {}
    max_scrolls = max(4, min(50, limit * 3))

    for _ in range(max_scrolls):
        video_links = driver.find_elements(by.CSS_SELECTOR, 'a[href*="/video/"]')
        for link in video_links:
            href = link.get_attribute("href")
            if not href or "/video/" not in href:
                continue

            url = canonical_video_url(href)
            if url in refs_by_url:
                continue

            refs_by_url[url] = VideoRef(
                url=url,
                views=find_view_count_near_link(link, by),
            )
            if len(refs_by_url) >= limit:
                return list(refs_by_url.values())

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)

    return list(refs_by_url.values())[:limit]


def first_text_by_css(driver: Any, by: Any, selector: str) -> str | None:
    elements = driver.find_elements(by.CSS_SELECTOR, selector)
    if not elements:
        return None

    text = element_text(elements[0])
    return text or None


def first_count_by_css(driver: Any, by: Any, selector: str) -> int | None:
    return parse_display_count(first_text_by_css(driver, by, selector))


def like_count_selectors() -> tuple[str, ...]:
    return (
        'strong[data-e2e="like-count"]',
        'strong[data-e2e="browse-like-count"]',
    )


def comment_count_selectors() -> tuple[str, ...]:
    return (
        'strong[data-e2e="comment-count"]',
        'strong[data-e2e="browse-comment-count"]',
    )


def favorite_count_selectors() -> tuple[str, ...]:
    return (
        'strong[data-e2e="favorite-count"]',
        'strong[data-e2e="browse-favorite-count"]',
    )


def share_count_selectors() -> tuple[str, ...]:
    return (
        'strong[data-e2e="share-count"]',
        'strong[data-e2e="share count"]',
    )


def video_metric_wait_selector() -> str:
    selectors = (
        like_count_selectors()
        + comment_count_selectors()
        + favorite_count_selectors()
        + share_count_selectors()
        + ('button[aria-label]',)
    )
    return ', '.join(selectors)


def first_count_by_css_any(
    driver: Any,
    by: Any,
    selectors: Iterable[str],
) -> int | None:
    for selector in selectors:
        count = first_count_by_css(driver, by, selector)
        if count is not None:
            return count

    return None


def read_likes_count(driver: Any, by: Any) -> int | None:
    count = first_count_by_css_any(driver, by, like_count_selectors())
    if count is not None:
        return count

    for button in driver.find_elements(by.CSS_SELECTOR, 'button[aria-label]'):
        likes = extract_likes_from_aria_label(button.get_attribute("aria-label"))
        if likes is not None:
            return likes

    return None


def scrape_video_metadata(
    driver: Any,
    ref: VideoRef,
    index: int,
    timeout: int,
) -> PostMetadata:
    by, ec, _, wait_cls = load_selenium_support()
    driver.get(ref.url)

    wait = wait_cls(driver, timeout)
    wait.until(
        ec.presence_of_element_located(
            (
                by.CSS_SELECTOR,
                video_metric_wait_selector(),
            )
        )
    )

    return PostMetadata(
        index=index,
        video_url=ref.url,
        views=ref.views,
        likes=read_likes_count(driver, by),
        comments=first_count_by_css_any(driver, by, comment_count_selectors()),
        saved=first_count_by_css_any(driver, by, favorite_count_selectors()),
        shares=first_count_by_css_any(driver, by, share_count_selectors()),
    )


def scrape_profile(
    username: str,
    count: int,
    headless: bool = True,
    timeout: int = 20,
    scroll_pause: float = 1.0,
    debugger_address: str | None = None,
    browser_binary: str | None = None,
) -> dict[str, Any]:
    normalized = normalize_username(username)
    driver = create_driver(
        headless=headless,
        debugger_address=debugger_address,
        browser_binary=browser_binary,
    )

    try:
        if debugger_address:
            open_new_tab(driver)

        video_refs = collect_latest_video_refs(
            driver=driver,
            username=normalized,
            limit=count,
            timeout=timeout,
            scroll_pause=scroll_pause,
        )

        posts: list[PostMetadata] = []
        for index, ref in enumerate(video_refs, start=1):
            try:
                posts.append(
                    scrape_video_metadata(
                        driver=driver,
                        ref=ref,
                        index=index,
                        timeout=timeout,
                    )
                )
            except Exception as exc:
                posts.append(
                    PostMetadata(
                        index=index,
                        video_url=ref.url,
                        views=ref.views,
                        likes=None,
                        comments=None,
                        saved=None,
                        shares=None,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )

        return {
            "platform": "tiktok",
            "username": normalized,
            "requested_count": count,
            "scraped_count": len(posts),
            "posts": [post.to_dict() for post in posts],
        }
    finally:
        if not debugger_address:
            driver.quit()


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        result = scrape_profile(
            username=args.username,
            count=args.count,
            headless=args.headless,
            timeout=args.timeout,
            scroll_pause=args.scroll_pause,
            debugger_address=(
                args.brave_debugger_address if args.connect_brave else None
            ),
            browser_binary=args.brave_binary,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    json_output = json.dumps(result, indent=4, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(json_output + "\n")
    else:
        print(json_output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
