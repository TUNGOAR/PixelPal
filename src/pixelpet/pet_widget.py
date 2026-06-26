"""宠物精灵渲染：按 fps 切帧。"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QWidget

from pixelpet.asset_loader import AssetLoader
from pixelpet.state_machine import State


class PetWidget(QWidget):
    def __init__(self, fps: int = 8, parent: QWidget | None = None):
        super().__init__(parent)
        self._loader: AssetLoader | None = None
        self._frames: list = []
        self._frame_idx = 0
        self._state: State = State.IDLE
        self._direction = "down"
        self._size_scale = 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(int(1000 / max(fps, 1)))

    def set_loader(self, loader: AssetLoader) -> None:
        self._loader = loader
        self._reload_frames()

    def set_fps(self, fps: int) -> None:
        self._timer.setInterval(int(1000 / max(fps, 1)))

    def set_state(self, state: State) -> None:
        if self._state == state:
            return
        self._state = state
        self._reload_frames()

    def set_direction(self, direction: str) -> None:
        if self._direction == direction:
            return
        self._direction = direction
        self._reload_frames()

    def set_size_scale(self, scale: float) -> None:
        self._size_scale = scale
        self._reload_frames()
        self._adjust_widget_size()
        self.update()

    def current_size(self):
        return self.size()

    def _reload_frames(self) -> None:
        if self._loader is None:
            self._frames = []
            return
        direction = self._direction if self._state == State.WALK else None
        self._frames = self._loader.frames_for(self._state.value, direction)
        self._frame_idx = 0
        self._adjust_widget_size()
        self.update()

    def _adjust_widget_size(self) -> None:
        if not self._frames:
            return
        base = self._frames[0].size()
        w = max(1, int(base.width() * self._size_scale))
        h = max(1, int(base.height() * self._size_scale))
        self.setFixedSize(w, h)

    def _advance(self) -> None:
        if not self._frames:
            return
        self._frame_idx = (self._frame_idx + 1) % len(self._frames)
        self.update()

    def paintEvent(self, _event) -> None:
        if not self._frames:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        target = self.rect()
        painter.drawPixmap(target, self._frames[self._frame_idx])
