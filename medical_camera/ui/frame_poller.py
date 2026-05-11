from __future__ import annotations

import queue
from time import perf_counter
from PySide6.QtCore import QThread, Signal, Slot, QPointF, QRectF
from PySide6.QtGui import QImage
import cv2
import numpy as np

from medical_camera.services.recognition import RecognitionEngine


class RecognitionWorker(QThread):
    """独立识别线程：与采集线程完全解耦，通过队列接收最新帧。"""
    recognition_result_ready = Signal(object)

    def __init__(self, dispatcher, parent=None) -> None:
        super().__init__(parent)
        self._dispatcher = dispatcher
        self._engine = RecognitionEngine()
        # maxsize=1：队列满时丢弃旧帧，只保留最新帧，避免积压
        self._frame_queue: queue.Queue = queue.Queue(maxsize=1)
        self._running = False
        self._roi_rect: QRectF | None = None

    def set_roi_rect(self, rect: QRectF | None) -> None:
        self._roi_rect = rect

    def submit_frame(self, bgr_data: np.ndarray) -> None:
        """由采集线程调用，非阻塞：队列满则丢弃旧帧再放入新帧。"""
        try:
            self._frame_queue.put_nowait(bgr_data)
        except queue.Full:
            try:
                self._frame_queue.get_nowait()  # 丢弃积压的旧帧
            except queue.Empty:
                pass
            try:
                self._frame_queue.put_nowait(bgr_data)
            except queue.Full:
                pass

    def stop(self) -> None:
        self._running = False
        # 放一个 None 让线程从阻塞的 get() 中唤醒
        try:
            self._frame_queue.put_nowait(None)
        except queue.Full:
            pass
        self.wait()

    def run(self) -> None:
        self._running = True
        while self._running:
            try:
                bgr_data = self._frame_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if bgr_data is None:  # 停止信号
                break

            state = self._dispatcher.state
            if not state.recognizing:
                continue

            roi_mask = None
            manual_fov_circle = None
            if state.detection_scope == "three_point":
                # Manual circle IS the FOV - no roi_mask needed
                manual_fov_circle = state.manual_fov_circle
            elif state.detection_scope == "roi" and self._roi_rect:
                h, w = bgr_data.shape[:2]
                roi_mask = np.zeros((h, w), dtype=np.uint8)
                x1 = int(self._roi_rect.left() * w)
                y1 = int(self._roi_rect.top() * h)
                x2 = int(self._roi_rect.right() * w)
                y2 = int(self._roi_rect.bottom() * h)
                cv2.rectangle(roi_mask, (x1, y1), (x2, y2), 255, -1)

            res = self._engine.process_frame(
                bgr_data,
                state.field_shape,
                threshold=int(state.recognition_threshold),
                roi_mask=roi_mask,
                pattern_mode=state.pattern_mode,
                shape_threshold=int(state.shape_threshold),
                manual_fov_circle=manual_fov_circle,
            )
            self.recognition_result_ready.emit(res)


