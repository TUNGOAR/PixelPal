"""加载 PNG 精灵帧，按状态组织。"""
from pathlib import Path

from PIL import Image
from PyQt6.QtGui import QPixmap


_PLACEHOLDER_SIZE = 8
_VALID_STATES = {"idle", "walk", "click", "chat"}
_WALK_DIRECTIONS = {"down", "up", "left", "right"}


def _make_placeholder() -> QPixmap:
    img = Image.new("RGBA", (_PLACEHOLDER_SIZE, _PLACEHOLDER_SIZE), (255, 0, 0, 255))
    return QPixmap.fromImage(_pil_to_qimage(img))


def _pil_to_qimage(img: Image.Image):
    from PyQt6.QtGui import QImage
    img = img.convert("RGBA")
    return QImage(
        img.tobytes("raw", "RGBA"),
        img.width,
        img.height,
        img.width * 4,
        QImage.Format.Format_RGBA8888,
    )


class AssetLoader:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)

    def _state_dir(self, state: str, direction: str | None) -> Path | None:
        if state == "walk":
            if direction not in _WALK_DIRECTIONS:
                return None
            d = self.base_dir / "walk" / direction
            return d if d.is_dir() else None
        if state not in _VALID_STATES:
            return None
        d = self.base_dir / state
        return d if d.is_dir() else None

    def has_state(self, state: str) -> bool:
        d = self.base_dir / state
        return d.is_dir() and any(d.glob("*.png"))

    def frames_for(self, state: str, direction: str | None = None) -> list[QPixmap]:
        d = self._state_dir(state, direction)
        if d is None:
            return [_make_placeholder()]
        files = sorted(d.glob("*.png"), key=lambda p: int(p.stem) if p.stem.isdigit() else 999)
        out = []
        for f in files:
            pil = Image.open(f)
            out.append(QPixmap.fromImage(_pil_to_qimage(pil)))
        return out if out else [_make_placeholder()]
