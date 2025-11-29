# typing_game_pyside6.py
# PySide6 タイピングゲーム（ローマ字->かなパーサ内蔵）
# Requires: PySide6
# Run: python typing_game_pyside6.py

import sys
import random
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QComboBox, QSlider
)
from PySide6.QtGui import QFont, QKeyEvent, QColor, QPainter, QPalette
from PySide6.QtCore import Qt, QTimer
from typing import List, Tuple
from src.romaji_parser import RomajiParser

TABLE_PATH = "./data/romaji_table.json"

# -------------------------
# Game target sentences (samples). 追加・読み替え可
# -------------------------
SENTENCES = [
    "こんにちは", "おはようございます", "ありがとうございます", "さようなら",
    "今日はいい天気ですね", "タイピングゲームを楽しもう", "さんま", "あんな", "しんぶん",
    "ちょっと", "きょうはにちようび", "プログラミングを学ぶ", "きゃりーぱみゅぱみゅ", "コンピュータ"
]

# -------------------------
# UI Widgets
# -------------------------
class TypingCanvas(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f1724, stop:1 #071122);"
                           "border-radius:12px;")
        self.target = ""
        self.pos = 0  # position in kana chars confirmed
        self.typed_kana = ""  # kana produced so far
        self.roman_buffer_display = ""  # what's currently in roman buffer (visual)
        self.parser = RomajiParser(TABLE_PATH)
        self.on_correct = None  # callback when progress changes (for stats)
        self.on_complete = None
        self.start_time = None
        self.key_count = 0

    def set_target(self, text):
        self.target = text
        self.pos = 0
        self.typed_kana = ""
        self.roman_buffer_display = ""
        self.parser = RomajiParser(TABLE_PATH)
        self.start_time = None
        self.key_count = 0
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        rect = self.contentsRect()
        # draw target: show completed part in dim, active char highlighted, remaining in grey
        font = QFont("Meiryo", 28)
        p.setFont(font)

        # layout positions
        margin = 20
        x = margin
        y = rect.height() // 2

        # draw completed kana
        completed = self.typed_kana
        remaining = self.target[len(completed):]

        # completed (dim)
        p.setPen(QColor(120, 200, 255))
        p.drawText(x, y, completed)

        # measure width of completed text to offset remaining
        metrics = p.fontMetrics()
        w = metrics.horizontalAdvance(completed)
        x += w

        # active next char highlight (if any)
        if remaining:
            next_char = remaining[0]
            # draw highlight box
            box_w = metrics.horizontalAdvance(next_char) + 12
            box_h = metrics.height() + 10
            p.setBrush(QColor(255, 255, 255, 20))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(x-6, y - metrics.ascent() - 6, box_w, box_h, 6, 6)
            p.setPen(QColor(255, 255, 200))
            p.drawText(x, y, next_char)
            x += metrics.horizontalAdvance(next_char)
            # draw rest
            p.setPen(QColor(180, 220, 255))
            p.drawText(x, y, remaining[1:])
        else:
            # finished
            p.setPen(QColor(120, 255, 170))
            p.drawText(x, y, "")

        # draw roman buffer below
        buf_font = QFont("Consolas", 14)
        p.setFont(buf_font)
        p.setPen(QColor(200,200,220,200))
        p.drawText(margin, y + 50, "roman buffer: " + self.parser.buffer)

    def keyPressEvent(self, event: QKeyEvent):
        # handle basic keys
        if event.key() == Qt.Key_Backspace:
            # rough handling: clear last typed roman char if any (simple behavior)
            if self.parser.buffer:
                self.parser.buffer = self.parser.buffer[:-1]
            else:
                # remove last kana produced (move pos back)
                if self.typed_kana:
                    self.typed_kana = self.typed_kana[:-1]
            self.update()
            return

        if event.key() == Qt.Key_Escape:
            self.setFocus(False)
            return

        ch = event.text()
        if not ch:
            return
        # only letters matter for romaji input; allow capitals too
        if ch.isalpha():
            # start timer on first key
            if self.start_time is None:
                self.start_time = time.time()
            self.key_count += 1
            produced = self.parser.feed(ch)
            # if parser produced kana, append them to typed_kana and advance pos accordingly
            for k in produced:
                self.typed_kana += k
            # check if newly produced kana match target at current progress
            # We do permissive acceptance: if typed_kana is longer than needed or mismatches, mark as mistake by NOT advancing?
            # For simplicity: we accept exact prefix matches, otherwise we register mistake visually by not advancing pos.
            # But here typed_kana is canonical; we compare
            if self.target.startswith(self.typed_kana):
                # valid progress
                pass
            else:
                # it's a mismatch: we keep it but visually indicate wrong (simple)
                # In a richer game you'd track errors; here we keep typed_kana anyway.
                pass

            # If the parser's buffer consumption leaves earlier produced kana that complete characters, check completion:
            if len(self.typed_kana) >= len(self.target):
                # finished
                if self.on_complete:
                    duration = time.time() - (self.start_time or time.time())
                    self.on_complete(duration, self.key_count)
            self.update()

        # ignore non-alpha (could extend to space/punctuation)
        return

