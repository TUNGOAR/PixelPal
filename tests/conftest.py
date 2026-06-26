import sys
from pathlib import Path

import pytest

# 让 src/ 可被 import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def qapp():
    """Provide a QGuiApplication instance for tests that exercise QPixmap.

    Without a running QGuiApplication, calling QPixmap.fromImage() on
    PyQt6 6.11 / Windows crashes the test process (exit 127). This fixture
    is NOT autouse — only tests that need Qt GUI objects should request it
    explicitly. Pure-Python business-layer tests must remain PyQt-free.
    """
    from PyQt6.QtGui import QGuiApplication

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    yield app
