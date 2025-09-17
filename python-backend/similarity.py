# similarity.py
from __future__ import annotations
import re
from typing import List, Tuple, Dict, Optional

import cv2
import numpy as np

# try SciPy for extra distance metrics; not required
try:
    from scipy.spatial.distance import cdist as _scipy_cdist
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False

# Optional, principled change-point detection
try:
    import ruptures as rpt
    _HAS_RUPTURES = True
except Exception:
    _HAS_RUPTURES = False

from feature_extractor import (
    line_embedding, lbp_hist, hog_hist, central_band_coords, color_stats_hv
)

def _cosine_consecutive(X: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    if X.shape[0] < 2:
        return np.array([], dtype=np.float32)
    
    diffs = []
    for i in range(X.shape[0] - 1):
        a, b = X[i], X[i + 1]
        dot = float(np.dot(a, b))
        na = float(np.linalg.norm(a)) + eps
        nb = float(np.linalg.norm(b)) + eps
        cos_sim = dot / (na * nb)
        cos_sim = np.clip(cos_sim, -1.0, 1.0)
        diffs.append(1.0 - cos_sim)
    
    return np.array(diffs, dtype=np.float32)

def consecutive_distances(X: np.ndarray, metric: str = "cosine") -> np.ndarray:
    if metric == "cosine":
        return _cosine_consecutive(X)
    elif metric == "euclidean" and _HAS_SCIPY:
        if X.shape[0] < 2:
            return np.array([], dtype=np.float32)
        dists = []
        for i in range(X.shape[0] - 1):
            d = float(_scipy_cdist([X[i]], [X[i + 1]], metric='euclidean')[0, 0])
            dists.append(d)
        return np.array(dists, dtype=np.float32)
    else:
        return _cosine_consecutive(X)

def _smooth(x: np.ndarray, win: int = 3) -> np.ndarray:
    x = np.asarray(x, np.float64)
    if x.size == 0 or win <= 1: return x.copy()
    if win % 2 == 0: win += 1
    pad = win // 2
    k = np.ones(win, np.float64) / win
    return np.convolve(np.pad(x, (pad,pad), mode="reflect"), k, mode="valid")

def _zscore(x: np.ndarray, method="mad", eps=1e-9) -> np.ndarray:
    x = np.asarray(x, np.float64)
    if x.size == 0: return x.copy()
    if method == "std":
        mu, sd = float(x.mean()), float(x.std()) + eps
        return (x - mu) / sd
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med))) + eps
    return 0.6745 * (x - med) / mad

def _peaks_from_thresh(z: np.ndarray, thresh: float) -> List[int]:
    above = z > thresh
    idx = np.where(above)[0]
    if idx.size == 0: return []
    edges = np.where(np.diff(idx) > 1)[0]
    runs = np.split(idx, edges + 1)
    peaks = [int(run[int(np.argmax(z[run]))]) for run in runs]
    return peaks

def _nms_min_gap(peaks: List[int], z: np.ndarray, min_gap: int) -> List[int]:
    if not peaks: return []
    order = sorted(peaks, key=lambda i: z[i], reverse=True)
    kept: List[int] = []
    for p in order:
        if all(abs(p-q) >= min_gap for q in kept):
            kept.append(p)
    return sorted(kept)

def detect_change_indices(X: np.ndarray, metric="cosine", smooth_win=3, z_method="mad",
                          z_thresh: Optional[float]=None, min_gap=2):
    dist = consecutive_distances(X, metric=metric)
    if dist.size == 0:
        return [], dist, np.array([])
    
    smooth_dist = _smooth(dist, win=smooth_win)
    z = _zscore(smooth_dist, method=z_method)
    
    if z_thresh is None:
        z_thresh = 2.0
    
    peaks = _peaks_from_thresh(z, z_thresh)
    peaks = _nms_min_gap(peaks, z, min_gap)
    
    return peaks, smooth_dist, z

def indices_to_segments(n: int, change_idxs: List[int]) -> List[Tuple[int,int]]:
    if n <= 0: return []
    ci = sorted(set(i for i in change_idxs if 0 <= i < n-1))
    starts = [0] + [i+1 for i in ci]
    ends = [i+1 for i in ci] + [n]
    return list(zip(starts, ends))

def _ink_mask(gray: np.ndarray) -> np.ndarray:
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ink = (bw == 0).astype(np.uint8)
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (3,3)))
    return ink.astype(bool)

def _dominant_angle_deg(hog_vec: np.ndarray, orientations: int = 9) -> float:
    if hog_vec.size == 0:
        return 90.0
    if hog_vec.size != orientations:
        return 90.0
    
    angle_step = 180.0 / orientations
    angles = np.arange(orientations) * angle_step
    dominant_bin = int(np.argmax(hog_vec))
    return float(angles[dominant_bin])