class HikvisionFramePoller(QThread):
    # Signals: (QImage, frame_number, pixel_type)
    image_ready = Signal(QImage, int, int)
    stats_ready = Signal(float, int)
    probe_result_ready = Signal(object)  # dict with R, G, B or Y

    def __init__(self, dispatcher, recognition_worker: RecognitionWorker, timeout_ms: int = 20) -> None:
        super().__init__()
        self._dispatcher = dispatcher
        self._recognition_worker = recognition_worker
        self._timeout_ms = timeout_ms
        self._running = False
        self._frame_count = 0
        self._last_stats_time = perf_counter()
        self._probe_point: QPointF | None = None  # Normalized
        self._probe_size = 11  # 11x11 area
        self._probe_paused = False

    def stop(self) -> None:
        self._running = False
        self.wait()

    def set_probe_point(self, pt: QPointF | None) -> None:
        self._probe_point = pt


    def set_probe_paused(self, paused: bool) -> None:
        self._probe_paused = paused

    def run(self) -> None:
        self._running = True
        self._frame_count = 0
        self._last_stats_time = perf_counter()
        self._last_emitted_frame_number = -1

        while self._running:
            frame = self._dispatcher.get_latest_frame(timeout_ms=self._timeout_ms)
            if frame is None or frame.frame_number == self._last_emitted_frame_number:
                self.msleep(5) # Prevent busy wait
                continue

            self._last_emitted_frame_number = frame.frame_number
            # Process image in background thread
            image, probe_res, bgr_data = self._process_frame(frame)
            if image:
                self.image_ready.emit(image, frame.frame_number, frame.pixel_type)
                if probe_res:
                    self.probe_result_ready.emit(probe_res)
                
                # 识别：非阻塞投递给独立识别线程
                if self._dispatcher.state.recognizing and bgr_data is not None:
                    self._recognition_worker.submit_frame(bgr_data.copy())

                self._frame_count += 1
                now = perf_counter()
                elapsed = now - self._last_stats_time
                if elapsed >= 1.0:
                    self.stats_ready.emit(self._frame_count / elapsed, frame.frame_number)
                    self._frame_count = 0
                    self._last_stats_time = now

    def _process_frame(self, frame) -> tuple[QImage | None, dict | None, np.ndarray | None]:
        data, width, height, byte_count = frame.data, frame.width, frame.height, frame.byte_count
        pixel_type = frame.pixel_type
        
        if not data or width <= 0 or height <= 0:
            return None, None

        pixel_count = width * height
        bgr = None
        mono_arr = None
        
        # 1. Convert to usable numpy array
        if byte_count == pixel_count:
            try:
                arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width))
                # Hikvision Bayer Formats
                # Hikvision Bayer Formats: Swap R and B by using 2RGB while display expects BGR
                if pixel_type == 0x01080008: bgr = cv2.cvtColor(arr, cv2.COLOR_BayerGR2RGB)
                elif pixel_type == 0x01080009: bgr = cv2.cvtColor(arr, cv2.COLOR_BayerRG2RGB)
                elif pixel_type == 0x0108000A: bgr = cv2.cvtColor(arr, cv2.COLOR_BayerGB2RGB)
                elif pixel_type == 0x0108000B: bgr = cv2.cvtColor(arr, cv2.COLOR_BayerBG2RGB)
                else:
                    mono_arr = arr
            except Exception:
                return None, None, None
        elif byte_count >= pixel_count * 3:
            # Assume RGB from camera, convert to BGR for internal processing
            arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))
            bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

        # 2. Handle Probe if active
        probe_res = None
        if self._probe_point and not self._probe_paused:
            px = int(self._probe_point.x() * width)
            py = int(self._probe_point.y() * height)
            s = self._probe_size // 2
            
            # Clamp to boundaries
            x1, x2 = max(0, px - s), min(width, px + s + 1)
            y1, y2 = max(0, py - s), min(height, py + s + 1)
            
            if bgr is not None:
                roi = bgr[y1:y2, x1:x2]
                avg = np.mean(roi, axis=(0, 1))
                probe_res = {"r": float(avg[2]), "g": float(avg[1]), "b": float(avg[0]), "type": "rgb"}
            elif mono_arr is not None:
                roi = mono_arr[y1:y2, x1:x2]
                avg = np.mean(roi)
                probe_res = {"y": float(avg), "type": "gray"}

        # 3. Build Final QImage
        out_bgr = None
        if bgr is not None:
            qimg = QImage(bgr.data, width, height, width * 3, QImage.Format.Format_BGR888).copy()
            out_bgr = bgr
        elif mono_arr is not None:
            # For display, normalize if needed or just use Grayscale8
            mono_8 = cv2.normalize(mono_arr, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            qimg = QImage(mono_8.data, width, height, width, QImage.Format.Format_Grayscale8).copy()
            out_bgr = cv2.cvtColor(mono_8, cv2.COLOR_GRAY2BGR)
        else:
            qimg = None
            
        return qimg, probe_res, out_bgr
