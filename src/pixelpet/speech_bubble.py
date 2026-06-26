"""头顶气泡：圆角矩形 + 文本，支持流式追加。"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
from PyQt6.QtWidgets import QWidget


_BG = QColor(255, 255, 255, 230)
_BORDER = QColor(80, 80, 80, 200)
_TEXT = QColor(20, 20, 20)
_TAIL_H = 8
_PADDING = 8
_MAX_WIDTH = 240


class SpeechBubble(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._text = ""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.hide()
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def set_text(self, text: str) -> None:
        self._text = text
        self._adjust_size()
        self.show()

    def append_token(self, token: str) -> None:
        self._text += token
        self._adjust_size()
        self.update()

    def hide_after(self, ms: int) -> None:
        self._hide_timer.start(ms)

    def show_at(self, parent_pos: QPoint, parent_size: QSize) -> None:
        x = parent_pos.x() + (parent_size.width() - self.width()) // 2
        y = parent_pos.y() - self.height() + _TAIL_H
        self.move(max(0, x), max(0, y))
        self.show()
        self.raise_()

    def _adjust_size(self) -> None:
        font = QFont()
        font.setPointSize(10)
        fm = QFontMetrics(font)
        rect = fm.boundingRect(
            QRect(0, 0, _MAX_WIDTH - 2 * _PADDING, 1000),
            Qt.TextFlag.TextWordWrap,
            self._text,
        )
        w = min(_MAX_WIDTH, rect.width() + 2 * _PADDING)
        h = rect.height() + 2 * _PADDING
        self.resize(w, h + _TAIL_H)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 气泡主体
        rect = QRect(0, 0, self.width(), self.height() - _TAIL_H)
        p.setBrush(_BG)
        p.setPen(QPen(_BORDER, 1))
        p.drawRoundedRect(rect, 8, 8)
        # 尾巴
        cx = self.width() // 2
        p.drawPolygon(
            [QPoint(cx - 6, rect.bottom()), QPoint(cx + 6, rect.bottom()), QPoint(cx, rect.bottom() + _TAIL_H)]
        )
        # 文本
        p.setPen(_TEXT)
        p.setFont(QFont("Microsoft YaHei", 10))
        p.drawText(rect.adjusted(_PADDING, _PADDING, -_PADDING, -_PADDING),
                   Qt.TextFlag.TextWordWrap, self._text)
