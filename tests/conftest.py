import sys
from pathlib import Path

import pytest

# 让 src/ 可被 import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(autouse=True)
def _qapp_for_qpixmap():
    """Ensure a QGuiApplication exists so QPixmap.fromImage works on Windows.

    Without a running QGuiApplication, calling QPixmap.fromImage() on
    PyQt6 6.11 / Windows crashes the test process (exit 127). pytest-qt
    exposes a `qapp` fixture but it is not autouse; this wrapper makes it
    available to every test that needs QPixmap without requiring each test
    to declare the fixture explicitly.
    """
    from PyQt6.QtGui import QGuiApplication

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    yield app
