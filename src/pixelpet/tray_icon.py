# src/pixelpet/tray_icon.py
"""系统托盘菜单。"""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

from pixelpet.i18n import (
    TRAY_SHOW, TRAY_HIDE, TRAY_PAUSE_PROACTIVE, TRAY_RESUME_PROACTIVE,
    TRAY_PROACTIVE_NOW, TRAY_SETTINGS, TRAY_QUIT,
)


class TrayIcon(QSystemTrayIcon):
    request_show = pyqtSignal()
    request_hide = pyqtSignal()
    request_proactive_now = pyqtSignal()
    request_toggle_proactive = pyqtSignal(bool)  # True = paused
    request_settings = pyqtSignal()
    request_quit = pyqtSignal()

    def __init__(self, icon: QIcon, parent=None):
        super().__init__(icon, parent)
        self._proactive_paused = False
        self._build_menu()

    def _build_menu(self) -> None:
        menu = QMenu()

        self._act_show = QAction(TRAY_SHOW, menu)
        self._act_show.triggered.connect(self.request_show.emit)
        menu.addAction(self._act_show)

        self._act_hide = QAction(TRAY_HIDE, menu)
        self._act_hide.triggered.connect(self.request_hide.emit)
        menu.addAction(self._act_hide)

        menu.addSeparator()

        self._act_pause = QAction(TRAY_PAUSE_PROACTIVE, menu)
        self._act_pause.setCheckable(True)
        self._act_pause.toggled.connect(self._on_pause_toggled)
        menu.addAction(self._act_pause)

        self._act_now = QAction(TRAY_PROACTIVE_NOW, menu)
        self._act_now.triggered.connect(self.request_proactive_now.emit)
        menu.addAction(self._act_now)

        menu.addSeparator()

        self._act_settings = QAction(TRAY_SETTINGS, menu)
        self._act_settings.triggered.connect(self.request_settings.emit)
        menu.addAction(self._act_settings)

        self._act_quit = QAction(TRAY_QUIT, menu)
        self._act_quit.triggered.connect(self.request_quit.emit)
        menu.addAction(self._act_quit)

        self.setContextMenu(menu)

    def _on_pause_toggled(self, checked: bool) -> None:
        self._proactive_paused = checked
        self._act_pause.setText(
            TRAY_RESUME_PROACTIVE if checked else TRAY_PAUSE_PROACTIVE
        )
        self.request_toggle_proactive.emit(checked)

    def is_proactive_paused(self) -> bool:
        return self._proactive_paused
