# pre_processor.py
"""
Preprocessing for manuscript pages:
1) Grayscale
2) Illumination/background correction
3) Small-angle deskew (±5°)
4) Sauvola adaptive binarization

Primary entry point: preprocess(bgr_img) -> bw uint8 (0 or 255)
"""

from __future__ import annotations
import cv2
import numpy as np
from typing import Dict, Tuple

try:
    from skimage.filters import threshold_sauvola
    _HAS_SAUVOLA = True
except Exception:
    _HAS_SAUVOLA = False


def _ensure_odd(n: int) -> int:
    return int(n + (n % 2 == 0))

def to_gray(img: np.ndarray) -> np.ndarray:
    """Convert BGR/RGB to single-channel grayscale (uint8)."""
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img

def _auto_kernel_size(shape: Tuple[int, int], frac: float = 0.035, min_ks: int = 21, max_ks: int = 151) -> int:
    """
    Choose an odd kernel size as a fraction of the smaller image dimension.
    Good defaults for background estimation on manuscript scans.
    """
    h, w = shape[:2]
    base = int(min(h, w) * frac)
    base = np.clip(base, min_ks, max_ks)
    return _ensure_odd(base)

def illumination_correct(gray: np.ndarray, method: str = "morph_open", frac: float = 0.035) -> np.ndarray:
    """
    Background estimation + removal for evening out illumination.
    """
    if gray.size == 0:
        return gray.copy()
    
    ks = _auto_kernel_size(gray.shape, frac=frac)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks))
    
    if method == "morph_open":
        bg_est = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
    else:
        bg_est = cv2.GaussianBlur(gray, (ks, ks), 0)
    
    # subtract background
    corrected = cv2.subtract(gray, bg_est)
    # stretch to full range
    corrected = cv2.normalize(corrected, None, 0, 255, cv2.NORM_MINMAX)
    return corrected

def _estimate_small_skew_angle(gray: np.ndarray, max_angle: float = 5.0) -> float:
    """Very basic skew estimation using Hough lines."""
    if gray.size == 0:
        return 0.0
    
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=int(gray.shape[0]*0.3))
    
    if lines is None or len(lines) == 0:
        return 0.0
    
    angles = []
    for line in lines[:50]:  # consider first 50 lines
        # Handle both formats: [[rho, theta]] and [rho, theta]
        if isinstance(line, np.ndarray) and line.ndim > 1:
            rho, theta = line[0]  # nested format [[rho, theta]]
        else:
            rho, theta = line  # flat format [rho, theta]
        angle_deg = (theta - np.pi/2) * 180 / np.pi
        if abs(angle_deg) <= max_angle:
            angles.append(angle_deg)
    
    return float(np.median(angles)) if angles else 0.0

def deskew_small(gray: np.ndarray, max_angle: float = 5.0, border_value: int = 255) -> Tuple[np.ndarray, float]:
    """
    Rotate image by a small estimated angle; returns (rotated, angle_degrees).
    """
    angle = _estimate_small_skew_angle(gray, max_angle)
    if abs(angle) < 0.1:
        return gray.copy(), angle
    
    h, w = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), 
                           flags=cv2.INTER_CUBIC, 
                           borderMode=cv2.BORDER_CONSTANT, 
                           borderValue=border_value)
    return rotated, angle

def binarize_sauvola(gray: np.ndarray, window: int = 31, k: float = 0.2) -> np.ndarray:
    """
    Sauvola adaptive thresholding with Otsu fallback.
    """
    window = int(window | 1)  # force odd
    if gray.size == 0:
        return gray.copy()
    
    if _HAS_SAUVOLA:
        try:
            thresh = threshold_sauvola(gray, window_size=window, k=k)
            binary = (gray > thresh).astype(np.uint8) * 255
            return binary
        except Exception:
            pass
    
    # Fallback to Otsu
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def preprocess(bgr_img: np.ndarray,
               illum_method: str = "morph_open",
               illum_frac: float = 0.035,
               do_deskew: bool = True,
               sauvola_window: int = 31,
               sauvola_k: float = 0.2) -> np.ndarray:
    """
    Full pipeline → returns a binary image (uint8 with values {0, 255}).
    """
    gray = to_gray(bgr_img)
    corrected = illumination_correct(gray, method=illum_method, frac=illum_frac)
    # Boost local contrast for faint strokes
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    corrected = clahe.apply(corrected)
    if do_deskew:
        corrected, _ = deskew_small(corrected, max_angle=5.0, border_value=255)
    bw = binarize_sauvola(corrected, window=sauvola_window, k=sauvola_k)
    # Light denoise without harming thin strokes
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    return bw
