# Romaji -> Hiragana parser (greedy, partial-match allowed)

import json
import os


class RomajiParser:
    VOWELS = set("aiueo")
    EMPTY = ""

    def __init__(self, table_path=None):
        """
        Load romaji-to-kana table and prepare sorted romaji keys
        (longest-first) for greedy matching.
        """
        if table_path is None:
            table_path = os.path.join(
                os.path.dirname(__file__), "romaji_table.json"
            )
        with open(table_path, "r", encoding="utf-8") as f:
            self.table = json.load(f)

        # Keys sorted by length (desc) to match longer sequences first
        self.romaji_keys = sorted(
            (k for k in self.table.keys() if k),
            key=len,
            reverse=True
        )
        self.buffer = ""
        self.output = []

    # ---- helpers ---------------------------------------------------------

    def _produce(self, kana):
        """Append kana or literal character to output."""
        self.output.append(kana)

    def _is_gemination(self, idx):
        """
        Check if the match position indicates a gemination,
        e.g., 'kk', 'tt'.
        """
        return idx > 0 and self.buffer[idx - 1] == self.buffer[idx]

    def _emit_literal(self, c):
        """Output literal character."""
        self._produce(c)

    # ---- romaji rule matching --------------------------------------------

    def _consume_first_match(self):
        """
        Search for the earliest romaji key appearing in the buffer.
        Not prefix-only: matches anywhere.
        Emits any left-side literal or gemination, then the matched kana,
        then consumes the matched segment from buffer.
        """
        for k in self.romaji_keys:
            idx = self.buffer.find(k)
            if idx == -1:
                continue

            kana = self.table.get(k)

            # Emit left part (literal or gemination)
            left = self.buffer[:idx]
            if self._is_gemination(idx):
                # Emit literal except the last same consonant, then gemination
                if idx > 1:
                    self._produce(left[:-1])
                self._produce("っ")
            else:
                if left:
                    self._produce(left)

            # Emit kana for the matched romaji sequence
            if kana is not None:
                self._produce(kana)

            # Consume buffer
            self.buffer = self.buffer[idx + len(k):]
            return True

        return False

    # ---- standalone 'n' logic --------------------------------------------

    def _try_n(self):
        """
        Consume standalone 'n' when safe.
        If next character is vowel / 'y' / 'n', wait for more input.
        """
        if not self.buffer.startswith("n"):
            return False

        # Only 'n' left → wait
        if len(self.buffer) == 1:
            return False

        nxt = self.buffer[1]

        # Cannot consume before vowel / y / n
        if nxt in self.VOWELS or nxt in ("y", "n"):
            return False

        # Emit ん
        self.buffer = self.buffer[1:]
        self._produce("ん")
        return True

    # ---- rule dispatcher -------------------------------------------------

    def _try_consume_left(self):
        """
        Try consuming from the left using the available rules.
        Returns True if something was consumed.
        """
        if self._try_n():
            return True
        if self._consume_first_match():
            return True
        return False

    # ---- public API ------------------------------------------------------

    def feed(self, ch):
        """
        Feed one character. Emit kana immediately when possible.
        Returns a list of produced kana (may be empty).
        """
        if not ch:
            return []

        # Literal passthrough when buffer is empty
        if not ch.isalpha() and self.buffer == "":
            self._produce(ch)
            return [self.output[-1]]

        # Append to processing buffer
        self.buffer += ch.lower()
        produced = []

        # Apply rules repeatedly
        while self._try_consume_left():
            produced.append(self.output[-1])

        return produced

    def flush(self):
        """
        Resolve remaining buffer when input ends.
        Handles final 'n', leftover matches, and literal fallback.
        """
        produced = []
        while self.buffer:
            if self._try_consume_left():
                produced.append(self.output[-1])
                continue

            # Final leftover 'n'
            if self.buffer.startswith("n"):
                self.buffer = self.buffer[1:]
                self._produce("ん")
                produced.append("ん")
                continue

            # Literal fallback
            c = self.buffer[0]
            self.buffer = self.buffer[1:]
            self._emit_literal(c)
            produced.append(c)

        return produced

    def get_output(self):
        """Return full concatenated kana output."""
        return self.EMPTY.join(self.output)

    def reset_output(self):
        """Clear output buffer."""
        self.output = []
