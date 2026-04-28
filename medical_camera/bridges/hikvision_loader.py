from __future__ import annotations

import ctypes
import os
from ctypes import POINTER, c_float, c_int, c_int64, c_uint8, c_uint32, c_void_p
from pathlib import Path

from .hikvision_types import (
    McHikDeviceInfo,
    McHikFrameInfo,
    McHikSnapshot,
)


class HikvisionBridgeLoadError(RuntimeError):
    """Raised when the native Hikvision bridge cannot be loaded."""


def default_hikvision_dll_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    candidates = [
        project_root / "native" / "build_runtime" / "Release" / "medical_camera_hikvision_capi.dll",
        project_root / "native" / "build" / "Release" / "medical_camera_hikvision_capi.dll",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def register_hikvision_dll_directories(dll_path: Path) -> list[object]:
    handles: list[object] = []
    candidate_dirs = [
        dll_path.parent,
        Path(r"C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64"),
        Path(r"G:\MVS\Development\Bin\win64"),
    ]
    for directory in candidate_dirs:
        if directory.exists():
            handles.append(os.add_dll_directory(str(directory)))
    return handles


def configure_hikvision_api(dll: ctypes.WinDLL) -> None:
    dll.mc_hik_initialize.restype = c_int
    dll.mc_hik_finalize.restype = c_int
    dll.mc_hik_create_camera.restype = c_void_p

    dll.mc_hik_destroy_camera.argtypes = [c_void_p]

    dll.mc_hik_enumerate_devices.argtypes = [
        c_uint32,
        POINTER(McHikDeviceInfo),
        c_uint32,
        POINTER(c_uint32),
    ]
    dll.mc_hik_enumerate_devices.restype = c_int

    dll.mc_hik_open_by_index.argtypes = [c_void_p, c_uint32, c_uint32]
    dll.mc_hik_open_by_index.restype = c_int

    dll.mc_hik_close.argtypes = [c_void_p]
    dll.mc_hik_close.restype = c_int

    dll.mc_hik_is_connected.argtypes = [c_void_p]
    dll.mc_hik_is_connected.restype = c_int

    dll.mc_hik_query_snapshot.argtypes = [c_void_p, POINTER(McHikSnapshot)]
    dll.mc_hik_query_snapshot.restype = c_int

    dll.mc_hik_set_exposure_auto.argtypes = [c_void_p, c_int]
    dll.mc_hik_set_exposure_auto.restype = c_int

    dll.mc_hik_set_exposure_time.argtypes = [c_void_p, c_float]
    dll.mc_hik_set_exposure_time.restype = c_int

    dll.mc_hik_get_exposure_time.argtypes = [c_void_p, POINTER(c_float)]
    dll.mc_hik_get_exposure_time.restype = c_int

    dll.mc_hik_set_gain_auto.argtypes = [c_void_p, c_int]
    dll.mc_hik_set_gain_auto.restype = c_int

    dll.mc_hik_set_gain.argtypes = [c_void_p, c_float]
    dll.mc_hik_set_gain.restype = c_int

    dll.mc_hik_get_gain.argtypes = [c_void_p, POINTER(c_float)]
    dll.mc_hik_get_gain.restype = c_int

    dll.mc_hik_set_white_balance_auto.argtypes = [c_void_p, c_int]
    dll.mc_hik_set_white_balance_auto.restype = c_int

    dll.mc_hik_set_balance_ratio_red.argtypes = [c_void_p, c_int64]
    dll.mc_hik_set_balance_ratio_red.restype = c_int

    dll.mc_hik_set_balance_ratio_green.argtypes = [c_void_p, c_int64]
    dll.mc_hik_set_balance_ratio_green.restype = c_int

    dll.mc_hik_set_balance_ratio_blue.argtypes = [c_void_p, c_int64]
    dll.mc_hik_set_balance_ratio_blue.restype = c_int

    dll.mc_hik_start_grabbing.argtypes = [c_void_p]
    dll.mc_hik_start_grabbing.restype = c_int

    dll.mc_hik_stop_grabbing.argtypes = [c_void_p]
    dll.mc_hik_stop_grabbing.restype = c_int

    dll.mc_hik_get_frame_info.argtypes = [c_void_p, c_uint32, POINTER(McHikFrameInfo)]
    dll.mc_hik_get_frame_info.restype = c_int

    dll.mc_hik_get_frame_data.argtypes = [c_void_p, c_uint32, POINTER(c_uint8), c_uint32, POINTER(McHikFrameInfo)]
    dll.mc_hik_get_frame_data.restype = c_int

    dll.mc_hik_save_features.argtypes = [c_void_p, ctypes.c_char_p]
    dll.mc_hik_save_features.restype = c_int

    dll.mc_hik_load_features.argtypes = [c_void_p, ctypes.c_char_p]
    dll.mc_hik_load_features.restype = c_int

    dll.mc_hik_error_to_string.argtypes = [c_int]
    dll.mc_hik_error_to_string.restype = ctypes.c_char_p


def load_hikvision_dll(dll_path: str | Path | None = None) -> tuple[ctypes.WinDLL, list[object]]:
    resolved_path = Path(dll_path or default_hikvision_dll_path()).resolve()
    if not resolved_path.exists():
        raise HikvisionBridgeLoadError(f"Native bridge not found: {resolved_path}")

    try:
        handles = register_hikvision_dll_directories(resolved_path)
        dll = ctypes.WinDLL(str(resolved_path))
    except OSError as exc:
        raise HikvisionBridgeLoadError(f"Failed to load Hikvision bridge: {resolved_path}") from exc

    configure_hikvision_api(dll)
    return dll, handles
