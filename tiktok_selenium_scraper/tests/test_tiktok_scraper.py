import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tiktok_scraper import (  # noqa: E402
    configure_chrome_options,
    extract_likes_from_aria_label,
    normalize_username,
    parse_args,
    parse_display_count,
    comment_count_selectors,
    favorite_count_selectors,
    like_count_selectors,
    share_count_selectors,
)


class TikTokScraperHelpersTest(unittest.TestCase):
    def test_normalize_username_strips_spaces_and_at_symbol(self):
        self.assertEqual(normalize_username("  @education_daily  "), "education_daily")

    def test_parse_display_count_handles_commas_and_suffixes(self):
        cases = {
            "1,234": 1234,
            "987": 987,
            "1.2K": 1200,
            "3M": 3000000,
            "4.5B": 4500000000,
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_display_count(raw), expected)

    def test_extract_likes_from_aria_label_uses_number_before_likes(self):
        self.assertEqual(extract_likes_from_aria_label("1.5K Likes"), 1500)

    def test_parse_args_accepts_connect_brave(self):
        args = parse_args(["@numnumasmr11", "5", "--connect-brave"])

        self.assertTrue(args.connect_brave)
        self.assertEqual(args.brave_debugger_address, "127.0.0.1:9222")

    def test_connect_brave_configures_debugger_without_headless_argument(self):
        class FakeOptions:
            def __init__(self):
                self.arguments = []
                self.debugger_address = None
                self.binary_location = None

            def add_argument(self, argument):
                self.arguments.append(argument)

        options = FakeOptions()

        configure_chrome_options(
            options,
            headless=True,
            debugger_address="127.0.0.1:9222",
            browser_binary="/usr/bin/brave-browser",
        )

        self.assertEqual(options.debugger_address, "127.0.0.1:9222")
        self.assertEqual(options.binary_location, "/usr/bin/brave-browser")
        self.assertNotIn("--headless=new", options.arguments)

    def test_count_selectors_include_current_and_browse_variants(self):
        self.assertIn('strong[data-e2e="like-count"]', like_count_selectors())
        self.assertIn('strong[data-e2e="comment-count"]', comment_count_selectors())
        self.assertIn('strong[data-e2e="browse-comment-count"]', comment_count_selectors())
        self.assertIn('strong[data-e2e="favorite-count"]', favorite_count_selectors())
        self.assertIn('strong[data-e2e="browse-favorite-count"]', favorite_count_selectors())
        self.assertIn('strong[data-e2e="share-count"]', share_count_selectors())
        self.assertIn('strong[data-e2e="share count"]', share_count_selectors())


if __name__ == "__main__":
    unittest.main()
