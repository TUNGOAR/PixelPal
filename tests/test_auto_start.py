import sys
from pathlib import Path
import pytest

from pixelpet.auto_start import AutoStart


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
def test_enable_disable_roundtrip(tmp_path):
    fake_exe = tmp_path / "PixelPet.exe"
    fake_exe.write_text("fake")
    a = AutoStart(app_name="PixelPetTest")
    try:
        assert a.is_enabled() is False
        a.enable(fake_exe)
        assert a.is_enabled() is True
    finally:
        a.disable()
    assert a.is_enabled() is False
