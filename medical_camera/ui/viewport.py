from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class CameraViewport(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(720, 520)
        self._frame_pixmap: QPixmap | None = None
        self._frame_number: int | None = None
        self._display_fps: float | None = None

    def set_frame(self, data: bytes, width: int, height: int, byte_count: int, frame_number: int, pixel_type: int = 0) -> None:
        image = self._build_image(data, width, height, byte_count, pixel_type)
        if image is None:
            return
        self._frame_pixmap = QPixmap.fromImage(image)
        self._frame_number = frame_number
        self.update()

    def set_display_fps(self, fps: float) -> None:
        self._display_fps = fps
        self.update()

    def clear_frame(self) -> None:
        self._frame_pixmap = None
        self._frame_number = None
        self._display_fps = None
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        outer = self.rect().adjusted(12, 12, -12, -12)
        painter.fillRect(self.rect(), QColor("#edf1f5"))

        frame_path = QPainterPath()
        frame_path.addRoundedRect(QRectF(outer), 20, 20)
        painter.fillPath(frame_path, QColor("#19212b"))

        image_rect = QRectF(outer).adjusted(22, 22, -22, -22)
        if self._frame_pixmap is None:
            self._draw_placeholder(painter, image_rect)
        else:
            self._draw_frame(painter, image_rect)

        self._draw_overlay(painter, image_rect)

    def _draw_frame(self, painter: QPainter, image_rect: QRectF) -> None:
        assert self._frame_pixmap is not None
        scaled = self._frame_pixmap.scaled(
            image_rect.size().toSize(),
            Qt.KeepAspectRatio,
            Qt.FastTransformation,
        )
        target = QRectF(
            image_rect.center().x() - scaled.width() / 2,
            image_rect.center().y() - scaled.height() / 2,
            scaled.width(),
            scaled.height(),
        )
        painter.drawPixmap(target.toRect(), scaled)
        painter.setPen(QColor("#ffffff"))
        text = "实时画面"
        if self._frame_number is not None:
            text = f"{text}  #{self._frame_number}"
        if self._display_fps is not None:
            text = f"{text}  {self._display_fps:.1f} FPS"
        painter.drawText(QRectF(image_rect.left() + 18, image_rect.top() + 18, 240, 24), text)

    def _draw_placeholder(self, painter: QPainter, image_rect: QRectF) -> None:
        painter.setPen(QColor("#ffffff"))
        painter.drawText(QRectF(image_rect.left() + 18, image_rect.top() + 18, 260, 24), "实时画面（等待相机帧）")

    def _draw_overlay(self, painter: QPainter, image_rect: QRectF) -> None:
        """移除硬编码的默认绘图内容"""
        pass

    @staticmethod
    def _build_image(data: bytes, width: int, height: int, byte_count: int, pixel_type: int = 0) -> QImage | None:
        if width <= 0 or height <= 0 or byte_count <= 0 or not data:
            return None

        import cv2
        import numpy as np

        pixel_count = width * height
        if byte_count == pixel_count:
            arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width))
            
            # Check Bayer formats (using BayerXX2BGR to flip R and B channels)
            if pixel_type == 0x01080008:  # BayerGR8
                bgr = cv2.cvtColor(arr, cv2.COLOR_BayerGR2BGR)
                return QImage(bgr.data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
            elif pixel_type == 0x01080009:  # BayerRG8
                bgr = cv2.cvtColor(arr, cv2.COLOR_BayerRG2BGR)
                return QImage(bgr.data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
            elif pixel_type == 0x0108000A:  # BayerGB8
                bgr = cv2.cvtColor(arr, cv2.COLOR_BayerGB2BGR)
                return QImage(bgr.data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
            elif pixel_type == 0x0108000B:  # BayerBG8
                bgr = cv2.cvtColor(arr, cv2.COLOR_BayerBG2BGR)
                return QImage(bgr.data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
            else:
                # Default to Mono8. Use OpenCV for fast stretching if needed.
                mono = cv2.normalize(arr, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                return QImage(mono.data, width, height, width, QImage.Format.Format_Grayscale8).copy()

        if byte_count >= pixel_count * 3:
            return QImage(data, width, height, width * 3, QImage.Format.Format_RGB888).copy()

        return None


FakeViewport = CameraViewport
