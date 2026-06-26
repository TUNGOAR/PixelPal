"""Windows 开机自启：通过 HKCU 注册表 Run 项。"""
from __future__ import annotations

import sys
from pathlib import Path

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


class AutoStart:
    def __init__(self, app_name: str = "PixelPet"):
        self.app_name = app_name

    def _key(self):
        if sys.platform != "win32":
            return None
        import winreg
        return winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )

    def is_enabled(self) -> bool:
        key = self._key()
        if key is None:
            return False
        import winreg
        try:
            winreg.QueryValueEx(key, self.app_name)
            return True
        except FileNotFoundError:
            return False

    def enable(self, executable_path: Path) -> None:
        key = self._key()
        if key is None:
            raise RuntimeError("AutoStart 仅支持 Windows")
        import winreg
        cmd = f'"{executable_path}" --minimized'
        winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, cmd)

    def disable(self) -> None:
        key = self._key()
        if key is None:
            return
        import winreg
        try:
            winreg.DeleteValue(key, self.app_name)
        except FileNotFoundError:
            pass
