# src/game_ui.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QComboBox, QSlider
)
from PySide6.QtGui import QFont, QPainter, QColor, QKeyEvent
from PySide6.QtCore import Qt, QTimer
from src.game_logic import GameState
from typing import List

SENTENCES = [
    "こんにちは", "おはようございます", "ありがとうございます",
    "さようなら", "今日はいい天気ですね", "タイピングゲームを楽しもう",
    "さんま", "あんな", "しんぶん", "ちょっと",
    "きょうはにちようび", "プログラミングを学ぶ",
    "きゃりーぱみゅぱみゅ", "コンピュータ"
]

class TypingCanvas(QFrame):
    """Canvas to display target text and user's progress."""
    def __init__(self, state: GameState, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                           " stop:0 #0f1724, stop:1 #071122);"
                           "border-radius:12px;")
        self.state = state
        self.on_complete = None

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        rect = self.contentsRect()
        margin = 20
        x = margin
        y = rect.height() // 2

        # fonts
        font = QFont("Meiryo", 28)
        buf_font = QFont("Consolas", 14)
        p.setFont(font)

        typed = self.state.typed_kana
        target = self.state.target
        remaining = target[len(typed):]

        # completed kana (dim)
        p.setPen(QColor(120, 200, 255))
        p.drawText(x, y, typed)

        metrics = p.fontMetrics()
        x += metrics.horizontalAdvance(typed)

        # next active char highlight
        if remaining:
            next_char = remaining[0]
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
            p.setPen(QColor(120, 255, 170))

        # draw roman buffer below
        p.setFont(buf_font)
        p.setPen(QColor(200,200,220,200))
        p.drawText(margin, y + 50, "roman buffer: " + self.state.parser.buffer)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Backspace:
            # delete last roman char
            if self.state.parser.buffer:
                self.state.parser.buffer = self.state.parser.buffer[:-1]
            elif self.state.typed_kana:
                self.state.typed_kana = self.state.typed_kana[:-1]
            self.update()
            return

        ch = event.text()
        if not ch:
            return

        if ch.isalpha():
            produced = self.state.feed(ch)
            # completion check
            if len(self.state.typed_kana) >= len(self.state.target):
                if self.on_complete:
                    self.on_complete()
            self.update()

class MainWindow(QMainWindow):
    """Main Window for typing game."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Typing Game")
        self.setMinimumSize(900, 420)

        self.state = GameState(SENTENCES[0])

        # central layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        # header
        header = QLabel("PySide6 Typing — Romaji -> Kana (Realtime)")
        header.setFont(QFont("Meiryo", 18))
        header.setStyleSheet("color: #cfe8ff;")
        layout.addWidget(header, alignment=Qt.AlignCenter)

        # top controls
        controls = QHBoxLayout()
        layout.addLayout(controls)
        self.sentence_combo = QComboBox()
        self.sentence_combo.addItems(SENTENCES)
        controls.addWidget(QLabel("Sentence:"))
        controls.addWidget(self.sentence_combo)
        self.start_btn = QPushButton("Start")
        controls.addWidget(self.start_btn)
        controls.addStretch()

        # canvas
        self.canvas = TypingCanvas(self.state)
        self.canvas.setFixedHeight(180)
        layout.addWidget(self.canvas)

        # stats
        stats = QHBoxLayout()
        layout.addLayout(stats)
        self.time_label = QLabel("Time: 0.0s")
        self.wpm_label = QLabel("WPM: 0")
        self.keys_label = QLabel("Keys: 0")
        self.acc_label = QLabel("Accuracy: 100%")
        for w in (self.time_label, self.wpm_label, self.keys_label, self.acc_label):
            w.setFont(QFont("Meiryo", 12))
            w.setStyleSheet("color: #d6f0ff; padding:6px;")
            stats.addWidget(w)
        stats.addStretch()

        # connections
        self.start_btn.clicked.connect(self.on_start)
        self.sentence_combo.currentIndexChanged.connect(self.on_sentence_change)
        self.canvas.on_complete = self.on_complete

        # timer
        self.ui_timer = QTimer()
        self.ui_timer.setInterval(200)
        self.ui_timer.timeout.connect(self.update_stats)

        self.reset_game()
        self.canvas.setFocus()

    def reset_game(self):
        self.state.reset(self.sentence_combo.currentText())
        self.time_label.setText("Time: 0.0s")
        self.wpm_label.setText("WPM: 0")
        self.keys_label.setText("Keys: 0")
        self.acc_label.setText("Accuracy: 100%")
        self.ui_timer.stop()
        self.canvas.update()

    def on_start(self):
        self.reset_game()
        self.canvas.setFocus()
        self.ui_timer.start()

    def on_sentence_change(self, idx):
        self.reset_game()

    def update_stats(self):
        elapsed = self.state.elapsed_time()
        self.time_label.setText(f"Time: {elapsed:.1f}s")
        self.wpm_label.setText(f"WPM: {self.state.wpm()}")
        self.keys_label.setText(f"Keys: {self.state.key_count}")
        self.acc_label.setText(f"Accuracy: {self.state.accuracy():.1f}%")

    def on_complete(self):
        self.ui_timer.stop()
        self.update_stats()
        self.acc_label.setText(f"Finished! {self.state.wpm()} WPM — {self.state.accuracy():.1f}%")
        self.canvas.clearFocus()
