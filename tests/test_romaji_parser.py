# test_romaji_parser.py
import unittest
from src.romaji_parser import RomajiParser, os, json

# Minimal test table if romaji_table.json is not available
TEST_TABLE = {
    "a": "あ", "i": "い", "u": "う", "e": "え", "o": "お",
    "ka": "か", "ki": "き", "ku": "く", "ke": "け", "ko": "こ",
    "sa": "さ", "shi": "し", "si": "し", "su": "す", "se": "せ", "so": "そ",
    "ta": "た", "chi": "ち", "ti": "ち", "tsu": "つ", "tu": "つ", "te": "て", "to": "と",
    "na": "な", "ni": "に", "nu": "ぬ", "ne": "ね", "no": "の",
    "ha": "は", "hi": "ひ", "fu": "ふ", "hu": "ふ", "he": "へ", "ho": "ほ",
    "ma": "ま", "mi": "み", "mu": "む", "me": "め", "mo": "も",
    "ya": "や", "yu": "ゆ", "yo": "よ",
    "ra": "ら", "ri": "り", "ru": "る", "re": "れ", "ro": "ろ",
    "wa": "わ", "wo": "を",
    "n": "ん", "nn": "ん", "kya": "きゃ", "nyu": "にゅ",
    "ti": "ち", "chi": "ち", "si": "し", "sh": "し"
}


class TestRomajiParser(unittest.TestCase):
    def setUp(self):
        # Create parser instance using the minimal test table
        # Temporarily override table by writing a JSON file
        self.table_path = "./data/romaji_table.json"
        self.parser = RomajiParser(self.table_path)

    def check_parse(self, romaji, expected):
        """Feed romaji input character by character and flush, then check output."""
        self.parser.reset_output()
        for ch in romaji:
            self.parser.feed(ch)
        self.parser.flush()
        self.assertEqual(self.parser.get_output(), expected)

    # ------------------------
    # Basic tests
    # ------------------------
    def test_simple_words(self):
        self.check_parse("konitiha", "こにちは")
        self.check_parse("konnnitiha", "こんにちは")
        self.check_parse("sanma", "さんま")
        self.check_parse("annna", "あんな")

    def test_small_tsu(self):
        self.check_parse("kko", "っこ")
        self.check_parse("gakkou", "がっこう")  # Requires extended table
        self.check_parse("ktta", "kった")
        self.check_parse("kccha", "kっちゃ")

    def test_special_n(self):
        self.check_parse("n", "ん")
        self.check_parse("nn", "ん")
        self.check_parse("na", "な")
        self.check_parse("ni", "に")
        self.check_parse("nni", "んい")

    def test_yoon(self):
        self.check_parse("kya", "きゃ")
        self.check_parse("nyu", "にゅ")

    def test_mixed(self):
        self.check_parse("konnichiwa", "こんいちわ")
        self.check_parse("annna", "あんな")
        self.check_parse("shinshi", "しんし")

    def test_chouon_and_symbols(self):
        # Long vowel mark ー should pass through as-is
        self.check_parse("ko-n-ni-chi-haー", "こ-ん-に-ち-はー")
        # Punctuation or other symbols should be preserved
        self.check_parse("kon-ni!?", "こん-に!?")
        # Mix of kana and long vowel / symbols
        self.check_parse("konnnichihaー!", "こんにちはー!")



if __name__ == "__main__":
    unittest.main()
