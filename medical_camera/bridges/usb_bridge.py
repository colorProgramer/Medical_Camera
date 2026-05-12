from __future__ import annotations

import ctypes
from pathlib import Path
from .usb_loader import load_usb_dll

class UsbBridge:
    def __init__(self, dll_path: str | Path | None = None) -> None:
        try:
            self._dll = load_usb_dll(dll_path)
            self._available = True
        except Exception:
            self._dll = None
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def get_device_count(self) -> int:
        if not self._dll:
            return 0
        return self._dll.mc_usb_get_device_count()

    def get_device_name(self, index: int) -> str:
        if not self._dll:
            return f"USB Camera {index} (Bridge Unavailable)"
        
        capacity = 256
        buffer = ctypes.create_unicode_buffer(capacity)
        status = self._dll.mc_usb_get_device_name(index, buffer, capacity)
        if status == 0:
            return buffer.value
        return f"USB Camera {index}"