# -------------------------
# Main Window
# -------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 タイピングゲーム")
        self.setMinimumSize(900, 420)

        # central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        header = QLabel("PySide6 Typing — ローマ字 → かな（リアルタイム）")
        header.setFont(QFont("Meiryo", 18))
        header.setStyleSheet("color: #cfe8ff;")
        layout.addWidget(header, alignment=Qt.AlignCenter)

        # top controls
        controls = QHBoxLayout()
        layout.addLayout(controls)

        self.sentence_combo = QComboBox()
        self.sentence_combo.addItems(SENTENCES)
        controls.addWidget(QLabel("お題："))
        controls.addWidget(self.sentence_combo)

        self.start_btn = QPushButton("Start")
        controls.addWidget(self.start_btn)

        controls.addStretch()

        # game canvas
        self.canvas = TypingCanvas()
        self.canvas.setFixedHeight(180)
        layout.addWidget(self.canvas)

        # stats bar
        stats = QHBoxLayout()
        layout.addLayout(stats)

        self.time_label = QLabel("Time: 0.0s")
        self.wpm_label = QLabel("WPM: 0")
        self.keys_label = QLabel("Keys: 0")
        self.status_label = QLabel("")
        for w in (self.time_label, self.wpm_label, self.keys_label, self.status_label):
            w.setFont(QFont("Meiryo", 12))
            w.setStyleSheet("color: #d6f0ff; padding:6px;")
            stats.addWidget(w)

        stats.addStretch()

        # connections
        self.start_btn.clicked.connect(self.on_start)
        self.sentence_combo.currentIndexChanged.connect(self.on_sentence_change)
        self.canvas.on_complete = self.on_complete

        # timer for UI updates (WPM etc)
        self.ui_timer = QTimer()
        self.ui_timer.setInterval(200)
        self.ui_timer.timeout.connect(self.update_stats)

        # initial state
        self.reset_game()

        # style
        self.setStyleSheet("""
            QMainWindow { background-color: #071122; }
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1f6feb, stop:1 #1556b0);
                          color: white; padding:8px 14px; border-radius:8px; font-weight:600;}
            QPushButton:pressed { background: #103f7a; }
            QComboBox { padding:6px; border-radius:6px; background: #0b2230; color: #dff; }
        """)
        # focus canvas to receive keys when clicked
        self.canvas.setFocus()

    def reset_game(self):
        self.canvas.set_target(self.sentence_combo.currentText())
        self.time_label.setText("Time: 0.0s")
        self.wpm_label.setText("WPM: 0")
        self.keys_label.setText("Keys: 0")
        self.status_label.setText("")
        self.ui_timer.stop()

    def on_start(self):
        # set the selected sentence and focus
        self.canvas.set_target(self.sentence_combo.currentText())
        self.canvas.setFocus()
        self.canvas.start_time = None
        self.canvas.key_count = 0
        self.canvas.parser = RomajiParser(TABLE_PATH)
        self.canvas.typed_kana = ""
        self.canvas.update()
        self.ui_timer.start()

    def on_sentence_change(self, idx):
        self.canvas.set_target(self.sentence_combo.currentText())

    def update_stats(self):
        if self.canvas.start_time:
            elapsed = time.time() - self.canvas.start_time
        else:
            elapsed = 0.0
        # rough WPM: (correct characters / 5) / minutes; use typed_kana length as characters typed
        chars = len(self.canvas.typed_kana)
        minutes = elapsed / 60 if elapsed > 0 else 1/60
        wpm = int((chars / 5) / minutes) if elapsed > 0 else 0
        self.time_label.setText(f"Time: {elapsed:.1f}s")
        self.wpm_label.setText(f"WPM: {wpm}")
        self.keys_label.setText(f"Keys: {self.canvas.key_count}")

    def on_complete(self, duration, keys):
        self.ui_timer.stop()
        chars = len(self.canvas.typed_kana)
        minutes = duration / 60 if duration > 0 else 1/60
        wpm = int((chars / 5) / minutes)
        accuracy = 100.0  # for now we don't compute per-key mistakes; could be extended
        self.status_label.setText(f"Finished! {wpm} WPM — {accuracy:.1f}%")
        # focus out
        self.canvas.clearFocus()

# -------------------------
# main
# -------------------------
def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
