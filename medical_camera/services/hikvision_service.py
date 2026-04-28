from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from medical_camera.bridges import (
    HikvisionBridge,
    HikvisionBridgeLoadError,
    MV_DEFAULT_DEVICE_MASK,
)


@dataclass(slots=True)
class ServiceResult:
    ok: bool
    message: str
    code: int = 0
    data: Any = None


@dataclass(slots=True)
class HikvisionDeviceSummary:
    index: int
    model_name: str
    serial_number: str
    vendor_name: str
    transport_layer_type: int
    user_defined_name: str = ""
    ip_address: str = ""

    @property
    def display_name(self) -> str:
        name = self.user_defined_name or self.model_name or "Hikvision Camera"
        suffix = f" (SN: {self.serial_number})" if self.serial_number else ""
        return f"{name}{suffix}"


@dataclass(slots=True)
class HikvisionCapabilityView:
    resolution_text: str = "--"
    fps_text: str = "--"
    exposure_text: str = "--"
    gain_text: str = "--"
    white_balance_text: str = "--"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class HikvisionFrameView:
    width: int
    height: int
    frame_number: int
    pixel_type: int
    byte_count: int
    data: bytes = b""


class HikvisionCameraService:
    """Application-facing adapter that keeps native SDK failures contained."""

    def __init__(self) -> None:
        self._bridge: HikvisionBridge | None = None
        self._initialized = False
        self._camera_created = False
        self._connected = False
        self._payload_size = 0

    @property
    def connected(self) -> bool:
        return self._connected

    def enumerate_devices(self) -> ServiceResult:
        setup = self._ensure_ready()
        if not setup.ok:
            return setup

        try:
            assert self._bridge is not None
            status, devices = self._bridge.enumerate_devices(MV_DEFAULT_DEVICE_MASK)
            if status != 0:
                return self._error_result(status, "枚举海康设备失败")

            summaries = [
                HikvisionDeviceSummary(
                    index=int(item["index"]),
                    model_name=str(item["model_name"]),
                    serial_number=str(item["serial_number"]),
                    vendor_name=str(item["vendor_name"]),
                    transport_layer_type=int(item["transport_layer_type"]),
                    user_defined_name=str(item["user_defined_name"]),
                    ip_address=str(item["ip_address"]),
                )
                for item in devices
            ]
            return ServiceResult(True, "设备枚举成功", data=summaries)
        except Exception as exc:
            return ServiceResult(False, f"设备枚举异常: {exc}")

    def connect(self, device_index: int) -> ServiceResult:
        setup = self._ensure_ready()
        if not setup.ok:
            return setup

        try:
            assert self._bridge is not None
            status = self._bridge.open_by_index(device_index, MV_DEFAULT_DEVICE_MASK)
            if status != 0:
                return self._error_result(status, "打开海康设备失败")

            self._connected = True
            snapshot_result = self.query_capabilities()
            if snapshot_result.ok:
                snapshot_result.message = "海康设备连接成功"
                return snapshot_result
            return ServiceResult(True, "海康设备连接成功，但读取能力快照失败")
        except Exception as exc:
            self._connected = False
            return ServiceResult(False, f"连接海康设备异常: {exc}")

    def disconnect(self) -> ServiceResult:
        if not self._bridge or not self._connected:
            return ServiceResult(True, "设备已断开")

        try:
            status = self._bridge.close()
            if status != 0:
                return self._error_result(status, "关闭海康设备失败")
            self._connected = False
            return ServiceResult(True, "海康设备已断开")
        except Exception as exc:
            return ServiceResult(False, f"断开海康设备异常: {exc}")

    def query_capabilities(self) -> ServiceResult:
        if not self._bridge or not self._connected:
            return ServiceResult(False, "海康设备尚未连接")

        try:
            status, snapshot = self._bridge.query_snapshot()
            if status != 0:
                return self._error_result(status, "读取海康能力快照失败")

            if snapshot.payload_size.status == 0:
                self._payload_size = int(snapshot.payload_size.current)

            capability = HikvisionCapabilityView(
                resolution_text=self._build_resolution_text(snapshot),
                fps_text=self._build_fps_text(snapshot),
                exposure_text=self._build_exposure_text(snapshot),
                gain_text=self._build_gain_text(snapshot),
                white_balance_text=self._build_white_balance_text(snapshot),
                raw={
                    "width": self._int_node_to_dict(snapshot.width),
                    "height": self._int_node_to_dict(snapshot.height),
                    "payload_size": self._int_node_to_dict(snapshot.payload_size),
                    "exposure": self._float_node_to_dict(snapshot.exposure_time),
                    "gain": self._float_node_to_dict(snapshot.gain),
                    "frame_rate": self._float_node_to_dict(snapshot.frame_rate),
                    "exposure_auto": self._enum_node_to_dict(snapshot.exposure_auto),
                    "gain_auto": self._enum_node_to_dict(snapshot.gain_auto),
                    "white_balance_auto": self._enum_node_to_dict(snapshot.white_balance_auto),
                    "balance_ratio_red": self._int_node_to_dict(snapshot.balance_ratio_red),
                    "balance_ratio_green": self._int_node_to_dict(snapshot.balance_ratio_green),
                    "balance_ratio_blue": self._int_node_to_dict(snapshot.balance_ratio_blue),
                },
            )
            return ServiceResult(True, "海康能力快照读取成功", data=capability)
        except Exception as exc:
            return ServiceResult(False, f"读取海康能力快照异常: {exc}")

    def set_exposure_auto(self, enabled: bool) -> ServiceResult:
        return self._set_feature(lambda: self._bridge.set_exposure_auto(enabled), "设置自动曝光失败")

    def set_exposure_time(self, value: float) -> ServiceResult:
        return self._set_feature(lambda: self._bridge.set_exposure_time(value), "设置曝光失败")

    def set_gain_auto(self, enabled: bool) -> ServiceResult:
        return self._set_feature(lambda: self._bridge.set_gain_auto(enabled), "设置自动增益失败")

    def set_gain(self, value: float) -> ServiceResult:
        return self._set_feature(lambda: self._bridge.set_gain(value), "设置增益失败")

    def set_white_balance_auto(self, enabled: bool) -> ServiceResult:
        return self._set_feature(lambda: self._bridge.set_white_balance_auto(enabled), "设置自动白平衡失败")

    def set_balance_ratio(self, channel: str, value: int) -> ServiceResult:
        setters: dict[str, Callable[[int], int]] = {
            "red": self._bridge.set_balance_ratio_red if self._bridge else lambda _: -1,
            "green": self._bridge.set_balance_ratio_green if self._bridge else lambda _: -1,
            "blue": self._bridge.set_balance_ratio_blue if self._bridge else lambda _: -1,
        }
        setter = setters.get(channel)
        if setter is None:
            return ServiceResult(False, f"未知白平衡通道: {channel}")
        return self._set_feature(lambda: setter(value), f"设置白平衡 {channel} 失败")

    def save_features(self, file_path: str) -> ServiceResult:
        if not self._bridge or not self._connected:
            return ServiceResult(False, "海康设备尚未连接")
        try:
            status = self._bridge.save_features(file_path)
            if status != 0:
                return self._error_result(status, "导出 mfs 文件失败")
            return ServiceResult(True, f"已导出 mfs 文件: {file_path}")
        except Exception as exc:
            return ServiceResult(False, f"导出 mfs 文件异常: {exc}")

    def load_features(self, file_path: str) -> ServiceResult:
        if not self._bridge or not self._connected:
            return ServiceResult(False, "海康设备尚未连接")
        try:
            status = self._bridge.load_features(file_path)
            if status != 0:
                return self._error_result(status, "导入 mfs 文件失败")
            result = self.query_capabilities()
            result.message = f"已导入 mfs 文件: {file_path}" if result.ok else f"已导入 mfs 文件，但刷新能力快照失败"
            return result
        except Exception as exc:
            return ServiceResult(False, f"导入 mfs 文件异常: {exc}")

    def start_grabbing(self) -> ServiceResult:
        if not self._bridge or not self._connected:
            return ServiceResult(False, "海康设备尚未连接")

        try:
            status = self._bridge.start_grabbing()
            if status != 0:
                return self._error_result(status, "启动采集失败")
            return ServiceResult(True, "海康采集已启动")
        except Exception as exc:
            return ServiceResult(False, f"启动采集异常: {exc}")

    def stop_grabbing(self) -> ServiceResult:
        if not self._bridge or not self._connected:
            return ServiceResult(True, "海康采集已停止")

        try:
            status = self._bridge.stop_grabbing()
            if status != 0:
                return self._error_result(status, "停止采集失败")
            return ServiceResult(True, "海康采集已停止")
        except Exception as exc:
            return ServiceResult(False, f"停止采集异常: {exc}")

    def probe_frame(self, timeout_ms: int = 1000) -> ServiceResult:
        if not self._bridge or not self._connected:
            return ServiceResult(False, "海康设备尚未连接")

        try:
            status, frame = self._bridge.get_frame_info(timeout_ms)
            if status != 0 or frame.status != 0:
                code = frame.status if frame.status != 0 else status
                return self._error_result(code, "首帧探测失败")

            return ServiceResult(
                True,
                "首帧探测成功",
                data=HikvisionFrameView(
                    width=int(frame.width),
                    height=int(frame.height),
                    frame_number=int(frame.frame_number),
                    pixel_type=int(frame.pixel_type),
                    byte_count=int(frame.byte_count),
                ),
            )
        except Exception as exc:
            return ServiceResult(False, f"首帧探测异常: {exc}")

    def get_latest_frame(self, timeout_ms: int = 30) -> ServiceResult:
        if not self._bridge or not self._connected:
            return ServiceResult(False, "海康设备尚未连接")

        try:
            capacity = max(self._payload_size, 1024 * 1024)
            status, frame, data = self._bridge.get_frame_data(capacity, timeout_ms)
            if status != 0 or frame.status != 0:
                code = frame.status if frame.status != 0 else status
                return self._error_result(code, "读取画面帧失败")

            return ServiceResult(
                True,
                "读取画面帧成功",
                data=HikvisionFrameView(
                    width=int(frame.width),
                    height=int(frame.height),
                    frame_number=int(frame.frame_number),
                    pixel_type=int(frame.pixel_type),
                    byte_count=int(frame.byte_count),
                    data=data,
                ),
            )
        except Exception as exc:
            return ServiceResult(False, f"读取画面帧异常: {exc}")

    def shutdown(self) -> None:
        if not self._bridge:
            return
        try:
            if self._connected:
                self._bridge.close()
        except Exception:
            pass
        try:
            if self._camera_created:
                self._bridge.destroy_camera()
        except Exception:
            pass
        try:
            if self._initialized:
                self._bridge.finalize()
        except Exception:
            pass
        self._connected = False
        self._camera_created = False
        self._initialized = False
        self._payload_size = 0
        self._bridge = None

    def _set_feature(self, setter: Callable[[], int], error_prefix: str) -> ServiceResult:
        if not self._bridge or not self._connected:
            return ServiceResult(False, "海康设备尚未连接")
        try:
            status = setter()
            if status != 0:
                return self._error_result(status, error_prefix)
            result = self.query_capabilities()
            result.message = "参数设置成功" if result.ok else "参数已设置，但刷新能力快照失败"
            return result
        except Exception as exc:
            return ServiceResult(False, f"{error_prefix}: {exc}")

    def _ensure_ready(self) -> ServiceResult:
        if self._bridge is None:
            try:
                self._bridge = HikvisionBridge()
            except HikvisionBridgeLoadError as exc:
                return ServiceResult(False, f"加载海康桥接失败: {exc}")
            except Exception as exc:
                return ServiceResult(False, f"初始化海康桥接异常: {exc}")

        if not self._initialized:
            status = self._bridge.initialize()
            if status != 0:
                return self._error_result(status, "初始化海康 SDK 失败")
            self._initialized = True

        if not self._camera_created:
            try:
                self._bridge.create_camera()
            except Exception as exc:
                return ServiceResult(False, f"创建海康相机对象异常: {exc}")
            self._camera_created = True

        return ServiceResult(True, "海康桥接已就绪")

    def _error_result(self, code: int, prefix: str) -> ServiceResult:
        if self._bridge is None:
            return ServiceResult(False, prefix, code=code)
        return ServiceResult(False, f"{prefix}: {self._bridge.error_to_string(code)}", code=code)

    @staticmethod
    def _int_node_to_dict(node: Any) -> dict[str, Any]:
        return {
            "status": int(node.status),
            "available": node.status == 0,
            "current": int(node.current),
            "minimum": int(node.minimum),
            "maximum": int(node.maximum),
            "increment": int(node.increment),
        }

    @staticmethod
    def _float_node_to_dict(node: Any) -> dict[str, Any]:
        return {
            "status": int(node.status),
            "available": node.status == 0,
            "current": float(node.current),
            "minimum": float(node.minimum),
            "maximum": float(node.maximum),
        }

    @staticmethod
    def _enum_node_to_dict(node: Any) -> dict[str, Any]:
        return {
            "status": int(node.status),
            "available": node.status == 0,
            "current": int(node.current),
            "supported_values": [int(node.supported_values[index]) for index in range(int(node.supported_count))],
        }

    @staticmethod
    def _build_resolution_text(snapshot: Any) -> str:
        if snapshot.width.status != 0 or snapshot.height.status != 0:
            return "--"
        return f"{snapshot.width.current} x {snapshot.height.current}"

    @staticmethod
    def _build_fps_text(snapshot: Any) -> str:
        if snapshot.frame_rate.status != 0:
            return "--"
        return f"{snapshot.frame_rate.current:.2f} FPS"

    @staticmethod
    def _build_exposure_text(snapshot: Any) -> str:
        if snapshot.exposure_time.status != 0:
            return "--"
        return f"{snapshot.exposure_time.current:.0f} us"

    @staticmethod
    def _build_gain_text(snapshot: Any) -> str:
        if snapshot.gain.status != 0:
            return "--"
        return f"{snapshot.gain.current:.1f} dB"

    @staticmethod
    def _build_white_balance_text(snapshot: Any) -> str:
        parts: list[str] = []
        if snapshot.balance_ratio_red.status == 0:
            parts.append(f"R:{snapshot.balance_ratio_red.current}")
        if snapshot.balance_ratio_green.status == 0:
            parts.append(f"G:{snapshot.balance_ratio_green.current}")
        if snapshot.balance_ratio_blue.status == 0:
            parts.append(f"B:{snapshot.balance_ratio_blue.current}")
        return " ".join(parts) if parts else "--"
