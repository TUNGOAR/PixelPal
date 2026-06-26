# src/pixelpet/main.py
"""启动入口。"""
from __future__ import annotations

import sys


def main() -> int:
    minimized = "--minimized" in sys.argv
    from pixelpet.app import App
    return App(minimized=minimized).run()


if __name__ == "__main__":
    sys.exit(main())
