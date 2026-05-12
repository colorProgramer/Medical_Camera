from __future__ import annotations
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Any

@dataclass
class RecognitionResult:
    fov_type: str = "circle"
    fov_data: dict = None  # Contains center, radius or box
    ellipses: list[dict] = None
    timestamp: float = 0.0

class RecognitionEngine:
    def __init__(self) -> None:
        self.config = {
            "n_ellipses": 5,
            "min_ellipse_area": 300,
            "max_ellipse_area_ratio": 0.35,
            "min_circularity": 0.15,
            "fov_threshold": 20,
            "fov_morph_k": 7,
            "blur_ksize": 5,
            "canny_low": 30,
            "canny_high": 100,
            "adapt_block": 51,
            "adapt_c": 10,
        }

    def process_frame(self, bgr_img: np.ndarray, fov_type: str = "circle", threshold: int = 20,
                      roi_mask: np.ndarray = None, pattern_mode: str = "all",
                      shape_threshold: int = 10, manual_fov_circle: dict | None = None) -> RecognitionResult:
        """Process a single frame and return detection results."""
        if bgr_img is None:
            return RecognitionResult()

        self.config["fov_threshold"] = threshold
        self.config["adapt_c"] = shape_threshold
        self.config["canny_low"] = shape_threshold * 3
        self.config["canny_high"] = shape_threshold * 10

        try:
            # 1. Detect FOV: manual circle takes priority over auto detection
            if manual_fov_circle is not None:
                fov_info = self._build_fov_from_manual_circle(bgr_img.shape, manual_fov_circle)
            else:
                fov_info = self._find_fov_boundary(bgr_img, fov_type, roi_mask)

            # 2. Find Ellipses inside the FOV
            ellipses = self._find_ellipses(bgr_img, fov_info, pattern_mode)

            return RecognitionResult(
                fov_type="circle" if manual_fov_circle else fov_type,
                fov_data=fov_info,
                ellipses=ellipses
            )
        except Exception as e:
            print(f"Recognition Error: {e}")
            return RecognitionResult()


    def _build_fov_from_manual_circle(self, img_shape: tuple, circle: dict) -> dict:
        """Build fov_info from a manually defined circle (normalized coords [0,1]).
        Output format is identical to _find_fov_boundary for seamless compatibility."""
        h, w = img_shape[:2]
        cx = int(circle['cx'] * w)
        cy = int(circle['cy'] * h)
        r = int(circle['r'] * w)  # radius normalized by image width
        r = max(1, min(r, max(w, h)))  # clamp to valid range

        fov_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(fov_mask, (cx, cy), r, 255, -1)
        area = float(np.pi * r * r)

        return {
            'type': 'circle',
            'center': (cx, cy),
            'radius': r,
            'mask': fov_mask,
            'area': area,
        }

    def _find_fov_boundary(self, img, fov_type='circle', roi_mask=None):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        work = cv2.bitwise_and(gray, gray, mask=roi_mask) if roi_mask is not None else gray.copy()
        _, binary = cv2.threshold(work, self.config["fov_threshold"], 255, cv2.THRESH_BINARY)
        
        k = self.config["fov_morph_k"]
        kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kern, iterations=3)
        
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return {'type': fov_type, 'area': 0, 'mask': np.zeros_like(gray)}
            
        largest = max(contours, key=cv2.contourArea)
        fov_area = cv2.contourArea(largest)
        fov = {'type': fov_type, 'contour': largest, 'area': fov_area}

        if fov_type == 'circle':
            (cx, cy), r = cv2.minEnclosingCircle(largest)
            center, radius = (int(cx), int(cy)), int(r)
            fov_mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.circle(fov_mask, center, radius, 255, -1)
            fov.update(center=center, radius=radius, mask=fov_mask)
        else:
            rect = cv2.minAreaRect(largest)
            box = np.intp(cv2.boxPoints(rect))
            fov_mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.fillPoly(fov_mask, [box], 255)
            cx, cy = rect[0]
            center = (int(cx), int(cy))
            fov.update(rect=rect, box=box, mask=fov_mask, center=center)
            
        return fov

    def _find_ellipses(self, img, fov_info, pattern_mode="all"):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        fov_mask = fov_info.get('mask')
        if fov_mask is None:
            return []
            
        masked = cv2.bitwise_and(gray, gray, mask=fov_mask)
        blurred = cv2.GaussianBlur(masked, (self.config["blur_ksize"],) * 2, 0)
        
        all_cnts = []
        k3 = np.ones((3, 3), np.uint8)

        # Strategy 1: Canny
        e1 = cv2.Canny(blurred, self.config["canny_low"], self.config["canny_high"])
        e1 = cv2.morphologyEx(e1, cv2.MORPH_CLOSE, k3, iterations=2)
        cnts1, _ = cv2.findContours(e1, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        all_cnts.extend(cnts1)

        if pattern_mode in ("dark_bg", "all"):
            # Strategy 2: Adaptive Threshold (Light targets)
            t2 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, self.config["adapt_block"], self.config["adapt_c"])
            t2 = cv2.bitwise_and(t2, t2, mask=fov_mask)
            t2 = cv2.morphologyEx(t2, cv2.MORPH_OPEN, k3, iterations=2)
            cnts2, _ = cv2.findContours(t2, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            all_cnts.extend(cnts2)

        if pattern_mode in ("light_bg", "all"):
            # Strategy 3: Adaptive Threshold Inv (Dark targets)
            t3 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, self.config["adapt_block"], self.config["adapt_c"])
            t3 = cv2.bitwise_and(t3, t3, mask=fov_mask)
            t3 = cv2.morphologyEx(t3, cv2.MORPH_OPEN, k3, iterations=2)
            cnts3, _ = cv2.findContours(t3, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            all_cnts.extend(cnts3)

        # Strategy 4: Otsu
        _, t4 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        t4 = cv2.bitwise_and(t4, t4, mask=fov_mask)
        t4 = cv2.morphologyEx(t4, cv2.MORPH_OPEN, k3, iterations=2)
        cnts4, _ = cv2.findContours(t4, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        all_cnts.extend(cnts4)

        candidates = []
        fov_area = fov_info.get('area', 0)
        
        for cnt in all_cnts:
            area = cv2.contourArea(cnt)
            if area < self.config["min_ellipse_area"] or len(cnt) < 5:
                continue
                
            try:
                el = cv2.fitEllipse(cnt)
            except:
                continue
                
            (ecx, ecy), (ew, eh), ea = el
            if ew <= 0 or eh <= 0: continue
            
            h, w = gray.shape
            ix, iy = int(ecx), int(ecy)
            if not (0 <= ix < w and 0 <= iy < h):
                continue
            if fov_mask[iy, ix] == 0:
                continue
            
            # Area ratio check
            el_area = np.pi * (ew / 2) * (eh / 2)
            if fov_area > 0 and el_area > fov_area * self.config["max_ellipse_area_ratio"]:
                continue

            circ = min(ew, eh) / max(ew, eh)
            if circ < self.config["min_circularity"]:
                continue
                
            candidates.append({
                'area': area,
                'ellipse': el,
                'center': (int(ecx), int(ecy)),
                'axes': (int(ew), int(eh)),
                'angle': int(ea)
            })
            
        # Deduplication (Simple DIST and SIZE based)
        unique = []
        for cand in candidates:
            (ecx, ecy) = cand['center']
            ew, eh = cand['axes']
            dup = False
            for u in unique:
                ux, uy = u['center']
                uw, uh = u['axes']
                dist = np.hypot(ecx - ux, ecy - uy)
                sz_diff = abs(max(ew, eh) - max(uw, uh)) / max(max(ew, eh), max(uw, uh), 1)
                if dist < max(ew, eh) * 0.3 and sz_diff < 0.3:
                    dup = True
                    break
            if not dup:
                unique.append(cand)

        unique.sort(key=lambda x: x['area'], reverse=True)
        return unique[:self.config["n_ellipses"]]
