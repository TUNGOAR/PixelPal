# src/pixelpet/pet_window.py
"""主窗口：透明无边框 + 拖拽 + 点击。"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import pyqtSignal


class PetWindow(QWidget):
    clicked = pyqtSignal()
    moved = pyqtSignal(QPoint)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._press_pos: QPoint | None = None
        self._press_time = 0
        self._drag_offset: QPoint | None = None

    def paintEvent(self, _event) -> None:
        # 透明背景，不需要绘制主体；子类 PetWidget 自行渲染
        pass

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._press_time = self._now_ms()
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            self.moved.emit(self.pos())

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
            elapsed = self._now_ms() - self._press_time
            moved_dist = (event.globalPosition().toPoint() - self._press_pos).manhattanLength()
            if elapsed < 200 and moved_dist < 5:
                self.clicked.emit()
        self._press_pos = None
        self._drag_offset = None

    @staticmethod
    def _now_ms() -> int:
        from time import monotonic_ns
        return monotonic_ns() // 1_000_000

    def move_to(self, pos: QPoint) -> None:
        self.move(pos)
        self.moved.emit(self.pos())

    def toggle_passthrough(self, enabled: bool) -> None:
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowTransparentForInput
        else:
            flags &= ~Qt.WindowType.WindowTransparentForInput
        self.hide()
        self.setWindowFlags(flags)
        self.show()
