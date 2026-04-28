from __future__ import annotations

from math import cos, pi, sin

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def build_icon(name: str, color: str, size: int = 18) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)

    match name:
        case "theme":
            _draw_theme_icon(painter, size)
        case "language":
            _draw_language_icon(painter, size)
        case "help":
            _draw_help_icon(painter, size)
        case "connect":
            _draw_connect_icon(painter, size)
        case "disconnect":
            _draw_disconnect_icon(painter, size)
        case "play":
            _draw_play_icon(painter, size)
        case "stop":
            _draw_stop_icon(painter, size)
        case "save":
            _draw_save_icon(painter, size)
        case "open":
            _draw_open_icon(painter, size)
        case "reset":
            _draw_reset_icon(painter, size)
        case "refresh":
            _draw_refresh_icon(painter, size)
        case "roi":
            _draw_roi_icon(painter, size)
        case "measure":
            _draw_measure_icon(painter, size)
        case "crosshair":
            _draw_crosshair_icon(painter, size)
        case _:
            _draw_placeholder_icon(painter, size)

    painter.end()
    return QIcon(pixmap)


def _draw_theme_icon(painter: QPainter, size: int) -> None:
    painter.drawArc(QRectF(3, 3, size - 6, size - 6), 35 * 16, 290 * 16)
    painter.drawLine(QPointF(size * 0.68, size * 0.18), QPointF(size * 0.82, size * 0.08))


def _draw_language_icon(painter: QPainter, size: int) -> None:
    painter.drawRoundedRect(QRectF(3, 3, size - 6, size - 6), 4, 4)
    painter.drawLine(QPointF(size * 0.28, size * 0.42), QPointF(size * 0.72, size * 0.42))
    painter.drawLine(QPointF(size * 0.50, size * 0.25), QPointF(size * 0.50, size * 0.75))
    painter.drawLine(QPointF(size * 0.34, size * 0.62), QPointF(size * 0.66, size * 0.62))


def _draw_help_icon(painter: QPainter, size: int) -> None:
    painter.drawEllipse(QRectF(2.5, 2.5, size - 5, size - 5))
    path = QPainterPath()
    path.moveTo(size * 0.38, size * 0.38)
    path.quadTo(size * 0.42, size * 0.24, size * 0.58, size * 0.28)
    path.quadTo(size * 0.72, size * 0.34, size * 0.64, size * 0.48)
    path.quadTo(size * 0.58, size * 0.58, size * 0.50, size * 0.61)
    painter.drawPath(path)
    painter.drawPoint(QPointF(size * 0.50, size * 0.77))


def _draw_connect_icon(painter: QPainter, size: int) -> None:
    painter.drawRoundedRect(QRectF(2.8, 5.5, size * 0.36, size * 0.28), 3, 3)
    painter.drawRoundedRect(QRectF(size * 0.61, size * 0.47, size * 0.20, size * 0.20), 2, 2)
    painter.drawLine(QPointF(size * 0.38, size * 0.50), QPointF(size * 0.58, size * 0.50))
    painter.drawLine(QPointF(size * 0.52, size * 0.44), QPointF(size * 0.58, size * 0.50))
    painter.drawLine(QPointF(size * 0.52, size * 0.56), QPointF(size * 0.58, size * 0.50))


def _draw_disconnect_icon(painter: QPainter, size: int) -> None:
    painter.drawRoundedRect(QRectF(2.8, 5.5, size * 0.36, size * 0.28), 3, 3)
    painter.drawLine(QPointF(size * 0.40, size * 0.50), QPointF(size * 0.63, size * 0.50))
    painter.drawLine(QPointF(size * 0.63, size * 0.36), QPointF(size * 0.80, size * 0.64))
    painter.drawLine(QPointF(size * 0.80, size * 0.36), QPointF(size * 0.63, size * 0.64))


def _draw_play_icon(painter: QPainter, size: int) -> None:
    path = QPainterPath()
    path.moveTo(size * 0.34, size * 0.24)
    path.lineTo(size * 0.74, size * 0.50)
    path.lineTo(size * 0.34, size * 0.76)
    path.closeSubpath()
    painter.drawPath(path)


def _draw_stop_icon(painter: QPainter, size: int) -> None:
    painter.drawRoundedRect(QRectF(size * 0.28, size * 0.28, size * 0.44, size * 0.44), 3, 3)