def _chi2(a: np.ndarray, b: np.ndarray, eps: float = 1e-9) -> float:
    a = a.astype(np.float64); b = b.astype(np.float64)
    return 0.5 * np.sum(((a - b) ** 2) / (a + b + eps))

def _coverage(gray_band: np.ndarray) -> float:
    mask = _ink_mask(gray_band)
    return float(mask.mean())

def _sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-x)))

def _reason_from_diffs(features_a: Dict, features_b: Dict) -> str:
    msgs = []
    specific_details = []
    
    # slant (dominant angle)
    da = features_a["dom_angle"]
    db = features_b["dom_angle"]
    d_slant = db - da  # positive → more left-leaning
    if abs(d_slant) >= 7:
        msgs.append("significant change in letter slant")
        direction = "more upright" if d_slant < 0 else "more left-leaning"
        specific_details.append(f"The handwriting becomes {direction}, suggesting a different pen grip or writing posture")

    # texture (LBP chi²)
    if features_a["lbp_chi2"] >= 0.15:
        msgs.append("distinct stroke texture patterns")
        specific_details.append("The micro-patterns within letterforms show different characteristics, indicating varied pen control or writing habits")

    # ink darkness (V mean)
    dv = features_b["v_mean"] - features_a["v_mean"]
    if abs(dv) >= 0.05:
        ink_change = "darker ink" if dv < 0 else "lighter ink"
        msgs.append(ink_change)
        specific_details.append(f"The {ink_change} suggests either a different writing instrument, ink mixture, or varying pressure application")

    # stroke density (coverage)
    dcov = features_b["coverage"] - features_a["coverage"]
    if abs(dcov) >= 0.05:
        pressure_change = "heavier strokes and increased pressure" if dcov > 0 else "finer, lighter strokes"
        msgs.append(pressure_change)
        if dcov > 0:
            specific_details.append("The increased stroke weight indicates either a different pen type, more ink flow, or a scribe applying greater writing pressure")
        else:
            specific_details.append("The lighter stroke weight suggests a finer writing instrument, less ink, or a more delicate writing approach")

    if not msgs:
        msgs = ["subtle but consistent paleographic differences"]
        specific_details.append("While individual changes are minor, the cumulative handwriting characteristics suggest a transition between scribal hands")
        specific_details.append("This could indicate a change in scribe, different writing conditions, or the same scribe writing at a different time")
    
    # Build comprehensive explanation
    main_changes = ", ".join(msgs)
    detailed_explanation = " ".join(specific_details[:2])  # Limit to 2 detail sentences for readability
    
    return f"Different scribal hand detected based on {main_changes}. {detailed_explanation}"

def _sort_by_num(paths: List[str]) -> List[str]:
    def key(p):
        m = re.search(r"(\d+)", p)
        return int(m.group(1)) if m else 0
    return sorted(paths, key=key)

