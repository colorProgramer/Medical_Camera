from __future__ import annotations

from ctypes import byref, c_float, c_int64, c_uint8, c_uint32, c_void_p, string_at
from pathlib import Path

from .hikvision_loader import load_hikvision_dll
from .hikvision_types import (
    MV_DEFAULT_DEVICE_MASK,
    MV_GIGE_DEVICE,
    MV_USB_DEVICE,
    McHikDeviceInfo,
    McHikFrameInfo,
    McHikSnapshot,
)


def _decode_text(raw: bytes) -> str:
    return raw.decode(errors="ignore").rstrip("\x00")


class HikvisionBridge:
    def __init__(self, dll_path: str | Path | None = None) -> None:
        self._dll, self._dll_dirs = load_hikvision_dll(dll_path)
        self._camera = c_void_p()

    def initialize(self) -> int:
        return self._dll.mc_hik_initialize()

    def finalize(self) -> int:
        return self._dll.mc_hik_finalize()

    def create_camera(self) -> None:
        self._camera = c_void_p(self._dll.mc_hik_create_camera())

    def destroy_camera(self) -> None:
        if self._camera:
            self._dll.mc_hik_destroy_camera(self._camera)
            self._camera = c_void_p()

    def enumerate_devices(self, transport_mask: int = MV_DEFAULT_DEVICE_MASK) -> tuple[int, list[dict[str, object]]]:
        out_count = c_uint32(0)
        status = self._dll.mc_hik_enumerate_devices(transport_mask, None, 0, byref(out_count))
        if status != 0 or out_count.value == 0:
            return status, []

        buffer = (McHikDeviceInfo * out_count.value)()
        status = self._dll.mc_hik_enumerate_devices(transport_mask, buffer, out_count.value, byref(out_count))
        devices = [
            {
                "index": item.index,
                "transport_layer_type": item.transport_layer_type,
                "vendor_name": _decode_text(item.vendor_name),
                "model_name": _decode_text(item.model_name),
                "serial_number": _decode_text(item.serial_number),
                "user_defined_name": _decode_text(item.user_defined_name),
                "ip_address": _decode_text(item.ip_address),
            }
            for item in buffer[: out_count.value]
        ]
        return status, devices

    def open_by_index(self, device_index: int, transport_mask: int = MV_DEFAULT_DEVICE_MASK) -> int:
        return self._dll.mc_hik_open_by_index(self._camera, device_index, transport_mask)

    def close(self) -> int:
        return self._dll.mc_hik_close(self._camera)

    def is_connected(self) -> bool:
        return bool(self._dll.mc_hik_is_connected(self._camera))

    def query_snapshot(self) -> tuple[int, McHikSnapshot]:
        snapshot = McHikSnapshot()
        status = self._dll.mc_hik_query_snapshot(self._camera, byref(snapshot))
        return status, snapshot

    def set_exposure_auto(self, enabled: bool) -> int:
        return self._dll.mc_hik_set_exposure_auto(self._camera, int(enabled))

    def set_exposure_time(self, value: float) -> int:
        return self._dll.mc_hik_set_exposure_time(self._camera, c_float(value))

    def get_exposure_time(self) -> tuple[int, float]:
        value = c_float(0.0)
        status = self._dll.mc_hik_get_exposure_time(self._camera, byref(value))
        return status, value.value

    def set_gain_auto(self, enabled: bool) -> int:
        return self._dll.mc_hik_set_gain_auto(self._camera, int(enabled))

    def set_gain(self, value: float) -> int:
        return self._dll.mc_hik_set_gain(self._camera, c_float(value))

    def get_gain(self) -> tuple[int, float]:
        value = c_float(0.0)
        status = self._dll.mc_hik_get_gain(self._camera, byref(value))
        return status, value.value

    def set_white_balance_auto(self, enabled: bool) -> int:
        return self._dll.mc_hik_set_white_balance_auto(self._camera, int(enabled))

    def set_balance_ratio_red(self, value: int) -> int:
        return self._dll.mc_hik_set_balance_ratio_red(self._camera, c_int64(value))

    def set_balance_ratio_green(self, value: int) -> int:
        return self._dll.mc_hik_set_balance_ratio_green(self._camera, c_int64(value))

    def set_balance_ratio_blue(self, value: int) -> int:
        return self._dll.mc_hik_set_balance_ratio_blue(self._camera, c_int64(value))

    def start_grabbing(self) -> int:
        return self._dll.mc_hik_start_grabbing(self._camera)

    def stop_grabbing(self) -> int:
        return self._dll.mc_hik_stop_grabbing(self._camera)

    def get_frame_info(self, timeout_ms: int = 1000) -> tuple[int, McHikFrameInfo]:
        frame = McHikFrameInfo()
        status = self._dll.mc_hik_get_frame_info(self._camera, timeout_ms, byref(frame))
        return status, frame

    def get_frame_data(self, capacity: int, timeout_ms: int = 1000) -> tuple[int, McHikFrameInfo, bytes]:
        frame = McHikFrameInfo()
        buffer = (c_uint8 * max(capacity, 1))()
        status = self._dll.mc_hik_get_frame_data(self._camera, timeout_ms, buffer, capacity, byref(frame))
        if status != 0 or frame.byte_count == 0:
            return status, frame, b""
        byte_count = min(frame.byte_count, capacity)
        return status, frame, string_at(buffer, byte_count)

    def save_features(self, file_path: str | Path) -> int:
        path_bytes = str(file_path).encode("utf-8")
        return self._dll.mc_hik_save_features(self._camera, path_bytes)

    def load_features(self, file_path: str | Path) -> int:
        path_bytes = str(file_path).encode("utf-8")
        return self._dll.mc_hik_load_features(self._camera, path_bytes)

    def error_to_string(self, error_code: int) -> str:
        return self._dll.mc_hik_error_to_string(error_code).decode(errors="ignore")
