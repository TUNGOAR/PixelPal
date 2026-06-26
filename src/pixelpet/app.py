# src/pixelpet/app.py
"""应用组装与主事件循环。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QImage, QPainter, QColor, QCursor
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from pixelpet.asset_loader import AssetLoader
from pixelpet.state_machine import StateMachine, State, Event
from pixelpet.behavior_scheduler import BehaviorScheduler
from pixelpet.chat_service import ChatService
from pixelpet.config_manager import ConfigManager
from pixelpet.llm_client import LLMClient
from pixelpet.llm_client.deepseek import DeepSeekClient
from pixelpet.auto_start import AutoStart
from pixelpet.pet_window import PetWindow
from pixelpet.pet_widget import PetWidget
from pixelpet.speech_bubble import SpeechBubble
from pixelpet.tray_icon import TrayIcon
from pixelpet.settings_dialog import SettingsDialog


def _make_default_icon() -> QIcon:
    pm = QPixmap(32, 32)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(120, 200, 255))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(4, 4, 24, 24, 4, 4)
    p.setBrush(QColor(20, 20, 20))
    p.drawEllipse(11, 12, 4, 4)
    p.drawEllipse(17, 12, 4, 4)
    p.end()
    return QIcon(pm)


def _build_llm(cfg: ConfigManager) -> LLMClient:
    provider = cfg.get("ai", "provider", "deepseek")
    if provider == "deepseek":
        return DeepSeekClient(
            api_key=cfg.get("ai", "api_key", ""),
            base_url=cfg.get("ai", "base_url", "https://api.deepseek.com/v1"),
            model=cfg.get("ai", "model", "deepseek-chat"),
        )
    raise RuntimeError(f"未实现的 provider: {provider}")


class App:
    def __init__(self, minimized: bool = False):
        self.qt = QApplication.instance() or QApplication(sys.argv)
        self.qt.setQuitOnLastWindowClosed(False)

        # 数据层
        cfg_path = Path.home() / "AppData" / "Roaming" / "PixelPet" / "config.yaml"
        example = Path(__file__).parent.parent.parent / "config.example.yaml"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        if not cfg_path.exists() and example.exists():
            cfg_path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        self.config = ConfigManager(cfg_path)

        self.state = StateMachine()
        self.behavior = BehaviorScheduler(self.state, self.config)
        self.llm = _build_llm(self.config)
        self.chat = ChatService(self.llm, self.config.get("ai", "system_prompt", ""))

        # 资源
        sprite_dir = Path(self.config.get("pet", "sprite_dir", "assets/pet"))
        if not sprite_dir.is_absolute():
            sprite_dir = Path(__file__).parent.parent.parent / sprite_dir
        self.loader = AssetLoader(sprite_dir)

        # UI
        self.window = PetWindow()
        self.widget = PetWidget(fps=int(self.config.get("animation", "fps", 8)))
        self.widget.set_loader(self.loader)
        self.widget.set_size_scale(float(self.config.get("pet", "size", 1.0)))
        self.widget.setParent(self.window)
        self.widget.show()
        self.window.resize(self.widget.size())

        self.bubble = SpeechBubble()
        self.tray = TrayIcon(_make_default_icon())
        self.tray.show()
        self.auto_start = AutoStart()

        self.settings_dialog: SettingsDialog | None = None

        # 信号连接
        self.state.on_change.append(self._on_state_change)
        self.window.clicked.connect(self._on_pet_clicked)
        self.tray.request_hide.connect(self.window.hide)
        self.tray.request_show.connect(self.window.show)
        self.tray.request_settings.connect(self._open_settings)
        self.tray.request_quit.connect(self._quit)

        # 启动位置：主屏右下角
        screen = self.qt.primaryScreen().availableGeometry()
        self.window.move(screen.right() - self.widget.width() - 50,
                         screen.bottom() - self.widget.height() - 50)
        if not minimized:
            self.window.show()

        # 行为调度 timer（每秒 tick）
        self._tick = QTimer()
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self._on_tick)
        self._tick.start()
        import time
        self._t0 = time.monotonic()

        # 鼠标跟踪
        self.qt.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

    def _on_state_change(self, old: State, new: State) -> None:
        self.widget.set_state(new)

    def _on_pet_clicked(self) -> None:
        # CLICK 短反馈 + 弹出输入
        self.state.transition(Event.CLICK)
        self.bubble.set_text("…")
        self.bubble.show_at(self.window.pos(), self.widget.size())
        # 用 input() 在控制台不便；改为弹出 QInputDialog
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self.window, "和宠物说", "你说：")
        if ok and text:
            asyncio.create_task(self._do_chat(text))
        else:
            self.bubble.hide()
            self.state.transition(Event.CANCEL)

    async def _do_chat(self, text: str) -> None:
        self.bubble.set_text("")
        self.state.transition(Event.SUBMIT)
        self.state.transition(Event.TOKEN_START)

        def on_token(t: str):
            self.bubble.append_token(t)

        def on_done():
            self.state.transition(Event.TOKEN_END)
            self.bubble.hide_after(8000)

        def on_error(e: Exception):
            self.bubble.set_text(f"（出错了：{e}）")
            self.bubble.hide_after(5000)
            self.state.transition(Event.CANCEL)

        await self.chat.send(text, on_token, on_done, on_error)

    def _on_tick(self) -> None:
        import time
        now = time.monotonic() - self._t0
        # 喂鼠标位置
        pos = QCursor.pos()
        self.behavior.update_mouse_position(pos.x(), pos.y(), now)
        # 调度
        actions = self.behavior.tick(now)
        if "walk" in actions:
            self._start_walk()
        if "proactive_chat" in actions:
            self._proactive_chat()

    def _start_walk(self) -> None:
        screen = self.qt.primaryScreen().availableGeometry()
        target_x = self.window.x() + (50 if (self._now_ns() % 2) else -50)
        target_y = self.window.y() + (30 if (self._now_ns() % 3) else -30)
        target_x = max(screen.left(), min(screen.right() - self.widget.width(), target_x))
        target_y = max(screen.top(), min(screen.bottom() - self.widget.height(), target_y))

        speed = float(self.config.get("pet", "walk_speed", 60))
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        self._anim = QPropertyAnimation(self.window, b"pos")
        self._anim.setDuration(max(100, int(1000 * 1.0)))
        self._anim.setStartValue(self.window.pos())
        self._anim.setEndValue(QPoint(target_x, target_y))
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.start()
        QTimer.singleShot(1000, lambda: self.state.transition(Event.TICK_WALK))

    def _proactive_chat(self) -> None:
        async def go():
            self.bubble.set_text("")
            self.state.transition(Event.SUBMIT)
            self.state.transition(Event.TOKEN_START)

            def on_token(t):
                self.bubble.append_token(t)

            def on_done():
                self.state.transition(Event.TOKEN_END)
                self.bubble.hide_after(8000)

            def on_error(e):
                self.bubble.hide()
                self.state.transition(Event.CANCEL)

            await self.chat.send(
                "现在请主动找主人说一句话，要求简短自然，符合当前时间与场景。",
                on_token, on_done, on_error,
            )

        asyncio.create_task(go())

    def _open_settings(self) -> None:
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(
                self.config, auto_start=self.auto_start,
                exe_path=Path(sys.executable),
            )
            self.settings_dialog.applied.connect(self._on_settings_applied)
        self.settings_dialog.show()
        self.settings_dialog.raise_()

    def _on_settings_applied(self, _cfg: dict) -> None:
        # 热生效：刷新 widget 参数
        self.widget.set_size_scale(float(self.config.get("pet", "size", 1.0)))
        self.widget.set_fps(int(self.config.get("animation", "fps", 8)))
        # 重建 LLM（API 配置可能变了）
        self.llm = _build_llm(self.config)
        self.chat.llm = self.llm
        self.chat.clear()

    def _quit(self) -> None:
        self.qt.quit()

    @staticmethod
    def _now_ns() -> int:
        from time import monotonic_ns
        return monotonic_ns()

    def run(self) -> int:
        return self.qt.exec()
