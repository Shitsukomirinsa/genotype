# src/game_logic.py
import time
from src.romaji_parser import RomajiParser
from typing import List

TABLE_PATH = "./data/romaji_table.json"

class GameState:
    """Manages the current typing game state."""
    def __init__(self, target: str):
        self.reset(target)

    def reset(self, target: str):
        self.target: str = target
        self.typed_kana: str = ""
        self.parser: RomajiParser = RomajiParser(TABLE_PATH)
        self.start_time: float = None
        self.key_count: int = 0
        self.mistakes: int = 0

    def feed(self, ch: str) -> List[str]:
        """Feed one character, update typed_kana and track mistakes."""
        if not ch:
            return []

        if self.start_time is None:
            self.start_time = time.time()
        self.key_count += 1

        produced = self.parser.feed(ch)
        for k in produced:
            self.typed_kana += k
            # Count mistakes if typed_kana deviates from target prefix
            if not self.target.startswith(self.typed_kana):
                self.mistakes += 1
        return produced

    def flush(self) -> List[str]:
        """Flush remaining parser buffer at the end of input."""
        produced = self.parser.flush()
        for k in produced:
            self.typed_kana += k
            if not self.target.startswith(self.typed_kana):
                self.mistakes += 1
        return produced

    def elapsed_time(self) -> float:
        """Return elapsed time since first key press."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def wpm(self) -> int:
        """Compute WPM based on typed characters."""
        elapsed = max(self.elapsed_time(), 1e-6)  # avoid div0
        minutes = elapsed / 60
        chars = len(self.typed_kana)
        return int((chars / 5) / minutes)

    def accuracy(self) -> float:
        """Compute accuracy percentage."""
        if self.key_count == 0:
            return 100.0
        return max(0.0, 100.0 - self.mistakes / self.key_count * 100)
