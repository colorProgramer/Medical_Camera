from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Any

from medical_camera.models.device import DEVICE_PROFILES, DeviceProfile, HIKVISION_PROFILE
from medical_camera.services.hikvision_service import (
    HikvisionCameraService,
    HikvisionDeviceSummary,
    HikvisionFrameView,
)

import os


@dataclass
class AppState:
    current_profile: DeviceProfile = HIKVISION_PROFILE
    theme: str = "light"
    connected: bool = False
    collecting: bool = False
    recognizing: bool = False
    recognition_mode: str = "single"
    detection_scope: str = "full"
    field_shape: str = "circle"
    pattern_mode: str = "dark_bg"
    zoom_text: str = "1.0x"
    resolution_text: str = "--"
    fps_text: str = "--"
    exposure_text: str = "--"
    gain_text: str = "--"
    white_balance_text: str = "--"
    hik_params: dict[str, Any] = field(default_factory=dict)
    available_devices: list[str] = field(default_factory=list)
    selected_device_index: int = 0
    logs: list[str] = field(default_factory=list)


class ActionDispatcher:
    """Single entry for page actions from UI or future AI commands."""

    def __init__(self) -> None:
        self.state = AppState()
        self._lock = RLock()
        self._hikvision = HikvisionCameraService()
        self._append_log("系统", "应用框架已启动")
        if self.state.current_profile.key == "hikvision":
            self.state.available_devices = ["正在枚举设备..."]
        else:
            self._refresh_device_list()

    def switch_device_type(self, device_key: str) -> AppState:
        with self._lock:
            self.state.current_profile = DEVICE_PROFILES[device_key]
            self.state.connected = False
            self.state.collecting = False
            self.state.recognizing = False
            self.state.selected_device_index = 0
            if device_key == "hikvision":
                self._append_log("设备", "已切换到海康工业相机模式")
                self.state.available_devices = ["正在枚举设备..."]
            else:
                self._append_log("设备", "已切换到 USB 相机模式")
                self.state.resolution_text = "1920 x 1080"
                self.state.fps_text = "60 FPS"
                self.state.exposure_text = "--"
                self.state.gain_text = "--"
                self.state.white_balance_text = "--"
                self._refresh_device_list()
            return self.state

    def apply_device_list(self, devices: list[str] | None, log_msg: str | None = None) -> None:
        with self._lock:
            if devices is not None:
                self.state.available_devices = devices
            if log_msg:
                self._append_log("设备", log_msg)

    def dispatch(self, action: str, payload: dict[str, Any] | None = None) -> AppState:
        with self._lock:
            payload = payload or {}
            handlers = {
                "connect_device": self._connect_device,
                "disconnect_device": self._disconnect_device,
                "start_collection": self._start_collection,
                "stop_collection": self._stop_collection,
                "save_image": self._save_image,
                "start_recognition": self._start_recognition,
                "stop_recognition": self._stop_recognition,
                "set_recognition_mode": self._set_recognition_mode,
                "set_detection_scope": self._set_detection_scope,
                "set_field_shape": self._set_field_shape,
                "set_pattern_mode": self._set_pattern_mode,
                "select_device": self._select_device,
                "refresh_devices": self._refresh_devices_action,
                "set_hik_exposure_auto": self._set_hik_exposure_auto,
                "set_hik_exposure": self._set_hik_exposure,
                "set_hik_gain_auto": self._set_hik_gain_auto,
                "set_hik_gain": self._set_hik_gain,
                "set_hik_white_balance_auto": self._set_hik_white_balance_auto,
                "set_hik_balance_ratio": self._set_hik_balance_ratio,
                "sync_hik_params": self._sync_hik_params,
                "reset_view": self._reset_view,
                "toggle_theme": self._toggle_theme,
                "import_mfs": self._import_mfs,
                "export_mfs": self._export_mfs,
                "append_log": self._append_log_action,
            }
            handler = handlers.get(action)
            if handler is None:
                self._append_log("警告", f"未识别动作: {action}")
                return self.state
            handler(payload)
            return self.state

    def shutdown(self) -> None:
        with self._lock:
            self._hikvision.shutdown()

    def get_latest_frame(self, timeout_ms: int = 10):
        with self._lock:
            if not self.state.collecting or self.state.current_profile.key != "hikvision":
                return None
            result = self._hikvision.get_latest_frame(timeout_ms=timeout_ms)
            return result.data if result.ok else None

    def _connect_device(self, _: dict[str, Any]) -> None:
        if self.state.current_profile.key != "hikvision":
            self.state.connected = True
            self._append_log("设备", "USB 相机连接占位逻辑已触发")
            return

        result = self._hikvision.connect(self.state.selected_device_index)
        if not result.ok:
            self._append_log("设备", result.message)
            return

        self.state.connected = True
        self._apply_hikvision_capability(result.data)
        self._append_log("设备", f"已连接海康设备: {self._current_device_name()}")

    def _disconnect_device(self, _: dict[str, Any]) -> None:
        if self.state.current_profile.key == "hikvision":
            result = self._hikvision.disconnect()
            self._append_log("设备", result.message)
        else:
            self._append_log("设备", "USB 相机已断开")
        self.state.connected = False
        self.state.collecting = False
        self.state.recognizing = False

    def _start_collection(self, _: dict[str, Any]) -> None:
        if not self.state.connected:
            self._append_log("采集", "设备尚未连接，无法开始采集")
            return

        if self.state.current_profile.key == "hikvision":
            result = self._hikvision.start_grabbing()
            self._append_log("采集", result.message)
            if not result.ok:
                return
            self._log_first_frame_probe()
        else:
            self._append_log("采集", "USB 相机采集占位逻辑已触发")
        self.state.collecting = True

    def _stop_collection(self, _: dict[str, Any]) -> None:
        if self.state.current_profile.key == "hikvision":
            result = self._hikvision.stop_grabbing()
            self._append_log("采集", result.message)
        else:
            self._append_log("采集", "USB 相机采集停止占位逻辑已触发")
        self.state.collecting = False

    def _save_image(self, _: dict[str, Any]) -> None:
        self._append_log("保存", "已触发保存图片动作")

    def _start_recognition(self, _: dict[str, Any]) -> None:
        if not self.state.collecting:
            self._append_log("识别", "采集尚未启动，识别已阻止")
            return
        self.state.recognizing = True
        mode_text = "实时识别" if self.state.recognition_mode == "real_time" else "单次识别"
        self._append_log("识别", f"已开始{mode_text}")

    def _stop_recognition(self, _: dict[str, Any]) -> None:
        self.state.recognizing = False
        self._append_log("识别", "识别已停止")

    def _set_recognition_mode(self, payload: dict[str, Any]) -> None:
        self.state.recognition_mode = str(payload["value"])
        self._append_log("识别", f"识别模式切换为: {self.state.recognition_mode}")

    def _set_detection_scope(self, payload: dict[str, Any]) -> None:
        self.state.detection_scope = str(payload["value"])
        self._append_log("识别", f"识别区域切换为: {self.state.detection_scope}")

    def _set_field_shape(self, payload: dict[str, Any]) -> None:
        self.state.field_shape = str(payload["value"])
        self._append_log("识别", f"视场类型切换为: {self.state.field_shape}")

    def _set_pattern_mode(self, payload: dict[str, Any]) -> None:
        self.state.pattern_mode = str(payload["value"])
        self._append_log("识别", f"图案模式切换为: {self.state.pattern_mode}")

    def _select_device(self, payload: dict[str, Any]) -> None:
        self.state.selected_device_index = int(payload.get("value", 0))

    def _refresh_devices_action(self, _: dict[str, Any]) -> None:
        if self.state.current_profile.key == "hikvision":
            self.state.available_devices = ["正在枚举设备..."]
        else:
            self._refresh_device_list()

    def _set_hik_exposure_auto(self, payload: dict[str, Any]) -> None:
        result = self._hikvision.set_exposure_auto(bool(payload.get("value", False)))
        self._apply_hik_result("参数", result)

    def _set_hik_exposure(self, payload: dict[str, Any]) -> None:
        result = self._hikvision.set_exposure_time(float(payload["value"]))
        self._apply_hik_result("参数", result)

    def _set_hik_gain_auto(self, payload: dict[str, Any]) -> None:
        result = self._hikvision.set_gain_auto(bool(payload.get("value", False)))
        self._apply_hik_result("参数", result)

    def _set_hik_gain(self, payload: dict[str, Any]) -> None:
        result = self._hikvision.set_gain(float(payload["value"]))
        self._apply_hik_result("参数", result)

    def _set_hik_white_balance_auto(self, payload: dict[str, Any]) -> None:
        result = self._hikvision.set_white_balance_auto(bool(payload.get("value", False)))
        self._apply_hik_result("参数", result)

    def _set_hik_balance_ratio(self, payload: dict[str, Any]) -> None:
        result = self._hikvision.set_balance_ratio(str(payload["channel"]), int(payload["value"]))
        self._apply_hik_result("参数", result)

    def _sync_hik_params(self, _: dict[str, Any]) -> None:
        if self.state.current_profile.key != "hikvision" or not self.state.connected:
            return
        result = self._hikvision.query_capabilities()
        if result.ok:
            self._apply_hikvision_capability(result.data)

    def _reset_view(self, _: dict[str, Any]) -> None:
        self.state.zoom_text = "1.0x"
        self._append_log("画面", "画面视图已复位")

    def _toggle_theme(self, _: dict[str, Any]) -> None:
        self.state.theme = "dark" if self.state.theme == "light" else "light"
        self._append_log("界面", f"主题已切换为: {self.state.theme}")

    def _import_mfs(self, payload: dict[str, Any]) -> None:
        if self.state.collecting:
            self._append_log("参数", "采集画面状态下无法导入 mfs，请先停止采集")
            return
        file_path = payload.get("file_path", "")
        if not file_path:
            self._append_log("参数", "未指定 mfs 文件路径")
            return
        if not os.path.exists(file_path):
            self._append_log("参数", f"mfs 文件不存在: {file_path}")
            return
        result = self._hikvision.load_features(file_path)
        if result.ok:
            self._apply_hikvision_capability(result.data)
        self._append_log("参数", result.message)

    def _export_mfs(self, payload: dict[str, Any]) -> None:
        if self.state.collecting:
            self._append_log("参数", "采集画面状态下无法导出 mfs，请先停止采集")
            return
        file_path = payload.get("file_path", "")
        if not file_path:
            self._append_log("参数", "未指定 mfs 文件路径")
            return
        result = self._hikvision.save_features(file_path)
        self._append_log("参数", result.message)

    def _refresh_device_list(self) -> None:
        if self.state.current_profile.key != "hikvision":
            self.state.available_devices = [self.state.current_profile.sample_device]
            return

        result = self._hikvision.enumerate_devices()
        if not result.ok:
            self.state.available_devices = ["未发现海康设备"]
            self._append_log("设备", result.message)
            return

        devices: list[HikvisionDeviceSummary] = result.data
        if not devices:
            self.state.available_devices = ["未发现海康设备"]
            self._append_log("设备", "未枚举到海康设备")
            return

        self.state.available_devices = [device.display_name for device in devices]
        self._append_log("设备", f"已枚举到 {len(devices)} 台海康设备")

    def _apply_hikvision_capability(self, capability: Any) -> None:
        if capability is None:
            return
        self.state.resolution_text = capability.resolution_text
        self.state.fps_text = capability.fps_text
        self.state.exposure_text = capability.exposure_text
        self.state.gain_text = capability.gain_text
        self.state.white_balance_text = capability.white_balance_text
        self.state.hik_params = capability.raw

    def _apply_hik_result(self, category: str, result: Any) -> None:
        if result.ok:
            self._apply_hikvision_capability(result.data)
        self._append_log(category, result.message)

    def _log_first_frame_probe(self) -> None:
        result = self._hikvision.probe_frame()
        if not result.ok:
            self._append_log("采集", result.message)
            return
        frame: HikvisionFrameView = result.data
        self._append_log(
            "采集",
            f"首帧有效: {frame.width} x {frame.height}, Bytes={frame.byte_count}, FrameNo={frame.frame_number}",
        )

    def _current_device_name(self) -> str:
        if not self.state.available_devices:
            return self.state.current_profile.sample_device
        index = min(max(self.state.selected_device_index, 0), len(self.state.available_devices) - 1)
        return self.state.available_devices[index]

    def _append_log_action(self, payload: dict[str, Any]) -> None:
        self._append_log(payload.get("category", "系统"), payload.get("message", ""))

    def _append_log(self, category: str, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.state.logs.insert(0, f"{timestamp} [{category}] {message}")
        self.state.logs = self.state.logs[:50]