class ImageProcessor:
    def __init__(self,
                 metric="cosine",
                 smooth_win=5,
                 z_method="mad",
                 z_thresh: Optional[float]=None,
                 min_gap=2,
                 min_run=2,
                 resize_height=128,
                 central_band_frac=0.6,
                 central_band_pad=2,
                 use_color=True,
                 w_lbp=1.0,
                 w_hog=1.0,
                 w_color=0.5,
                 algo: str = "auto",        # "auto" | "peaks" | "ruptures"
                 ruptures_pen: Optional[float] = None):
        self.metric = metric
        self.smooth_win = smooth_win
        self.z_method = z_method
        self.z_thresh = z_thresh
        self.min_gap = min_gap
        self.min_run = min_run
        self.resize_height = resize_height
        self.central_band_frac = central_band_frac
        self.central_band_pad = central_band_pad
        self.use_color = use_color
        self.w_lbp = w_lbp
        self.w_hog = w_hog
        self.w_color = w_color
        self.algo = algo
        self.ruptures_pen = ruptures_pen
        self.use_color = use_color
        self.w_lbp = w_lbp
        self.w_hog = w_hog
        self.w_color = w_color

    def _band_views(self, img: np.ndarray):
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        H, W = g.shape[:2]
        top, bot = central_band_coords(g, frac=self.central_band_frac,
                                       pad=self.central_band_pad, method="maxsum", min_band_px=12)
        gray_band = g[top:bot, :]
        color_band = img[top:bot, :]
        return gray_band, color_band

    def _diagnostics(self, img: np.ndarray) -> Dict[str, float]:
        gray_band, color_band = self._band_views(img)
        # features for explanation (not the big embedding)
        lbp = lbp_hist(gray_band)
        hog = hog_hist(gray_band)
        dom_angle = _dominant_angle_deg(hog)  # degrees in [0,180)
        # map angle to slant-ish interpretation around vertical 90°
        # keep raw angle for diffs
        cov = _coverage(gray_band)
        cstats = color_stats_hv(color_band, gray_band)  # [h_cos, h_sin, h_var, v_mean, v_std]
        return {
            "lbp": lbp,
            "hog": hog,
            "dom_angle": dom_angle,
            "coverage": cov,
            "v_mean": float(cstats[3]),
            "v_std": float(cstats[4]),
        }

    def detect_with_reasons(self, line_paths: List[str]) -> Dict[str, object]:
        if not line_paths: return {"changes": [], "z": [], "dist": []}
        # read + embed
        paths = _sort_by_num(line_paths)
        imgs, embs, diags = [], [], []
        for p in paths:
            img = cv2.imread(p, cv2.IMREAD_COLOR)
            if img is None: continue
            imgs.append(img)
            embs.append(line_embedding(
                img,
                central_band_frac=self.central_band_frac,
                central_band_pad=self.central_band_pad,
                resize_height=self.resize_height,
                use_color=self.use_color,
                w_lbp=self.w_lbp, w_hog=self.w_hog, w_color=self.w_color
            ))
            diags.append(self._diagnostics(img))

        if len(embs) < 2: return {"changes": [], "z": [], "dist": []}
        X = np.vstack(embs).astype(np.float32)
        
        # detect with adaptive threshold if not provided
        change_idxs: List[int] = []
        dist = np.array([])
        z = np.array([])
        
        # 1) Peak/z-score method (fast)
        def _peaks_method(z_override=None):
            if z_override is None:
                z_override = self.z_thresh
            return detect_change_indices(
                X, metric=self.metric, smooth_win=self.smooth_win,
                z_method=self.z_method, z_thresh=z_override, min_gap=self.min_gap
            )

        # 2) Ruptures on the smoothed 1D distance signal (principled)
        def _ruptures_method(smooth_dist):
            if not _HAS_RUPTURES or smooth_dist.size < 3:
                return []
            # Use PELT on 1D with L2; choose a mild penalty if none provided
            pen = float(self.ruptures_pen) if self.ruptures_pen is not None else max(2.0, 2.0*np.log(len(smooth_dist)))
            algo = rpt.Pelt(model="l2").fit(smooth_dist.reshape(-1, 1))
            try:
                bkps = algo.predict(pen=pen)  # 1-based ends, includes len
            except Exception:
                return []
            raw = [i-1 for i in bkps[:-1]]  # to boundary indices between lines
            # enforce min_run
            kept = []
            last = -999
            for i in raw:
                if i - last >= self.min_run:
                    kept.append(i)
                    last = i
            return kept

        use_peaks = (self.algo in ("auto", "peaks"))
        use_rupt = (self.algo in ("auto", "ruptures"))

        # Always compute a baseline dist/z (used for confidence either way)
        _, dist, z = _peaks_method(self.z_thresh if self.z_thresh is not None else 2.0)

        if use_peaks:
            if self.z_thresh is None:
                for t in (2.5, 2.2, 2.0, 1.8, 1.6, 1.4):
                    peaks, dist_tmp, z_tmp = _peaks_method(t)
                    if len(peaks) >= 1:
                        change_idxs = peaks; dist = dist_tmp; z = z_tmp; break
            else:
                change_idxs, dist, z = _peaks_method(self.z_thresh)

        if use_rupt and (not change_idxs):
            # run ruptures on smoothed distance if peaks found none
            smooth_dist = _smooth(consecutive_distances(X, metric=self.metric), win=self.smooth_win)
            change_idxs = _ruptures_method(smooth_dist)

        # Enforce min_gap across any change_idxs we have
        final_changes: List[int] = []
        for i in sorted(set(change_idxs)):
            if not final_changes or (i - final_changes[-1]) >= self.min_gap:
                final_changes.append(i)

        changes = []
        for i in final_changes:
            if 0 <= i < len(imgs) - 1:
                # confidence from z: squash with sigmoid around z=2.0
                conf = _sigmoid(float(z[i] - 2.0))  # ~0.88 at z=2, ~0.95 at z=3
                # explanations
                a, b = diags[i], diags[i+1]
                # texture dissimilarity via chi² on LBP
                a["lbp_chi2"] = _chi2(a["lbp"], b["lbp"])
                reason = _reason_from_diffs(a, b)
                changes.append({"index": int(i), "confidence": float(conf), "reason": reason})

        return {"changes": changes, "z": z.tolist(), "dist": dist.tolist()}
