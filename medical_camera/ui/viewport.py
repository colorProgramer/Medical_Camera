from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal, QSizeF
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

import cv2
import numpy as np


class CameraViewport(QWidget):
    zoom_changed = Signal(float)
    roi_changed = Signal(object)       # Normalized QRectF or None
    fov_circle_defined = Signal(object) # dict {cx,cy,r} normalized or None
    mouse_moved = Signal(QPointF)      # Normalized point
    probe_paused_changed = Signal(bool)
    
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(720, 520)
        self._frame_pixmap: QPixmap | None = None
        self._frame_number: int | None = None
        self._display_fps: float | None = None
        
        # Zoom and Pan state
        self._zoom_factor = 1.0
        self._pan_offset = QPointF(0, 0)
        self._is_dragging = False
        self._drag_start = QPointF(0, 0)
        
        self._cached_clip_path = QPainterPath()
        self._probe_mode = False
        self._probe_paused = False
        # Interaction mode: "normal" | "roi" | "three_point"
        self._interaction_mode: str = "normal"
        self._roi_rect: QRectF | None = None
        self._active_handle: str | None = None  # 'tl','tr','bl','br','center'
        # Three-point circle state (persists across mode switches)
        self._fov_points: list[QPointF] = []   # normalized, max 3
        self._manual_fov_circle: dict | None = None  # {cx,cy,r} normalized
        # Whether three_point scope is selected (controls display, independent of interaction)
        self._three_point_scope: bool = False
        self._recognition_res: Any | None = None
        self._fov_n_percent = 70.0
        self._overlay_config = {
            "show_fov_boundary": True,
            "show_fov_70": True,
            "show_roi_rect": True,
            "show_fov_center": True,
            "show_screen_center": True,
        }

        # Performance cache
        self._render_rect = QRectF()
        self._render_dirty = True

        self.setMouseTracking(True)

    def set_roi_mode(self, enabled: bool) -> None:
        if enabled:
            self._interaction_mode = "roi"
            self._probe_mode = False
        elif self._interaction_mode == "roi":
            self._interaction_mode = "normal"
        self.setCursor(Qt.CrossCursor if self._interaction_mode != "normal" else Qt.ArrowCursor)
        self.update()

    def set_three_point_mode(self, enabled: bool) -> None:
        """Activate/deactivate three-point INTERACTION mode (requires roi_switch ON).
        Data persists across switches. Display is controlled by set_three_point_scope."""
        if enabled:
            self._interaction_mode = "three_point"
            self._probe_mode = False
            self.setCursor(Qt.CrossCursor)
            # Re-emit current circle if already defined
            self.fov_circle_defined.emit(self._manual_fov_circle)
        else:
            if self._interaction_mode == "three_point":
                self._interaction_mode = "normal"
            self.setCursor(Qt.ArrowCursor)
        self.update()

    def set_three_point_scope(self, active: bool) -> None:
        """Set whether three_point scope is selected (controls marker/circle display)."""
        self._three_point_scope = active
        self.update()

    def set_probe_mode(self, enabled: bool) -> None:
        self._probe_mode = enabled
        if enabled:
            self._interaction_mode = "normal"
        self.setCursor(Qt.CrossCursor if enabled else Qt.ArrowCursor)
        self.update()

    def clear_fov_points(self) -> None:
        """Reset three-point circle (right-click behavior)."""
        self._fov_points = []
        self._manual_fov_circle = None
        self.fov_circle_defined.emit(None)
        self.update()

    def set_roi_rect(self, rect_norm: Any | None) -> None:
        self._roi_rect = rect_norm
        self.update()

    def set_recognition_result(self, res: Any | None) -> None:
        self._recognition_res = res
        self.update()

    def set_overlay_config(self, config: dict) -> None:
        self._overlay_config.update(config)
        self.update()

    def set_fov_n_percent(self, value: float) -> None:
        self._fov_n_percent = value
        self.update()

    def _update_render_rect(self) -> None:
        if not self._frame_pixmap:
            self._render_rect = QRectF()
            return
            
        outer = self.rect().adjusted(12, 12, -12, -12)
        image_rect = QRectF(outer).adjusted(22, 22, -22, -22)
        
        pix_size = self._frame_pixmap.size()
        ratio = min(image_rect.width() / pix_size.width(), image_rect.height() / pix_size.height())
        final_w = pix_size.width() * ratio * self._zoom_factor
        final_h = pix_size.height() * ratio * self._zoom_factor
        
        self._render_rect = QRectF(
            image_rect.center().x() - final_w / 2 + self._pan_offset.x(),
            image_rect.center().y() - final_h / 2 + self._pan_offset.y(),
            final_w,
            final_h,
        )
        self._render_dirty = False

    def set_image(self, image: QImage, frame_number: int) -> None:
        self._frame_pixmap = QPixmap.fromImage(image)
        self._frame_number = frame_number
        self._render_dirty = True
        self.update()

    def set_display_fps(self, fps: float) -> None:
        self._display_fps = fps
        self.update()

    def clear_frame(self) -> None:
        self._frame_pixmap = None
        self._frame_number = None
        self._display_fps = None
        self.update()

    def _viewport_to_norm(self, pos: QPointF) -> QPointF:
        if self._render_dirty: self._update_render_rect()
        r = self._render_rect
        if r.width() == 0 or r.height() == 0:
            return QPointF(0, 0)
        return QPointF((pos.x() - r.left()) / r.width(), (pos.y() - r.top()) / r.height())

    def _norm_to_viewport(self, norm_pos: QPointF) -> QPointF:
        if self._render_dirty: self._update_render_rect()
        r = self._render_rect
        return QPointF(r.left() + norm_pos.x() * r.width(), r.top() + norm_pos.y() * r.height())

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if not self._frame_pixmap:
            return

        if self._render_dirty: self._update_render_rect()
        render_rect = self._render_rect

        pos = event.position()
        clamped_pos = QPointF(
            max(render_rect.left(), min(pos.x(), render_rect.right())),
            max(render_rect.top(), min(pos.y(), render_rect.bottom()))
        )

        if self._interaction_mode == "roi":
            if event.button() == Qt.RightButton:
                self._roi_rect = None
                self.roi_changed.emit(None)
                self.update()
                return

            norm_pos = self._viewport_to_norm(clamped_pos)

            if self._roi_rect:
                h_size = 12
                tl = self._norm_to_viewport(self._roi_rect.topLeft())
                tr = self._norm_to_viewport(self._roi_rect.topRight())
                bl = self._norm_to_viewport(self._roi_rect.bottomLeft())
                br = self._norm_to_viewport(self._roi_rect.bottomRight())

                if (pos - tl).manhattanLength() < h_size: self._active_handle = 'tl'
                elif (pos - tr).manhattanLength() < h_size: self._active_handle = 'tr'
                elif (pos - bl).manhattanLength() < h_size: self._active_handle = 'bl'
                elif (pos - br).manhattanLength() < h_size: self._active_handle = 'br'
                elif self._norm_to_viewport_rect(self._roi_rect).contains(pos):
                    self._active_handle = 'center'
                else:
                    if render_rect.contains(pos):
                        self._roi_rect = QRectF(norm_pos, QSizeF(0, 0))
                        self._active_handle = 'br'
            else:
                if render_rect.contains(pos):
                    self._roi_rect = QRectF(norm_pos, QSizeF(0, 0))
                    self._active_handle = 'br'

            self._drag_start = norm_pos
            self.update()

        elif self._interaction_mode == "three_point":
            norm_pos = self._viewport_to_norm(clamped_pos)

            if event.button() == Qt.RightButton:
                # Right-click: reset all points
                self._fov_points = []
                self._manual_fov_circle = None
                self.fov_circle_defined.emit(None)
                self.update()
                return

            if event.button() == Qt.LeftButton:
                HIT_PX = 15.0
                # Check if clicking near an existing point → delete it
                for i, pt in enumerate(self._fov_points):
                    vp = self._norm_to_viewport(pt)
                    if (clamped_pos - vp).manhattanLength() < HIT_PX:
                        self._fov_points.pop(i)
                        self._manual_fov_circle = None
                        self.fov_circle_defined.emit(None)
                        self.update()
                        return
                # Add point only if < 3
                if len(self._fov_points) < 3:
                    self._fov_points.append(norm_pos)
                    if len(self._fov_points) == 3:
                        # Fit circle in VIEWPORT PIXEL space to avoid aspect-ratio distortion
                        rr = self._render_rect
                        vp_pts = [self._norm_to_viewport(p) for p in self._fov_points]
                        circle_vp = self._fit_circle_3pts(*vp_pts)
                        if circle_vp and rr.width() > 0 and rr.height() > 0:
                            self._manual_fov_circle = {
                                'cx': (circle_vp['cx'] - rr.left()) / rr.width(),
                                'cy': (circle_vp['cy'] - rr.top()) / rr.height(),
                                'r': circle_vp['r'] / rr.width(),  # radius as fraction of viewport width
                            }
                        else:
                            self._manual_fov_circle = None
                        self.fov_circle_defined.emit(self._manual_fov_circle)
                    self.update()
                # else: already 3 points and not near any → do nothing

        elif self._probe_mode:
            if event.button() == Qt.LeftButton:
                self._probe_paused = True
                self.probe_paused_changed.emit(True)
        else:
            if event.button() == Qt.LeftButton:
                self._is_dragging = True
                self._drag_start = pos
                self.setCursor(Qt.ClosedHandCursor)
        event.accept()

    def _norm_to_viewport_rect(self, norm_rect: QRectF) -> QRectF:
        tl = self._norm_to_viewport(norm_rect.topLeft())
        br = self._norm_to_viewport(norm_rect.bottomRight())
        return QRectF(tl, br).normalized()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if not self._frame_pixmap:
            return
            
        if self._render_dirty: self._update_render_rect()
        render_rect = self._render_rect
        pos = event.position()
        
        if self._interaction_mode == "roi":
            if not event.buttons() & Qt.LeftButton:
                if self._roi_rect:
                    h_size = 12
                    tl = self._norm_to_viewport(self._roi_rect.topLeft())
                    tr = self._norm_to_viewport(self._roi_rect.topRight())
                    bl = self._norm_to_viewport(self._roi_rect.bottomLeft())
                    br = self._norm_to_viewport(self._roi_rect.bottomRight())

                    if (pos - tl).manhattanLength() < h_size or (pos - br).manhattanLength() < h_size:
                        self.setCursor(Qt.SizeFDiagCursor)
                    elif (pos - tr).manhattanLength() < h_size or (pos - bl).manhattanLength() < h_size:
                        self.setCursor(Qt.SizeBDiagCursor)
                    elif self._norm_to_viewport_rect(self._roi_rect).contains(pos):
                        self.setCursor(Qt.OpenHandCursor)
                    else:
                        self.setCursor(Qt.CrossCursor)
                else:
                    self.setCursor(Qt.CrossCursor)

            if self._active_handle:
                clamped_pos = QPointF(
                    max(render_rect.left(), min(pos.x(), render_rect.right())),
                    max(render_rect.top(), min(pos.y(), render_rect.bottom()))
                )
                norm_pos = self._viewport_to_norm(clamped_pos)
                
                if self._active_handle == 'tl': self._roi_rect.setTopLeft(norm_pos)
                elif self._active_handle == 'tr': self._roi_rect.setTopRight(norm_pos)
                elif self._active_handle == 'bl': self._roi_rect.setBottomLeft(norm_pos)
                elif self._active_handle == 'br': self._roi_rect.setBottomRight(norm_pos)
                elif self._active_handle == 'center':
                    delta = norm_pos - self._drag_start
                    new_rect = self._roi_rect.translated(delta)
                    if new_rect.left() >= 0 and new_rect.right() <= 1 and \
                       new_rect.top() >= 0 and new_rect.bottom() <= 1:
                        self._roi_rect = new_rect
                    self._drag_start = norm_pos
                
                self._roi_rect = self._roi_rect.normalized()
                self.update()
                self.roi_changed.emit(self._roi_rect)
        elif self._probe_mode:
            if not self._probe_paused:
                if render_rect.contains(pos):
                    norm_pos = self._viewport_to_norm(pos)
                    self.mouse_moved.emit(norm_pos)
                else:
                    self.mouse_moved.emit(None)
        elif self._is_dragging:
            delta = pos - self._drag_start
            self._pan_offset += delta
            self._drag_start = pos
            self._render_dirty = True
            self.update()
        event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._is_dragging = False
        self._probe_paused = False
        self.probe_paused_changed.emit(False)
        self._active_handle = None
        if self._interaction_mode == "normal":
            self.setCursor(Qt.ArrowCursor)
        event.accept()

    def _draw_overlay(self, painter: QPainter, image_rect: QRectF) -> None:
        if not self._frame_pixmap:
            return

        if self._render_dirty: self._update_render_rect()

        # 1. Screen center star lines
        if self._overlay_config.get("show_screen_center", True):
            self._draw_screen_center(painter, image_rect)

        # 2. ROI box — only visible in roi mode
        if self._interaction_mode == "roi" and self._roi_rect:
            self._draw_roi(painter, image_rect)

        # 3. Three-point markers/circle — visible when scope is three_point (regardless of interaction)
        if self._three_point_scope:
            self._draw_fov_points(painter, image_rect)

        # 4. Recognition results
        if self._recognition_res:
            self._draw_recognition(painter, image_rect)

    def _draw_screen_center(self, painter: QPainter, image_rect: QRectF) -> None:
        if not self._frame_pixmap:
            return
            
        if self._render_dirty: self._update_render_rect()
        render_rect = self._render_rect
        
        painter.save()
        painter.setClipRect(render_rect)
        
        pen = QPen(QColor(255, 255, 255, 80), 1, Qt.DashLine)
        painter.setPen(pen)
        
        cx, cy = render_rect.center().x(), render_rect.center().y()
        
        painter.drawLine(QPointF(cx, render_rect.top()), QPointF(cx, render_rect.bottom()))
        painter.drawLine(QPointF(render_rect.left(), cy), QPointF(render_rect.right(), cy))
        
        L = max(render_rect.width(), render_rect.height())
        painter.drawLine(QPointF(cx - L, cy - L), QPointF(cx + L, cy + L))
        painter.drawLine(QPointF(cx - L, cy + L), QPointF(cx + L, cy - L))
        painter.restore()

    def _draw_recognition(self, painter: QPainter, image_rect: QRectF) -> None:
        res = self._recognition_res
        if not res or not res.fov_data:
            return
            
        painter.save()
        fov = res.fov_data
        fw, fh = self._frame_pixmap.width(), self._frame_pixmap.height()
        
        fov_cx, fov_cy, fov_base_r = None, None, None
        if fov['type'] == 'circle' and 'center' in fov:
            fov_cx, fov_cy = fov['center']
            fov_base_r = fov['radius']
        elif fov['type'] in ('rect', 'rectangle') and 'rect' in fov:
            (rcx, rcy), (rw_box, rh_box), _ = fov['rect']
            fov_cx, fov_cy = rcx, rcy
            fov_base_r = np.hypot(rw_box, rh_box) / 2
        
        # 1. FOV Boundary (Requirement 1)
        if self._overlay_config.get("show_fov_boundary", True):
            pen = QPen(Qt.green, 2, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            
            if fov['type'] == 'circle' and 'center' in fov:
                cx, cy = fov['center']
                r = fov['radius']
                pt = self._norm_to_viewport(QPointF(cx / fw, cy / fh))
                rw = r * self._render_rect.width() / fw
                painter.drawEllipse(pt, rw, rw)
            elif fov['type'] in ('rect', 'rectangle') and 'box' in fov:
                pts = [self._norm_to_viewport(QPointF(px / fw, py / fh)) for px, py in fov['box']]
                painter.drawPolygon(pts)

        # 2. FOV Center Cross - CLIPPED to FOV (Requirement 5)
        if self._overlay_config.get("show_fov_center", True) and 'center' in fov:
            painter.save()
            # Create clipping path for FOV
            clip_path = QPainterPath()
            if fov['type'] == 'circle':
                cx, cy = fov['center']
                r = fov['radius']
                pt = self._norm_to_viewport(QPointF(cx / fw, cy / fh))
                rw = r * self._render_rect.width() / fw
                clip_path.addEllipse(pt, rw, rw)
            elif fov['type'] in ('rect', 'rectangle') and 'box' in fov:
                pts = [self._norm_to_viewport(QPointF(px / fw, py / fh)) for px, py in fov['box']]
                clip_path.addPolygon(pts)
            
            painter.setClipPath(clip_path)
            
            # Draw cross lines across the WHOLE image but clipped
            cx_fov, cy_fov = fov['center']
            pt_fov = self._norm_to_viewport(QPointF(cx_fov / fw, cy_fov / fh))
            
            painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))
            painter.drawLine(QPointF(pt_fov.x(), image_rect.top()), QPointF(pt_fov.x(), image_rect.bottom()))
            painter.drawLine(QPointF(image_rect.left(), pt_fov.y()), QPointF(image_rect.right(), pt_fov.y()))
            painter.restore()

        # 3. N% FOV circle (Requirement 3)
        if self._overlay_config.get("show_fov_n", True):
            if fov_cx is not None and fov_base_r is not None:
                r = fov_base_r * (self._fov_n_percent / 100.0)
                pt = self._norm_to_viewport(QPointF(fov_cx / fw, fov_cy / fh))
                rw_render = r * self._render_rect.width() / fw
                painter.setPen(QPen(Qt.yellow, 1, Qt.DotLine))
                painter.drawEllipse(pt, rw_render, rw_render)
                painter.setPen(Qt.yellow)
                painter.drawText(pt + QPointF(rw_render + 5, 0), f"{self._fov_n_percent:.0f}%")

        # 4. Intra-FOV Ellipses (Requirement 2)
        if self._overlay_config.get("show_ellipses", True) and res.ellipses:
            colors = [QColor("#ff4d4f"), QColor("#1890ff"), QColor("#ffec3d"), QColor("#eb2f96"), QColor("#13c2c2")]
            font = painter.font()
            font.setPixelSize(14)
            font.setBold(True)
            painter.setFont(font)
            
            for i, el in enumerate(res.ellipses):
                col = colors[i % len(colors)]
                ecx, ecy = el['center']
                ew, eh = el['axes']
                angle = el['angle']
                
                pt = self._norm_to_viewport(QPointF(ecx / fw, ecy / fh))
                rw = (ew / 2) * self._render_rect.width() / fw
                rh = (eh / 2) * self._render_rect.height() / fh
                
                painter.save()
                painter.setPen(QPen(col, 2))
                painter.translate(pt)
                painter.rotate(angle)
                painter.drawEllipse(QPointF(0, 0), rw, rh)
                # Cross inside ellipse
                painter.setPen(QPen(col, 1))
                painter.drawLine(QPointF(-rw, 0), QPointF(rw, 0))
                painter.drawLine(QPointF(0, -rh), QPointF(0, rh))
                painter.restore()
                
                painter.setBrush(col)
                painter.drawEllipse(pt, 3, 3)
                painter.setBrush(Qt.NoBrush)
                painter.setPen(col)
                
                label = f"#{i+1}"
                if fov_cx is not None and fov_base_r is not None:
                    dx = ecx - fov_cx
                    dy = ecy - fov_cy
                    d = np.hypot(dx, dy)
                    if d < fov_base_r * 0.15:
                        label = "c"
                    else:
                        deg = np.degrees(np.arctan2(dy, dx))
                        if -22.5 <= deg < 22.5: label = "r"
                        elif 22.5 <= deg < 67.5: label = "rb"
                        elif 67.5 <= deg < 112.5: label = "b"
                        elif 112.5 <= deg < 157.5: label = "lb"
                        elif deg >= 157.5 or deg < -157.5: label = "l"
                        elif -157.5 <= deg < -112.5: label = "lt"
                        elif -112.5 <= deg < -67.5: label = "t"
                        elif -67.5 <= deg < -22.5: label = "rt"

                painter.drawText(pt + QPointF(15, -15), label)
        painter.restore()

    def _draw_roi(self, painter: QPainter, image_rect: QRectF) -> None:
        v_roi = self._norm_to_viewport_rect(self._roi_rect)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#409eff"), 2, Qt.SolidLine))
        painter.drawRect(v_roi)
        # Corner handles
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#409eff"), 1.5))
        h_size = 8
        for pt in [v_roi.topLeft(), v_roi.topRight(), v_roi.bottomLeft(), v_roi.bottomRight()]:
            painter.drawRect(QRectF(pt.x() - h_size / 2, pt.y() - h_size / 2, h_size, h_size))

    @staticmethod
    def _fit_circle_3pts(p1: QPointF, p2: QPointF, p3: QPointF) -> dict | None:
        import math
        ax, ay = p1.x(), p1.y()
        bx, by = p2.x(), p2.y()
        cx, cy = p3.x(), p3.y()
        d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if abs(d) < 1e-10:
            return None
        ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
        uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
        r = ((ax - ux) ** 2 + (ay - uy) ** 2) ** 0.5
        if not (math.isfinite(ux) and math.isfinite(uy) and math.isfinite(r)):
            return None
        if r <= 0:
            return None
        return {'cx': ux, 'cy': uy, 'r': r}

    def _draw_fov_points(self, painter: QPainter, image_rect: QRectF) -> None:
        """Draw three-point circle markers and fitted circle preview."""
        if not self._frame_pixmap:
            return
        painter.save()

        # Draw fitted circle ONLY when show_fov_boundary is checked
        if self._manual_fov_circle and self._overlay_config.get("show_fov_boundary", False):
            import math
            fc = self._manual_fov_circle
            if not (math.isfinite(fc.get('cx', 0)) and math.isfinite(fc.get('cy', 0)) and math.isfinite(fc.get('r', 0))):
                painter.restore()
                return
            if fc['r'] <= 0:
                painter.restore()
                return
            pt = self._norm_to_viewport(QPointF(fc['cx'], fc['cy']))
            r_px = fc['r'] * self._render_rect.width()
            if not (math.isfinite(pt.x()) and math.isfinite(pt.y()) and math.isfinite(r_px)):
                painter.restore()
                return
            painter.setPen(QPen(QColor("#00e5ff"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(pt, r_px, r_px)

        # Draw each point as × with label
        COLORS = [QColor("#ff6b6b"), QColor("#ffd93d"), QColor("#6bcb77")]
        S = 7
        for i, pt_norm in enumerate(self._fov_points):
            vp = self._norm_to_viewport(pt_norm)
            col = COLORS[i]
            painter.setPen(QPen(col, 2))
            painter.drawLine(QPointF(vp.x() - S, vp.y() - S), QPointF(vp.x() + S, vp.y() + S))
            painter.drawLine(QPointF(vp.x() - S, vp.y() + S), QPointF(vp.x() + S, vp.y() - S))
            font = painter.font()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(col)
            painter.drawText(QPointF(vp.x() + 10, vp.y() - 8), f"P{i + 1}")

        # Hint text — only show in interaction mode (roi_switch ON)
        if self._interaction_mode == "three_point":
            font = painter.font()
            font.setPixelSize(13)
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255, 200))
            n = len(self._fov_points)
            if n < 3:
                hint = f"点击圆弧边缘放置点 {n + 1}/3   右键重置"
            else:
                hint = "三点定圆完成   点击已有点可删除   右键重置"
            painter.drawText(image_rect.adjusted(10, 10, 0, 0), hint)

        painter.restore()

    def zoom_in(self, focal_point: QPointF | None = None) -> float:
        return self._apply_zoom(1.2, focal_point)

    def zoom_out(self, focal_point: QPointF | None = None) -> float:
        return self._apply_zoom(1/1.2, focal_point)

    def _apply_zoom(self, scale: float, focal_point: QPointF | None = None) -> float:
        old_zoom = self._zoom_factor
        self._zoom_factor *= scale
        
        if self._zoom_factor > 10.0: self._zoom_factor = 10.0
        if self._zoom_factor < 0.1: self._zoom_factor = 0.1
            
        actual_scale = self._zoom_factor / old_zoom
        if focal_point:
            v_center = self.rect().center()
            rel_focal = focal_point - v_center - self._pan_offset
            self._pan_offset -= rel_focal * (actual_scale - 1)
            
        self._render_dirty = True
        self.update()
        self.zoom_changed.emit(self._zoom_factor)
        return self._zoom_factor

    def reset_view(self) -> None:
        self._zoom_factor = 1.0
        self._pan_offset = QPointF(0, 0)
        self._render_dirty = True
        self.update()
        self.zoom_changed.emit(self._zoom_factor)

    def reset_all(self) -> None:
        """Complete reset of all interactive states."""
        self.reset_view()
        self._roi_rect = None
        self._fov_points = []
        self._manual_fov_circle = None
        self._interaction_mode = "normal"
        self._probe_mode = False
        self._probe_paused = False
        self._recognition_res = None
        self.update()

    def wheelEvent(self, event) -> None:  # noqa: N802
        delta = event.angleDelta().y()
        focal_point = event.position()
        if delta > 0: self.zoom_in(focal_point)
        else: self.zoom_out(focal_point)
        event.accept()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        if self._zoom_factor != 1.0:
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

        outer = self.rect().adjusted(12, 12, -12, -12)
        painter.fillRect(self.rect(), QColor("#edf1f5"))
        painter.setBrush(QColor("#19212b"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(outer), 20, 20)

        image_rect = QRectF(outer).adjusted(22, 22, -22, -22)
        painter.save()
        painter.setClipRect(image_rect)

        if self._frame_pixmap is None:
            painter.setPen(QColor("#ffffff"))
            painter.drawText(image_rect.adjusted(18, 18, 0, 0), "实时画面（等待相机帧）")
        else:
            if self._render_dirty: self._update_render_rect()
            painter.drawPixmap(self._render_rect.toRect(), self._frame_pixmap)
            
            painter.setPen(QColor("#ffffff"))
            text = f"实时画面  #{self._frame_number}  {self._display_fps or 0:.1f} FPS"
            painter.drawText(image_rect.adjusted(18, 18, 500, 24), text)
        
        painter.restore()
        self._draw_overlay(painter, image_rect)

    def resizeEvent(self, event) -> None:  # noqa: N802
        self._render_dirty = True
        super().resizeEvent(event)


FakeViewport = CameraViewport
