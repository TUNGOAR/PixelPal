"""YAML 配置管理：缺字段回退默认，写入立即落盘。"""
from pathlib import Path
from typing import Any
import copy

import yaml


_DEFAULTS: dict[str, dict[str, Any]] = {
    "pet": {
        "size": 1.0,
        "walk_speed": 60,
        "idle_to_walk_min": 8,
        "idle_to_walk_max": 25,
        "walk_duration_min": 3,
        "walk_duration_max": 8,
        "proactive_chat_min": 60,
        "proactive_chat_max": 180,
        "mouse_idle_threshold": 30,
        "sprite_dir": "assets/pet",
    },
    "animation": {"fps": 8},
    "window": {"always_on_top": True, "mouse_passthrough": False},
    "ai": {
        "provider": "deepseek",
        "api_key": "",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "system_prompt": (
            "你是 PixelPet，一只住在用户桌面的像素风宠物。"
            "性格：活泼、爱吐槽、偶尔撒娇。说话简短（≤30 字），像微信气泡。"
        ),
    },
    "startup": {"auto_start": False},
}


class ConfigManager:
    def __init__(self, path: Path):
        self.path = Path(path)
        if not self.path.exists():
            self._save(_DEFAULTS)
        self._data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return copy.deepcopy(_DEFAULTS)
        on_disk = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        merged = copy.deepcopy(_DEFAULTS)
        for section, kv in on_disk.items():
            merged.setdefault(section, {})
            for k, v in kv.items():
                merged[section][k] = v
        return merged

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def get(self, section: str, key: str, default: Any = None) -> Any:
        return self._data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        self._data.setdefault(section, {})[key] = value
        self._save(self._data)

    def reload(self) -> None:
        self._data = self._load()

    def all(self) -> dict:
        return copy.deepcopy(self._data)