def _draw_save_icon(painter: QPainter, size: int) -> None:
    painter.drawRoundedRect(QRectF(3, 3, size - 6, size - 6), 3, 3)
    painter.drawRect(QRectF(size * 0.30, size * 0.26, size * 0.40, size * 0.18))
    painter.drawLine(QPointF(size * 0.32, size * 0.68), QPointF(size * 0.68, size * 0.68))


def _draw_open_icon(painter: QPainter, size: int) -> None:
    path = QPainterPath()
    path.moveTo(size * 0.18, size * 0.42)
    path.lineTo(size * 0.36, size * 0.42)
    path.lineTo(size * 0.44, size * 0.30)
    path.lineTo(size * 0.78, size * 0.30)
    path.lineTo(size * 0.72, size * 0.70)
    path.lineTo(size * 0.22, size * 0.70)
    path.closeSubpath()
    painter.drawPath(path)


def _draw_reset_icon(painter: QPainter, size: int) -> None:
    painter.drawArc(QRectF(3, 3, size - 6, size - 6), 40 * 16, 260 * 16)
    painter.drawLine(QPointF(size * 0.26, size * 0.34), QPointF(size * 0.18, size * 0.26))
    painter.drawLine(QPointF(size * 0.26, size * 0.34), QPointF(size * 0.14, size * 0.36))


def _draw_refresh_icon(painter: QPainter, size: int) -> None:
    painter.drawArc(QRectF(3, 3, size - 6, size - 6), 35 * 16, 220 * 16)
    painter.drawLine(QPointF(size * 0.72, size * 0.24), QPointF(size * 0.82, size * 0.22))
    painter.drawLine(QPointF(size * 0.72, size * 0.24), QPointF(size * 0.76, size * 0.12))
    painter.drawArc(QRectF(3, 3, size - 6, size - 6), 215 * 16, 220 * 16)
    painter.drawLine(QPointF(size * 0.28, size * 0.76), QPointF(size * 0.18, size * 0.78))
    painter.drawLine(QPointF(size * 0.28, size * 0.76), QPointF(size * 0.24, size * 0.88))


def _draw_roi_icon(painter: QPainter, size: int) -> None:
    painter.drawRect(QRectF(4, 4, size - 8, size - 8))
    corner = 4
    painter.drawLine(QPointF(4, 4 + corner), QPointF(4, 4))
    painter.drawLine(QPointF(4, 4), QPointF(4 + corner, 4))
    painter.drawLine(QPointF(size - 4 - corner, 4), QPointF(size - 4, 4))
    painter.drawLine(QPointF(size - 4, 4), QPointF(size - 4, 4 + corner))
    painter.drawLine(QPointF(4, size - 4 - corner), QPointF(4, size - 4))
    painter.drawLine(QPointF(4, size - 4), QPointF(4 + corner, size - 4))
    painter.drawLine(QPointF(size - 4 - corner, size - 4), QPointF(size - 4, size - 4))
    painter.drawLine(QPointF(size - 4, size - 4 - corner), QPointF(size - 4, size - 4))


def _draw_measure_icon(painter: QPainter, size: int) -> None:
    painter.drawLine(QPointF(size * 0.22, size * 0.72), QPointF(size * 0.76, size * 0.28))
    for offset in (0.00, 0.18, 0.36, 0.54):
        x = size * (0.26 + offset)
        y = size * (0.68 - offset)
        painter.drawLine(QPointF(x - 1, y + 3), QPointF(x + 2, y + 6))


def _draw_crosshair_icon(painter: QPainter, size: int) -> None:
    painter.drawLine(QPointF(size * 0.50, size * 0.18), QPointF(size * 0.50, size * 0.82))
    painter.drawLine(QPointF(size * 0.18, size * 0.50), QPointF(size * 0.82, size * 0.50))
    painter.drawEllipse(QRectF(size * 0.34, size * 0.34, size * 0.32, size * 0.32))


def _draw_placeholder_icon(painter: QPainter, size: int) -> None:
    painter.drawEllipse(QRectF(4, 4, size - 8, size - 8))
    for idx in range(3):
        angle = (idx / 3) * 2 * pi
        center = QPointF(size * 0.5 + cos(angle) * size * 0.16, size * 0.5 + sin(angle) * size * 0.16)
        painter.drawPoint(center)
