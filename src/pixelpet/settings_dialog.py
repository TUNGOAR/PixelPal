# src/pixelpet/settings_dialog.py
"""设置面板：三 Tab。"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QHBoxLayout, QFileDialog,
    QComboBox, QDialogButtonBox, QPlainTextEdit, QMessageBox,
)

from pixelpet.i18n import SETTINGS_TITLE, SETTINGS_TAB_GENERAL, SETTINGS_TAB_BEHAVIOR, SETTINGS_TAB_AI
from pixelpet.config_manager import ConfigManager


class SettingsDialog(QDialog):
    applied = pyqtSignal(dict)

    def __init__(self, config: ConfigManager, auto_start=None, exe_path: Path | None = None, is_frozen: bool = True, parent=None):
        super().__init__(parent)
        self.setWindowTitle(SETTINGS_TITLE)
        self.config = config
        self.auto_start = auto_start
        self.exe_path = exe_path
        self.is_frozen = is_frozen

        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), SETTINGS_TAB_GENERAL)
        tabs.addTab(self._build_behavior_tab(), SETTINGS_TAB_BEHAVIOR)
        tabs.addTab(self._build_ai_tab(), SETTINGS_TAB_AI)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    # ----- General -----
    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.chk_auto_start = QCheckBox()
        self.chk_auto_start.setChecked(self.config.get("startup", "auto_start", False))
        form.addRow("开机自启", self.chk_auto_start)

        self.ed_sprite_dir = QLineEdit(self.config.get("pet", "sprite_dir", "assets/pet"))
        btn_browse = QPushButton("浏览…")
        btn_browse.clicked.connect(self._browse_sprite_dir)
        h = QHBoxLayout()
        h.addWidget(self.ed_sprite_dir, 1)
        h.addWidget(btn_browse)
        form.addRow("主题目录", self._wrap(h))
        return w

    def _wrap(self, layout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    def _browse_sprite_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "选择主题目录", self.ed_sprite_dir.text())
        if d:
            self.ed_sprite_dir.setText(d)

    # ----- Behavior -----
    def _build_behavior_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.spin_size = QDoubleSpinBox()
        self.spin_size.setRange(0.25, 4.0)
        self.spin_size.setSingleStep(0.25)
        self.spin_size.setValue(float(self.config.get("pet", "size", 1.0)))
        form.addRow("尺寸倍数", self.spin_size)

        self.spin_speed = QSpinBox()
        self.spin_speed.setRange(10, 400)
        self.spin_speed.setValue(int(self.config.get("pet", "walk_speed", 60)))
        form.addRow("行走速度 (px/秒)", self.spin_speed)

        self.spin_idle_min = QSpinBox()
        self.spin_idle_min.setRange(1, 600)
        self.spin_idle_min.setValue(int(self.config.get("pet", "idle_to_walk_min", 8)))
        form.addRow("待机→行走最小 (秒)", self.spin_idle_min)

        self.spin_idle_max = QSpinBox()
        self.spin_idle_max.setRange(1, 600)
        self.spin_idle_max.setValue(int(self.config.get("pet", "idle_to_walk_max", 25)))
        form.addRow("待机→行走最大 (秒)", self.spin_idle_max)

        self.spin_walk_min = QSpinBox()
        self.spin_walk_min.setRange(1, 120)
        self.spin_walk_min.setValue(int(self.config.get("pet", "walk_duration_min", 3)))
        form.addRow("行走最短 (秒)", self.spin_walk_min)

        self.spin_walk_max = QSpinBox()
        self.spin_walk_max.setRange(1, 120)
        self.spin_walk_max.setValue(int(self.config.get("pet", "walk_duration_max", 8)))
        form.addRow("行走最长 (秒)", self.spin_walk_max)

        self.spin_pro_min = QSpinBox()
        self.spin_pro_min.setRange(5, 3600)
        self.spin_pro_min.setValue(int(self.config.get("pet", "proactive_chat_min", 60)))
        form.addRow("搭讪间隔最小 (秒)", self.spin_pro_min)

        self.spin_pro_max = QSpinBox()
        self.spin_pro_max.setRange(5, 3600)
        self.spin_pro_max.setValue(int(self.config.get("pet", "proactive_chat_max", 180)))
        form.addRow("搭讪间隔最大 (秒)", self.spin_pro_max)

        self.spin_mouse_idle = QSpinBox()
        self.spin_mouse_idle.setRange(0, 3600)
        self.spin_mouse_idle.setValue(int(self.config.get("pet", "mouse_idle_threshold", 30)))
        form.addRow("鼠标静止阈值 (秒)", self.spin_mouse_idle)
        return w

    # ----- AI -----
    def _build_ai_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.cmb_provider = QComboBox()
        self.cmb_provider.addItems(["deepseek", "openai", "claude"])
        self.cmb_provider.setCurrentText(self.config.get("ai", "provider", "deepseek"))
        form.addRow("Provider", self.cmb_provider)

        self.ed_api_key = QLineEdit(self.config.get("ai", "api_key", ""))
        self.ed_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API Key", self.ed_api_key)

        self.ed_base_url = QLineEdit(self.config.get("ai", "base_url", "https://api.deepseek.com/v1"))
        form.addRow("Base URL", self.ed_base_url)

        self.ed_model = QLineEdit(self.config.get("ai", "model", "deepseek-chat"))
        form.addRow("Model", self.ed_model)

        self.ed_system = QPlainTextEdit(self.config.get("ai", "system_prompt", ""))
        self.ed_system.setFixedHeight(100)
        form.addRow("System Prompt", self.ed_system)
        return w

    # ----- Apply -----
    def _on_ok(self) -> None:
        # 校验：最小值不能大于最大值
        if self.spin_idle_min.value() > self.spin_idle_max.value():
            QMessageBox.warning(self, SETTINGS_TITLE, "最小值不能大于最大值（待机→行走）")
            return
        if self.spin_walk_min.value() > self.spin_walk_max.value():
            QMessageBox.warning(self, SETTINGS_TITLE, "最小值不能大于最大值（行走时长）")
            return
        if self.spin_pro_min.value() > self.spin_pro_max.value():
            QMessageBox.warning(self, SETTINGS_TITLE, "最小值不能大于最大值（搭讪间隔）")
            return
        new_cfg = {
            "startup": {"auto_start": self.chk_auto_start.isChecked()},
            "pet": {
                "size": self.spin_size.value(),
                "walk_speed": self.spin_speed.value(),
                "idle_to_walk_min": self.spin_idle_min.value(),
                "idle_to_walk_max": self.spin_idle_max.value(),
                "walk_duration_min": self.spin_walk_min.value(),
                "walk_duration_max": self.spin_walk_max.value(),
                "proactive_chat_min": self.spin_pro_min.value(),
                "proactive_chat_max": self.spin_pro_max.value(),
                "mouse_idle_threshold": self.spin_mouse_idle.value(),
                "sprite_dir": self.ed_sprite_dir.text(),
            },
            "ai": {
                "provider": self.cmb_provider.currentText(),
                "api_key": self.ed_api_key.text(),
                "base_url": self.ed_base_url.text(),
                "model": self.ed_model.text(),
                "system_prompt": self.ed_system.toPlainText(),
            },
        }
        # 落盘
        for section, kv in new_cfg.items():
            for k, v in kv.items():
                self.config.set(section, k, v)
        # 开机自启
        if self.auto_start is not None and self.exe_path is not None:
            if new_cfg["startup"]["auto_start"]:
                if not self.is_frozen:
                    # 开发模式下 sys.executable 是 python.exe，写入注册表后无法正常运行
                    QMessageBox.warning(
                        self, SETTINGS_TITLE,
                        "开发模式下不支持开机自启，请先打包后再启用。"
                    )
                    new_cfg["startup"]["auto_start"] = False
                    self.config.set("startup", "auto_start", False)
                    self.chk_auto_start.setChecked(False)
                else:
                    self.auto_start.enable(self.exe_path)
            else:
                self.auto_start.disable()
        self.applied.emit(new_cfg)
        self.accept()