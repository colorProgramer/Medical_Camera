import sys
import os
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        # We are in dev mode, base_path is project root
        # This file is at medical_camera/utils/path.py
        base_path = Path(__file__).resolve().parent.parent.parent

    return base_path / relative_path
