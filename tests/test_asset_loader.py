from pathlib import Path
from pixelpet.asset_loader import AssetLoader

FIXTURES = Path(__file__).parent / "fixtures" / "asset_pet"

def test_loads_idle_frames_in_order(qapp):
    loader = AssetLoader(FIXTURES)
    frames = loader.frames_for("idle")
    assert len(frames) == 2
    # 帧按文件名数字升序
    assert frames[0].width() == 16
    assert frames[1].width() == 16

def test_missing_state_returns_placeholder(qapp):
    loader = AssetLoader(FIXTURES)
    frames = loader.frames_for("walk")  # 不存在的状态
    assert len(frames) == 1
    assert frames[0].width() == 8  # 占位图

def test_has_state(qapp):
    loader = AssetLoader(FIXTURES)
    assert loader.has_state("idle") is True
    assert loader.has_state("walk") is False
