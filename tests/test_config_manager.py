import pytest
from pathlib import Path
from pixelpet.config_manager import ConfigManager

@pytest.fixture
def cfg_path(tmp_path):
    p = tmp_path / "config.yaml"
    return p

def test_init_creates_file_with_defaults(cfg_path):
    cm = ConfigManager(cfg_path)
    assert cfg_path.exists()
    assert cm.get("pet", "size") == 1.0
    assert cm.get("ai", "provider") == "deepseek"

def test_get_with_default_when_missing(cfg_path):
    cm = ConfigManager(cfg_path)
    assert cm.get("nonexistent", "x", default="fallback") == "fallback"

def test_set_persists_to_disk(cfg_path):
    cm = ConfigManager(cfg_path)
    cm.set("pet", "size", 2.5)
    cm2 = ConfigManager(cfg_path)
    assert cm2.get("pet", "size") == 2.5

def test_partial_config_fills_defaults(tmp_path):
    p = tmp_path / "partial.yaml"
    p.write_text("pet:\n  size: 3.0\n", encoding="utf-8")
    cm = ConfigManager(p)
    assert cm.get("pet", "size") == 3.0
    assert cm.get("ai", "provider") == "deepseek"  # 默认补齐

def test_reload_reads_from_disk(cfg_path):
    cm = ConfigManager(cfg_path)
    cfg_path.write_text("pet:\n  size: 9.0\n", encoding="utf-8")
    cm.reload()
    assert cm.get("pet", "size") == 9.0
