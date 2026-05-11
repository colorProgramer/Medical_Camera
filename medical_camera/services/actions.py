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
from medical_camera.services.usb_service import UsbCameraService

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
    language: str = "zh_CN"
    hik_params: dict[str, Any] = field(default_factory=dict)
    available_devices: list[str] = field(default_factory=list)
    selected_device_index: int = 0
    logs: list[str] = field(default_factory=list)
    
    # USB specific params
    usb_width: int = 1920
    usb_height: int = 1080
    usb_fps: int = 30
    usb_pixel_format: str = "MJPG"
    recognition_threshold: int = 20
    shape_threshold: int = 10
    fov_n_percent: float = 70.0
    overlay_visibility: dict[str, bool] = field(default_factory=lambda: {
        "show_fov_boundary": False,
        "show_ellipses": False,
        "show_fov_n": False,
        "show_fov_center": False,
        "show_screen_center": False,
    })
    roi_rect: Any | None = None
    manual_fov_circle: dict | None = None  # {cx, cy, r} normalized [0,1], None=auto detect


class ActionDispatcher:
    """Single entry for page actions from UI or future AI commands."""

    def __init__(self) -> None:
        self.state = AppState()
        self._lock = RLock()
        self._hikvision = HikvisionCameraService()
        self._usb = UsbCameraService()
        self._append_log("系统", "应用框架已启动")
        self._refresh_device_list()

    def switch_device_type(self, device_key: str) -> AppState:
        with self._lock:
            # Force close and disconnect everything before switching profiles
            self._close_camera({})
            self._hikvision.disconnect()
            self._usb.disconnect()
            
            self.state.current_profile = DEVICE_PROFILES[device_key]
            self.state.connected = False
            self.state.collecting = False
            self.state.recognizing = False
            self.state.selected_device_index = 0
            if device_key == "hikvision":
                self._append_log("设备", "已切换到海康工业相机模式")
                self.state.available_devices = ["正在枚举海康设备..."]
            else:
                self._append_log("设备", "已切换到 USB 相机模式")
                self.state.available_devices = ["正在枚举 USB 设备..."]
                self.state.resolution_text = "auto_detect"
                self.state.fps_text = "auto_detect"
                self.state.exposure_text = "--"
                self.state.gain_text = "--"
                self.state.white_balance_text = "--"
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
                "open_camera": self._open_camera,
                "close_camera": self._close_camera,
                "save_image": self._save_image,
                "start_recognition": self._start_recognition,
                "stop_recognition": self._stop_recognition,
                "set_recognition_mode": self._set_recognition_mode,
                "set_detection_scope": self._set_detection_scope,
                "set_field_shape": self._set_field_shape,
                "set_pattern_mode": self._set_pattern_mode,
                "set_recognition_threshold": self._set_recognition_threshold,
                "set_shape_threshold": self._set_shape_threshold,
                "set_fov_n_percent": self._set_fov_n_percent,
                "set_overlay_visibility": self._set_overlay_visibility,
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
                "export_mfs": self._export_mfs,
                "import_mfs": self._import_mfs,
                "append_log": self._append_log_action,
                "apply_usb_params": self._apply_usb_params,
                "import_global_config": self._import_global_config,
                "export_global_config": self._export_global_config,
                "set_language": self._set_language,
                "set_roi_rect": self._set_roi_rect,
                "set_manual_fov_circle": self._set_manual_fov_circle,
            }
            handler = handlers.get(action)
            if handler is None:
                self._append_log("警告", f"未识别动作: {action}")
                return self.state
            handler(payload)
            return self.state

    def shutdown(self) -> None:
        with self._lock:
            self._close_camera({})
            self._hikvision.shutdown()
            self._usb.disconnect()

    def get_latest_frame(self, timeout_ms: int = 10):
        with self._lock:
            if not self.state.collecting:
                return None
            
            if self.state.current_profile.key == "hikvision":
                result = self._hikvision.get_latest_frame(timeout_ms=timeout_ms)
                return result.data if result.ok else None
            else:
                result = self._usb.get_latest_frame(timeout_ms=timeout_ms)
                return result.data if result.ok else None

    def _open_camera(self, payload: dict[str, Any]) -> None:
        self._connect_device(payload)
        if self.state.connected:
            self._start_collection(payload)

    def _close_camera(self, payload: dict[str, Any]) -> None:
        self._stop_collection(payload)
        self._disconnect_device(payload)

    def _connect_device(self, _: dict[str, Any]) -> None:
        if self.state.current_profile.key != "hikvision":
            if not self.state.available_devices:
                self._append_log("错误", "连接失败：当前未发现可用 USB 设备")
                return
            result = self._usb.connect(self.state.selected_device_index)
            if result.ok:
                self.state.connected = True
                self.state.resolution_text = "自动探测"
                self.state.fps_text = "自动探测"
                self._append_log("设备", f"已连接 USB 相机: {self._current_device_name()}")
            else:
                self._append_log("设备", result.message)
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
            result = self._usb.disconnect()
            self._append_log("设备", result.message)
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
            result = self._usb.start_grabbing()
            self._append_log("采集", result.message)
            if not result.ok:
                return
        self.state.collecting = True

    def _stop_collection(self, _: dict[str, Any]) -> None:
        if self.state.current_profile.key == "hikvision":
            result = self._hikvision.stop_grabbing()
            self._append_log("采集", result.message)
        else:
            result = self._usb.stop_grabbing()
            self._append_log("采集", result.message)
        self.state.collecting = False

    def _save_image(self, payload: dict[str, Any]) -> None:
        file_path = payload.get("file_path")
        count = max(1, int(payload.get("count", 1)))
        if not file_path:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            name = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            file_path = os.path.join(desktop, name)

        base, ext = os.path.splitext(file_path)
        for i in range(count):
            if count > 1:
                save_path = f"{base}_{i + 1:03d}{ext}"
            else:
                save_path = file_path
            if self.state.current_profile.key == "hikvision":
                result = self._hikvision.save_current_frame(save_path)
            else:
                result = self._usb.save_current_frame(save_path)
            self._append_log("保存", result.message)
            if count > 1 and i < count - 1:
                import time
                time.sleep(0.1)

    def _start_recognition(self, _: dict[str, Any]) -> None:
        if not self.state.collecting:
            self._append_log("识别", "采集尚未启动，识别已阻止")
            return
        self.state.recognizing = True
        self._append_log("识别", "已开启识别")

    def _stop_recognition(self, _: dict[str, Any]) -> None:
        self.state.recognizing = False
        self._append_log("识别", "识别已停止")

    def _set_recognition_mode(self, payload: dict[str, Any]) -> None:
        self.state.recognition_mode = str(payload["value"])
        self._append_log("识别", f"识别模式切换为: {self.state.recognition_mode}")

    def _set_detection_scope(self, payload: dict[str, Any]) -> None:
        scope = str(payload["value"])
        self.state.detection_scope = scope
        if scope == "three_point":
            # Three-point circle mode forces circle FOV type
            self.state.field_shape = "circle"
        elif scope != "three_point":
            # Leaving three_point mode: clear manual circle
            self.state.manual_fov_circle = None
        self._append_log("识别", f"识别区域切换为: {scope}")

    def _set_field_shape(self, payload: dict[str, Any]) -> None:
        self.state.field_shape = str(payload["value"])
        self._append_log("识别", f"视场类型切换为: {self.state.field_shape}")

    def _set_pattern_mode(self, payload: dict[str, Any]) -> None:
        self.state.pattern_mode = str(payload["value"])
        self._append_log("识别", f"图案模式切换为: {self.state.pattern_mode}")

    def _set_recognition_threshold(self, payload: dict[str, Any]) -> None:
        self.state.recognition_threshold = float(payload["value"])
        self._append_log("识别", f"识别阈值调整为: {self.state.recognition_threshold}")

    def _set_shape_threshold(self, payload: dict[str, Any]) -> None:
        self.state.shape_threshold = int(payload["value"])
        self._append_log("识别", f"图形提取阈值调整为: {self.state.shape_threshold}")

    def _set_fov_n_percent(self, payload: dict[str, Any]) -> None:
        self.state.fov_n_percent = float(payload["value"])

    def _set_overlay_visibility(self, payload: dict[str, Any]) -> None:
        key = str(payload["key"])
        visible = bool(payload["value"])
        self.state.overlay_visibility[key] = visible
        self._append_log("界面", f"图层 '{key}' 可见性设置为: {visible}")

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
        hik_params = self.state.hik_params
        if hik_params:
            ea = hik_params.get("exposure_auto", {})
            if ea.get("available") and ea.get("current", 0) > 0:
                self._append_log("参数", "自动曝光开启中，手动曝光值已忽略，请先关闭自动曝光")
                return
        result = self._hikvision.set_exposure_time(float(payload["value"]))
        self._apply_hik_result("参数", result)

    def _set_hik_gain_auto(self, payload: dict[str, Any]) -> None:
        result = self._hikvision.set_gain_auto(bool(payload.get("value", False)))
        self._apply_hik_result("参数", result)

    def _set_hik_gain(self, payload: dict[str, Any]) -> None:
        hik_params = self.state.hik_params
        if hik_params:
            ga = hik_params.get("gain_auto", {})
            if ga.get("available") and ga.get("current", 0) > 0:
                self._append_log("参数", "自动增益开启中，手动增益值已忽略，请先关闭自动增益")
                return
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
        if not self.state.connected:
            self._append_log("参数", "相机未连接，无法导入 mfs")
            return
            
        was_collecting = self.state.collecting
        if was_collecting:
            self._stop_collection({})

        file_path = payload.get("file_path", "")
        if not file_path:
            self._append_log("参数", "未指定 mfs 文件路径")
        elif not os.path.exists(file_path):
            self._append_log("参数", f"mfs 文件不存在: {file_path}")
        else:
            result = self._hikvision.load_features(file_path)
            if result.ok:
                self._apply_hikvision_capability(result.data)
            self._append_log("参数", result.message)
            
        if was_collecting:
            self._start_collection({})

    def _export_mfs(self, payload: dict[str, Any]) -> None:
        file_path = payload.get("file_path", "config.mfs")
        if not self.state.connected or self.state.current_profile.key != "hikvision":
            self._append_log("备份", "设备未连接，无法导出 MFS")
            return

        was_collecting = self.state.collecting
        if was_collecting:
            self._stop_collection({})

        result = self._hikvision.save_features(file_path)
        self._append_log("备份", result.message)

        if was_collecting:
            self._start_collection({})

    def _apply_usb_params(self, payload: dict[str, Any]) -> None:
        width = payload.get("width", 1920)
        height = payload.get("height", 1080)
        fps = payload.get("fps", 30)
        pixel_format = payload.get("pixel_format", "MJPG")
        
        result = self._usb.set_parameters(width, height, fps, pixel_format)
        self._append_log("设置", result.message)
        if result.ok:
            self.state.resolution_text = f"{width} x {height}"
            self.state.fps_text = f"{fps} FPS"
            # Update state for UI sync
            self.state.usb_width = width
            self.state.usb_height = height
            self.state.usb_fps = fps
            self.state.usb_pixel_format = pixel_format

    def _import_global_config(self, payload: dict[str, Any]) -> None:
        file_path = payload.get("file_path")
        if not file_path:
            return
        try:
            import json
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                
            device_type = config.get("device_type")
            if device_type and self.state.current_profile.key != device_type:
                if self.state.connected:
                    self._disconnect_device({})
                self.switch_device_type(device_type)
                
            usb_params = config.get("usb_params", {})
            if usb_params:
                self.state.usb_width = usb_params.get("width", self.state.usb_width)
                self.state.usb_height = usb_params.get("height", self.state.usb_height)
                self.state.usb_fps = usb_params.get("fps", self.state.usb_fps)
                self.state.usb_pixel_format = usb_params.get("pixel_format", self.state.usb_pixel_format)
                if self.state.current_profile.key == "usb" and self.state.connected:
                    self._apply_usb_params(usb_params)

            hik_params = config.get("hik_params", {})
            if hik_params and self.state.current_profile.key == "hikvision" and self.state.connected:
                self._apply_imported_hik_params(hik_params)
                    
            rec_params = config.get("recognition", {})
            if rec_params:
                self.state.detection_scope = rec_params.get("detection_scope", self.state.detection_scope)
                self.state.recognition_threshold = rec_params.get("recognition_threshold", self.state.recognition_threshold)
                self.state.shape_threshold = rec_params.get("shape_threshold", self.state.shape_threshold)
                self.state.field_shape = rec_params.get("field_shape", self.state.field_shape)
                self.state.pattern_mode = rec_params.get("pattern_mode", self.state.pattern_mode)
                
            overlay_params = config.get("overlay", {})
            if overlay_params:
                if "visibility" in overlay_params:
                    self.state.overlay_visibility.update(overlay_params["visibility"])
                self.state.fov_n_percent = overlay_params.get("fov_n_percent", self.state.fov_n_percent)
                
            roi_params = config.get("roi")
            
            lang = config.get("language")
            if lang:
                self._set_language({"value": lang})
            if roi_params:
                from PySide6.QtCore import QRectF
                x, y, w, h = roi_params["x"], roi_params["y"], roi_params["w"], roi_params["h"]
                self.state.roi_rect = QRectF(x, y, w, h)

            fov_circle = config.get("manual_fov_circle")
            if fov_circle and isinstance(fov_circle, dict):
                self.state.manual_fov_circle = fov_circle
                
            self._append_log("配置", f"全局配置已加载: {file_path}")
        except Exception as e:
            self._append_log("配置", f"读取全局配置失败: {e}")

    def _apply_imported_hik_params(self, hik_params: dict[str, Any]) -> None:
        was_collecting = self.state.collecting
        if was_collecting:
            self._stop_collection({})

        if "exposure_auto" in hik_params:
            ea = hik_params["exposure_auto"]
            auto_on = ea.get("current", 0) > 0 if isinstance(ea, dict) else bool(ea)
            self._hikvision.set_exposure_auto(auto_on)

        if "gain_auto" in hik_params:
            ga = hik_params["gain_auto"]
            auto_on = ga.get("current", 0) > 0 if isinstance(ga, dict) else bool(ga)
            self._hikvision.set_gain_auto(auto_on)

        if "white_balance_auto" in hik_params:
            wba = hik_params["white_balance_auto"]
            auto_on = wba.get("current", 0) > 0 if isinstance(wba, dict) else bool(wba)
            self._hikvision.set_white_balance_auto(auto_on)

        if "exposure" in hik_params:
            exp = hik_params["exposure"]
            val = exp.get("current", exp) if isinstance(exp, dict) else exp
            self._hikvision.set_exposure_time(float(val))

        if "gain" in hik_params:
            gn = hik_params["gain"]
            val = gn.get("current", gn) if isinstance(gn, dict) else gn
            self._hikvision.set_gain(float(val))

        for ch, key in [("red", "balance_ratio_red"), ("green", "balance_ratio_green"), ("blue", "balance_ratio_blue")]:
            if key in hik_params:
                br = hik_params[key]
                val = br.get("current", br) if isinstance(br, dict) else br
                self._hikvision.set_balance_ratio(ch, int(val))

        result = self._hikvision.query_capabilities()
        if result.ok:
            self._apply_hikvision_capability(result.data)

        if was_collecting:
            self._start_collection({})

    def _export_global_config(self, payload: dict[str, Any]) -> None:
        file_path = payload.get("file_path")
        if not file_path:
            return
            
        try:
            import json
            roi_data = None
            if self.state.roi_rect:
                r = self.state.roi_rect
                roi_data = {"x": r.x(), "y": r.y(), "w": r.width(), "h": r.height()}

            hik_params = self.state.hik_params
            hik_export = {}
            if hik_params:
                for key in ("exposure", "gain", "exposure_auto", "gain_auto",
                            "white_balance_auto", "balance_ratio_red",
                            "balance_ratio_green", "balance_ratio_blue"):
                    if key in hik_params:
                        hik_export[key] = hik_params[key]

            config = {
                "device_type": self.state.current_profile.key,
                "usb_params": {
                    "width": self.state.usb_width,
                    "height": self.state.usb_height,
                    "fps": self.state.usb_fps,
                    "pixel_format": self.state.usb_pixel_format
                },
                "hik_params": hik_export,
                "recognition": {
                    "detection_scope": self.state.detection_scope,
                    "recognition_threshold": self.state.recognition_threshold,
                    "shape_threshold": self.state.shape_threshold,
                    "field_shape": self.state.field_shape,
                    "pattern_mode": self.state.pattern_mode
                },
                "overlay": {
                    "visibility": self.state.overlay_visibility.copy(),
                    "fov_n_percent": self.state.fov_n_percent
                },
                "roi": roi_data,
                "manual_fov_circle": self.state.manual_fov_circle,
                "language": self.state.language,
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self._append_log("配置", f"全局配置已保存至: {file_path}")
        except Exception as e:
            self._append_log("配置", f"保存全局配置失败: {e}")

    def _refresh_device_list(self) -> None:
        if self.state.current_profile.key == "hikvision":
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
        else:
            result = self._usb.enumerate_devices()
            self.state.available_devices = result.data
            self._append_log("设备", result.message)

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

    def _set_roi_rect(self, payload: dict[str, Any]) -> None:
        self.state.roi_rect = payload.get("roi")

    def _set_manual_fov_circle(self, payload: dict[str, Any]) -> None:
        self.state.manual_fov_circle = payload.get("circle")

    def _append_log_action(self, payload: dict[str, Any]) -> None:
        self._append_log(payload.get("category", "系统"), payload.get("message", ""))

    def _set_language(self, payload: dict[str, Any]) -> None:
        lang = payload.get("value", "zh_CN")
        self.state.language = lang
        from medical_camera.services.i18n import i18n
        i18n.set_language(lang)
        self._append_log("系统", f"语言切换为: {lang}")

    def _append_log(self, category: str, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.state.logs.insert(0, f"{timestamp} [{category}] {message}")
        self.state.logs = self.state.logs[:50]
