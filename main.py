#!/usr/bin/env python3
"""
yt-dlp GUI - Графический интерфейс для yt-dlp
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """Точка входа приложения"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
