from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

@dataclass(slots=True)
class UsbServiceResult:
    ok: bool
    message: str
    data: Any = None

@dataclass(slots=True)
class UsbFrameView:
    width: int
    height: int
    frame_number: int
    pixel_type: int
    data: bytes
    byte_count: int

class UsbCameraService:
    def __init__(self) -> None:
        self._cap: cv2.VideoCapture | None = None
        self._connected = False
        self._running = False
        self._thread: threading.Thread | None = None
        self._latest_frame: UsbFrameView | None = None
        self._lock = threading.Lock()
        self._frame_counter = 0

    @property
    def connected(self) -> bool:
        return self._connected

    def enumerate_devices(self) -> UsbServiceResult:
        from medical_camera.bridges.usb_bridge import UsbBridge
        bridge = UsbBridge()
        
        available = []
        if bridge.available:
            try:
                count = bridge.get_device_count()
                for i in range(count):
                    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                    if not cap or not cap.isOpened():
                        cap = cv2.VideoCapture(i)
                    
                    if cap and cap.isOpened():
                        name = bridge.get_device_name(i)
                        available.append(name)
                        cap.release()
            except Exception as e:
                return UsbServiceResult(False, f"枚举 USB 设备时发生异常: {e}", data=["枚举失败"])
        else:
            # Fallback for when the DLL is not available
            for i in range(5):
                try:
                    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                    if cap and cap.isOpened():
                        available.append(f"USB Camera {i} (Native Bridge Not Found)")
                        cap.release()
                except Exception:
                    continue
        
        if not available:
            return UsbServiceResult(False, "未发现可用 USB 相机", data=["未发现 USB 设备"])
        return UsbServiceResult(True, f"发现 {len(available)} 个 USB 设备", data=available)

    def connect(self, index: int) -> UsbServiceResult:
        self.disconnect()
        
        try:
            self._cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not self._cap.isOpened():
                return UsbServiceResult(False, f"无法打开 USB 相机 index={index}")
            
            # Set default parameters on connect
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self._connected = True
            self._frame_counter = 0
            return UsbServiceResult(True, f"USB 相机连接成功 (分辨率: {w}x{h})")
        except Exception as e:
            return UsbServiceResult(False, f"连接 USB 相机异常: {e}")

    def set_parameters(self, width: int, height: int, fps: int, pixel_format: str) -> UsbServiceResult:
        if not self._cap or not self._connected:
            return UsbServiceResult(False, "相机未连接")
        
        try:
            # MJPG/YUY2 handling
            fourcc = cv2.VideoWriter_fourcc(*pixel_format) if len(pixel_format) == 4 else -1
            
            was_running = self._running
            if was_running:
                self.stop_grabbing()
            
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self._cap.set(cv2.CAP_PROP_FPS, fps)
            if fourcc != -1:
                self._cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            
            # Verify actual params
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            f = int(self._cap.get(cv2.CAP_PROP_FPS))
            
            if was_running:
                self.start_grabbing()
                
            return UsbServiceResult(True, f"参数已更新: {w}x{h} @ {f} FPS ({pixel_format})")
        except Exception as e:
            return UsbServiceResult(False, f"设置 USB 参数失败: {e}")

    def disconnect(self) -> UsbServiceResult:
        self.stop_grabbing()
        if self._cap:
            self._cap.release()
            self._cap = None
        self._connected = False
        return UsbServiceResult(True, "USB 相机已断开")

    def start_grabbing(self) -> UsbServiceResult:
        if not self._connected or not self._cap:
            return UsbServiceResult(False, "相机未连接")
        
        if self._running:
            return UsbServiceResult(True, "采集已在运行")
        
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        return UsbServiceResult(True, "USB 采集已启动")

    def stop_grabbing(self) -> UsbServiceResult:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        return UsbServiceResult(True, "USB 采集已停止")

    def get_latest_frame(self, timeout_ms: int = 10) -> UsbServiceResult:
        with self._lock:
            if self._latest_frame:
                return UsbServiceResult(True, "获取帧成功", data=self._latest_frame)
            return UsbServiceResult(False, "无可用帧")

    def save_current_frame(self, file_path: str) -> UsbServiceResult:
        with self._lock:
            frame = self._latest_frame
        
        if not frame:
            return UsbServiceResult(False, "没有正在运行的采集流，无法截图")
        
        try:
            # frame.data is stored as RGB for viewport compatibility
            rgb_arr = np.frombuffer(frame.data, dtype=np.uint8).reshape((frame.height, frame.width, 3))
            
            ext = file_path.lower().split('.')[-1]
            if ext == 'raw':
                # Save the raw buffer (which is currently RGB bytes)
                with open(file_path, "wb") as f:
                    f.write(frame.data)
                return UsbServiceResult(True, f"图片已保存 (RAW 原始数据): {file_path}")

            # Convert RGB back to BGR for OpenCV imwrite
            bgr_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
            
            params = []
            if ext in ('jpg', 'jpeg'):
                params = [cv2.IMWRITE_JPEG_QUALITY, 100]
            elif ext == 'png':
                params = [cv2.IMWRITE_PNG_COMPRESSION, 0]
            
            success = cv2.imwrite(file_path, bgr_arr, params)
            if not success:
                return UsbServiceResult(False, f"OpenCV 写入文件失败: {file_path}")
                
            return UsbServiceResult(True, f"图片已保存: {file_path}")
        except Exception as e:
            return UsbServiceResult(False, f"保存 USB 图片失败: {e}")

    def _capture_loop(self) -> None:
        while self._running and self._cap:
            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            
            h, w = frame.shape[:2]
            self._frame_counter += 1
            
            # Keep as BGR for frame_poller.py compatibility (Format_BGR888)
            frame_bytes = frame.tobytes()
            
            view = UsbFrameView(
                width=w,
                height=h,
                frame_number=self._frame_counter,
                pixel_type=0, # Placeholder
                data=frame_bytes,
                byte_count=len(frame_bytes)
            )
            
            with self._lock:
                self._latest_frame = view
            
            # Yield some time to other threads
            time.sleep(0.005)
