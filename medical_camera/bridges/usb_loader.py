from __future__ import annotations

import ctypes
from ctypes import c_int, c_wchar_p
from pathlib import Path
from medical_camera.utils.path import get_resource_path

class UsbBridgeLoadError(RuntimeError):
    """Raised when the native USB bridge cannot be loaded."""

def default_usb_dll_path() -> Path:
    candidates = [
        get_resource_path("native/bin/medical_camera_usb.dll"),
        get_resource_path("medical_camera_usb.dll"),
        Path("medical_camera_usb.dll"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]

def configure_usb_api(dll: ctypes.WinDLL) -> None:
    dll.mc_usb_get_device_count.restype = c_int
    dll.mc_usb_get_device_name.argtypes = [c_int, c_wchar_p, c_int]
    dll.mc_usb_get_device_name.restype = c_int

def load_usb_dll(dll_path: str | Path | None = None) -> ctypes.WinDLL:
    resolved_path = Path(dll_path or default_usb_dll_path()).resolve()
    if not resolved_path.exists():
        raise UsbBridgeLoadError(f"Native USB bridge not found: {resolved_path}")

    try:
        dll = ctypes.WinDLL(str(resolved_path))
    except OSError as exc:
        raise UsbBridgeLoadError(f"Failed to load USB bridge: {resolved_path}") from exc

    configure_usb_api(dll)
    return dll
