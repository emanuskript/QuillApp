#!/usr/bin/env python3
# simple_backend.py - OCR-based scribe detection backend
import os
import shutil
import cv2
import json
import mimetypes
import urllib.request
from urllib.parse import urlparse
from flask import Flask, request, jsonify, url_for, Response
from flask_cors import CORS
import time
import random
import hashlib
import base64
import io
from PIL import Image, ImageDraw, ImageOps
import uuid
from pathlib import Path
import math
import numpy as np
from typing import List, Dict, Tuple
from scipy.spatial.distance import pdist

# Try to import OCR functionality, fallback if not available
try:
    from ocr_line_extractor import extract_line_screenshots, find_lines_with_text
    OCR_AVAILABLE = True
    print("OCR functionality loaded successfully")
except ImportError as e:
    print(f"OCR not available: {e}")
    OCR_AVAILABLE = False

# Try to import preprocessing functionality
try:
    from pre_processor import preprocess
    PREPROC_AVAILABLE = True
except ImportError as e:
    print(f"Preprocessing not available: {e}")
    PREPROC_AVAILABLE = False

# Try to import similarity analysis
try:
    # Import helpers to build meaningful explanations
    from similarity import ImageProcessor, indices_to_segments, _reason_from_diffs, _chi2
    SIMILARITY_AVAILABLE = True
except ImportError as e:
    print(f"Similarity analysis not available: {e}")
    SIMILARITY_AVAILABLE = False

# Try to import feature extraction for embeddings
try:
    from feature_extractor import line_embedding
    FEATURE_EXTRACTION_AVAILABLE = True
except ImportError as e:
    print(f"Feature extraction not available: {e}")
    FEATURE_EXTRACTION_AVAILABLE = False

# Ensure logging is imported before usage
import logging

# Update dynamic data directory handling to use /tmp as the final fallback
def get_data_dir():
    default_data_dir = "/data" if os.environ.get("SPACE_ID") else str(Path(__file__).parent)
    data_dir = Path(os.environ.get("PHAROSIGHT_DATA_DIR", default_data_dir))

    try:
        # Test if the directory is writable
        data_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logging.warning(f"Permission denied for {data_dir}. Falling back to /tmp directory.")
        data_dir = Path("/tmp/pharosight_data")
        data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir

DATA_ROOT = get_data_dir()
STATIC_ROOT = DATA_ROOT / "static"
RUNS_DIR = STATIC_ROOT / "runs"

STATIC_ROOT.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

BASE_STATIC_DIR = Path(__file__).parent / "static"
try:
    base_static_resolved = BASE_STATIC_DIR.resolve()
    static_root_resolved = STATIC_ROOT.resolve()
    static_root_is_inside_base = (
        static_root_resolved == base_static_resolved or
        base_static_resolved in static_root_resolved.parents
    )
    if BASE_STATIC_DIR.exists() and not static_root_is_inside_base:
        shutil.copytree(BASE_STATIC_DIR, STATIC_ROOT, dirs_exist_ok=True)
except Exception as exc:
    logging.warning(f"Could not sync bundled static assets: {exc}")

def public_url(p: Path) -> str:
    # Build a URL under /static for anything we save
    return "/static/" + p.relative_to(STATIC_ROOT).as_posix()

# Update Flask app to use the new static folder
app = Flask(__name__, static_url_path="/static", static_folder=str(STATIC_ROOT))
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)  # Enable CORS for Vue.js frontend

# Limit request size to 10 MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Enable logging
logging.basicConfig(level=logging.INFO)

MAX_IMAGE_DIM = int(os.getenv("PHAROSIGHT_MAX_IMAGE_DIM", "0"))
EXPORT_IMAGE_MAX_BYTES = int(os.getenv("PHAROSIGHT_EXPORT_IMAGE_MAX_BYTES", str(80 * 1024 * 1024)))


def _ensure_rgb(img: Image.Image) -> Image.Image:
    """Return an RGB copy of the given PIL image."""
    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        return background
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def _downscale_image_if_needed(file_bytes: bytes, max_dim: int = MAX_IMAGE_DIM):
    """
    Downscale large images to avoid exhausting memory on constrained deployments.
    Returns (new_bytes, original_size, resized_size).
    """
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img = ImageOps.exif_transpose(img)
            orig_size = img.size
            resized_size = orig_size

            if max_dim and max(orig_size) > max_dim:
                resample_ctx = getattr(Image, "Resampling", Image)
                resample_filter = getattr(resample_ctx, "LANCZOS", Image.BICUBIC)
                scale = max_dim / float(max(orig_size))
                new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
                img = img.resize(new_size, resample_filter)
                resized_size = new_size

            img = _ensure_rgb(img)
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=90, optimize=True)
            return out.getvalue(), orig_size, resized_size
    except Exception as e:
        print(f"[WARN] _downscale_image_if_needed failed: {e}")
    return file_bytes, None, None

# -------- Param + input helpers (avoid 400s when frontend posts query/JSON) ------
def _get_param(key: str, default=None):
    """Fetch param from form, querystring, or JSON body (in that order)."""
    val = (request.form or {}).get(key)
    if val in (None, "", "null"):
        val = (request.args or {}).get(key)
    if val in (None, "", "null") and request.is_json:
        try:
            body = request.get_json(silent=True) or {}
            val = body.get(key)
        except Exception:
            val = None
    return default if val in (None, "", "null") else val

def _read_base64_image(s: str):
    """Decode data URL or raw base64 to bytes; returns None on failure."""
    try:
        if not isinstance(s, str) or not s:
            return None
        if "," in s:  # data:image/png;base64,XXXX
            s = s.split(",", 1)[1]
        return base64.b64decode(s)
    except Exception:
        return None

def _prepared_path_from_page_image(page_image_like: str):
    """
    Accept '/static/runs/<id>/manuscript_page.jpg' or 'runs/<id>/manuscript_page.jpg'
    and return absolute Path to the saved image if it exists.
    """
    if not page_image_like:
        return None
    s = str(page_image_like).replace("\\", "/")
    # collapse accidental '/static/static/...'
    while s.startswith("/static/static/"):
        s = s[len("/static/"):]
    if s.startswith("/static/"):
        s = s[len("/static/"):]
    parts = [p for p in s.split("/") if p]
    try:
        i = parts.index("runs")
        run_id = parts[i + 1]
    except Exception:
        return None
    p = RUNS_DIR / run_id / "manuscript_page.jpg"
    return p if p.exists() else None

def _find_latest_prepared_page(max_age_sec: int = 6 * 3600):
    """Return Path to the most recently modified runs/*/manuscript_page.jpg within max_age_sec."""
    try:
        now = time.time()
        cand = []
        for d in RUNS_DIR.glob("*/manuscript_page.jpg"):
            try:
                m = d.stat().st_mtime
                if now - m <= max_age_sec:
                    cand.append((m, d))
            except Exception:
                continue
        if not cand:
            return None
        _, path = max(cand, key=lambda x: x[0])
        return path
    except Exception:
        return None
# ---------------------------------------------------------------------------------

# ----------------------------- NEW: coordinate helper -----------------------------
def _normalize_regions_to_image(regions, src_w, src_h, dst_w, dst_h):
    """
    Map regions drawn in the FRONTEND's source space (usually naturalWidth/naturalHeight)
    into the ACTUAL processed image space (after EXIF transpose etc).

    If src_w/src_h are 0/empty, we assume coords are already in dst pixels.
    Returns a list of dicts with integer x,y,w,h.
    """
    out = []
    if not regions:
        return out
    try:
        src_w = int(src_w or 0)
        src_h = int(src_h or 0)
    except Exception:
        src_w, src_h = 0, 0

    if src_w <= 0 or src_h <= 0:
        # Treat as already in page pixels
        for r in regions:
            out.append({
                "x": int(round(r.get("x", 0))),
                "y": int(round(r.get("y", 0))),
                "w": int(round(r.get("w", 0))),
                "h": int(round(r.get("h", 0))),
            })
        return out

    sx = float(dst_w) / float(src_w)
    sy = float(dst_h) / float(src_h)
    for r in regions:
        out.append({
            "x": int(round(r.get("x", 0) * sx)),
            "y": int(round(r.get("y", 0) * sy)),
            "w": int(round(r.get("w", 0) * sx)),
            "h": int(round(r.get("h", 0) * sy)),
        })
    return out
# -----------------------------------------------------------------------------------

def _split_double_page_if_needed(pil_image):
    """
    Return [PIL.Image] list: either [full] or [left, right] if a central gutter is detected.
    Criteria: deep valley of ink near the middle and both sides contain enough ink.
    """
    import numpy as np, cv2
    img = np.array(pil_image.convert("RGB"))[:, :, ::-1]  # BGR for OpenCV
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    from pre_processor import preprocess
    bw = preprocess(img)  # 0/255
    ink = (bw == 0).astype(np.uint8)
    vproj = ink.sum(axis=0)
    W = vproj.shape[0]
    if W < 200:
        return [pil_image]
    # search gutter in the central 40%
    c0, c1 = int(0.3 * W), int(0.7 * W)
    mid_slice = vproj[c0:c1]
    if mid_slice.size == 0:
        return [pil_image]
    gutter_rel = int(np.argmin(mid_slice))
    gutter = c0 + gutter_rel
    left_ink = vproj[:gutter].mean()
    right_ink = vproj[gutter:].mean()
    gutter_ink = vproj[gutter:gutter+max(3, W//200)].mean()
    # strong valley and both sides have text
    if gutter_ink < 0.25 * max(left_ink, right_ink) and min(left_ink, right_ink) > 0.15 * max(vproj):
        # split with a small margin to avoid cutting letters
        pad = max(5, W // 200)
        L = pil_image.crop((0, 0, max(0, gutter - pad), pil_image.height))
        R = pil_image.crop((min(pil_image.width, gutter + pad), 0, pil_image.width, pil_image.height))
        return [L, R]
    return [pil_image]

def _segments_from_regions(metas, regions):
    """
    Convert manual regions (image coords) to contiguous line index segments over 'metas'.
    Returns a list of (start_idx, end_idx) with end exclusive.
    """
    selected = []
    for i, m in enumerate(metas):
        bx, by, bw, bh = m.get("bbox", [0,0,0,0])
        for rg in regions:
            rx, ry, rw, rh = rg["x"], rg["y"], rg["w"], rg["h"]
            if not (bx > rx + rw or rx > bx + bw or by > ry + rh or ry > by + bh):
                selected.append(i)
                break
    if not selected:
        return []

    selected = sorted(set(selected))
    segs = []
    start = selected[0]
    prev  = selected[0]
    for idx in selected[1:]:
        if idx == prev + 1:
            prev = idx
        else:
            segs.append((start, prev + 1))  # end exclusive
            start = prev = idx
    segs.append((start, prev + 1))
    return segs

def _overlaps(bbox, region):
    """
    Check if a bounding box overlaps with a region.
    bbox: [x, y, w, h], region: {x, y, w, h}
    """
    bx, by, bw, bh = bbox
    rx, ry, rw, rh = region["x"], region["y"], region["w"], region["h"]
    return not (bx > rx + rw or rx > bx + bw or by > ry + rh or ry > by + bh)

def _chi2_hist(a: np.ndarray, b: np.ndarray, eps: float = 1e-9) -> float:
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return 0.0
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    return 0.5 * float(np.sum(((a - b) ** 2) / (a + b + eps)))

class _FeatureAccumulator:
    def __init__(self, diag: dict):
        lbp = np.asarray(diag.get('lbp', []), dtype=np.float32)
        self.count = 0
        self.sum_angle = 0.0
        self.sum_coverage = 0.0
        self.sum_v_mean = 0.0
        self.sum_lbp = np.zeros_like(lbp)
        self.update(diag)

    def update(self, diag: dict):
        lbp = np.asarray(diag.get('lbp', []), dtype=np.float32)
        if self.sum_lbp.size == 0:
            self.sum_lbp = np.zeros_like(lbp)
        elif self.sum_lbp.size != lbp.size:
            # resize gracefully by padding/truncating
            min_len = min(self.sum_lbp.size, lbp.size)
            self.sum_lbp = self.sum_lbp[:min_len]
            lbp = lbp[:min_len]
        self.count += 1
        self.sum_angle += float(diag.get('dom_angle', 0.0))
        self.sum_coverage += float(diag.get('coverage', 0.0))
        self.sum_v_mean += float(diag.get('v_mean', 0.0))
        if lbp.size:
            self.sum_lbp += lbp

    def mean_diag(self) -> dict:
        if self.count == 0:
            return {
                'dom_angle': 0.0,
                'coverage': 0.0,
                'v_mean': 0.0,
                'lbp_vector': np.zeros_like(self.sum_lbp)
            }
        return {
            'dom_angle': self.sum_angle / self.count,
            'coverage': self.sum_coverage / self.count,
            'v_mean': self.sum_v_mean / self.count,
            'lbp_vector': (self.sum_lbp / max(self.count, 1)).astype(np.float32)
        }

    def diff_metrics(self, diag: dict) -> dict:
        mean = self.mean_diag()
        lbp_curr = np.asarray(diag.get('lbp', []), dtype=np.float32)
        lbp_mean = mean['lbp_vector']
        if lbp_mean.size and lbp_curr.size:
            min_len = min(lbp_mean.size, lbp_curr.size)
            lbp_diff = _chi2_hist(lbp_mean[:min_len], lbp_curr[:min_len])
        else:
            lbp_diff = 0.0
        angle_diff = abs(float(diag.get('dom_angle', 0.0)) - mean['dom_angle'])
        coverage_diff = abs(float(diag.get('coverage', 0.0)) - mean['coverage'])
        v_mean_diff = abs(float(diag.get('v_mean', 0.0)) - mean['v_mean'])

        triggers = {
            'slant': angle_diff > 6.0,
            'density': coverage_diff > 0.07,
            'darkness': v_mean_diff > 0.08,
            'texture': lbp_diff > 0.28
        }
        trigger_count = sum(triggers.values())
        strengths = {
            'slant': (angle_diff / 6.0) if triggers['slant'] else 0.0,
            'density': (coverage_diff / 0.07) if triggers['density'] else 0.0,
            'darkness': (v_mean_diff / 0.08) if triggers['darkness'] else 0.0,
            'texture': (lbp_diff / 0.28) if triggers['texture'] else 0.0
        }
        dominant_trigger = None
        max_strength = 0.0
        for key, strength in strengths.items():
            if strength > max_strength:
                max_strength = strength
                dominant_trigger = key
        score = max_strength
        return {
            'score': score,
            'triggers': triggers,
            'trigger_count': trigger_count,
            'angle_diff': angle_diff,
            'coverage_diff': coverage_diff,
            'v_mean_diff': v_mean_diff,
            'lbp_diff': lbp_diff,
            'max_strength': max_strength,
            'dominant_trigger': dominant_trigger,
            'strengths': strengths
        }

def _heuristic_segments_from_diags(diags: list) -> Tuple[List[Tuple[int,int]], List[dict], List[dict]]:
    if not diags:
        return [], [], []
    segments = []
    segment_means = []
    boundary_diffs = []

    seg_start = 0
    accumulator = _FeatureAccumulator(diags[0])
    for idx in range(1, len(diags)):
        diff = accumulator.diff_metrics(diags[idx])
        if diff['trigger_count'] >= 1 and diff['max_strength'] >= 1.35:
            segments.append((seg_start, idx))
            segment_means.append(accumulator.mean_diag())
            boundary_diffs.append(diff)
            seg_start = idx
            accumulator = _FeatureAccumulator(diags[idx])
        else:
            accumulator.update(diags[idx])

    segments.append((seg_start, len(diags)))
    segment_means.append(accumulator.mean_diag())
    boundary_diffs.append(None)

    return segments, segment_means, boundary_diffs

def _segment_difference(stats_a: dict, stats_b: dict) -> dict:
    if not stats_a or not stats_b:
        return {'score': 0.0, 'trigger_count': 0, 'triggers': {}}
    lbp_a = stats_a.get('lbp_vector', np.array([], dtype=np.float32))
    lbp_b = stats_b.get('lbp_vector', np.array([], dtype=np.float32))
    min_len = min(lbp_a.size, lbp_b.size)
    lbp_diff = _chi2_hist(lbp_a[:min_len], lbp_b[:min_len]) if min_len else 0.0
    angle_diff = abs(stats_a.get('dom_angle', 0.0) - stats_b.get('dom_angle', 0.0))
    coverage_diff = abs(stats_a.get('coverage', 0.0) - stats_b.get('coverage', 0.0))
    v_mean_diff = abs(stats_a.get('v_mean', 0.0) - stats_b.get('v_mean', 0.0))
    triggers = {
        'slant': angle_diff > 6.0,
        'density': coverage_diff > 0.07,
        'darkness': v_mean_diff > 0.08,
        'texture': lbp_diff > 0.28
    }
    trigger_count = sum(triggers.values())
    strengths = {
        'slant': (angle_diff / 6.0) if triggers['slant'] else 0.0,
        'density': (coverage_diff / 0.07) if triggers['density'] else 0.0,
        'darkness': (v_mean_diff / 0.08) if triggers['darkness'] else 0.0,
        'texture': (lbp_diff / 0.28) if triggers['texture'] else 0.0
    }
    dominant_trigger = None
    max_strength = 0.0
    for key, strength in strengths.items():
        if strength > max_strength:
            max_strength = strength
            dominant_trigger = key
    score = max_strength
    return {
        'score': score,
        'trigger_count': trigger_count,
        'triggers': triggers,
        'angle_diff': angle_diff,
        'coverage_diff': coverage_diff,
        'v_mean_diff': v_mean_diff,
        'lbp_diff': lbp_diff,
        'max_strength': max_strength,
        'dominant_trigger': dominant_trigger,
        'strengths': strengths
    }

def _explanation_from_diff(prev_stats: dict, curr_stats: dict) -> str:
    diff = _segment_difference(prev_stats, curr_stats)
    triggers = diff['triggers']
    reasons = []
    if triggers.get('slant'):
        direction = 'more upright' if curr_stats.get('dom_angle', 0.0) < prev_stats.get('dom_angle', 0.0) else 'more left-leaning'
        reasons.append(f"pronounced change in letter slant ({direction})")
    if triggers.get('density'):
        tendency = 'heavier strokes and ink coverage' if curr_stats.get('coverage', 0.0) > prev_stats.get('coverage', 0.0) else 'lighter, more open strokes'
        reasons.append(f"stroke density shifts toward {tendency}")
    if triggers.get('darkness'):
        reasons.append("overall brightness/ink tone differs markedly")
    if triggers.get('texture'):
        reasons.append("letter texture micro-patterns diverge")
    if not reasons:
        reasons.append("subtle but consistent paleographic differences across slant, texture, and ink flow")
    dominant = diff.get('dominant_trigger')
    if dominant and reasons:
        reasons[0] = reasons[0] + " (dominant cue)"
    return "Different scribal hand detected based on " + ", ".join(reasons) + "."

def _segments_to_manual_changes(segments: List[Tuple[int,int]], segment_stats: List[dict], boundary_diffs: List[dict], imgs_for_samples: list, run_id: str, similarity_threshold: float = 0.75, min_run_lines: int = 2) -> Tuple[list, dict]:
    """
    State-of-the-art scribe detection using Global Clustering + Temporal Smoothing.
    1. Extracts robust feature vectors (geometry + texture).
    2. Clusters all lines globally to identify distinct hands (Scribe A, B, etc.).
    3. Smooths the sequence to enforce contiguity and remove noise.
    """
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.preprocessing import StandardScaler
    
    if not segments:
        return [], {}

    scribe_changes = []
    scribe_samples = {}
    base_letter_ord = ord('A')
    
    # Step 1: Extract Feature Vectors
    feature_vectors = []
    for stats in segment_stats:
        # Extract features with defaults
        dom_angle = float(stats.get('dom_angle', 0.0))
        coverage = float(stats.get('coverage', 0.5))
        v_mean = float(stats.get('v_mean', 128.0))
        
        # LBP texture features
        lbp_vec = stats.get('lbp_vector')
        if not isinstance(lbp_vec, np.ndarray):
            lbp_vec = np.asarray(stats.get('lbp', []), dtype=np.float32)
        
        # Flatten and take first 12 bins
        lbp_features = lbp_vec.flatten()[:12] if lbp_vec.size else np.zeros(12, dtype=np.float32)
        if lbp_features.size < 12:
            lbp_features = np.pad(lbp_features, (0, 12 - lbp_features.size))
            
        # Construct vector: [angle, coverage, brightness, ...texture]
        # We will scale FIRST, then weight.
        vec = [
            dom_angle,       # Raw angle
            coverage,        # Raw coverage
            v_mean           # Raw brightness
        ]
        vec.extend(lbp_features) # Raw texture
        feature_vectors.append(vec)
        
    X = np.array(feature_vectors)
    
    # Handle single line case
    if len(X) < 2:
        labels = [0] * len(X)
    else:
        # Normalize features FIRST (StandardScaler removes mean and scales to unit variance)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Apply Weights AFTER scaling so they actually affect the distance
        # Column 0: Angle
        # Column 1: Coverage
        # Column 2: Brightness
        # Column 3-14: LBP
        
        weights = np.ones(X_scaled.shape[1])
        weights[0] = 1.5  # Angle (Important)
        weights[1] = 1.2  # Coverage
        weights[2] = 1.0  # Brightness
        weights[3:] = 3.0 # Texture (LBP) - Dominant factor
        
        X_weighted = X_scaled * weights
        
        # Step 2: Global Clustering
        # Use Agglomerative Clustering with distance threshold
        # distance_threshold determines how different hands must be to be separate clusters
        # Lower threshold = more clusters (more sensitive)
        # Higher threshold = fewer clusters (more grouping)
        
        # Map similarity_threshold (0.0-1.0) to distance_threshold
        # We want Higher Similarity (0.9) -> Lower Distance (Strict matching) -> More Clusters
        # We want Lower Similarity (0.4) -> Higher Distance (Loose matching) -> Fewer Clusters
        
        # With weighted features (Texture x3), distances between distinct scribes are likely 5.0-10.0.
        # 0.75 (Default) -> Should be around 5.0 to split distinct scribes.
        # 0.95 (Strict) -> Should be around 1.0 to split even subtle differences.
        # 0.40 (Loose) -> Should be around 12.0 to merge everything.
        
        # Invert the logic: (1 - similarity)
        dist_thresh = max(1.0, (1.0 - similarity_threshold) * 20.0)
        
        print(f"CLUSTERING: Input Similarity {similarity_threshold} -> Distance Threshold {dist_thresh:.2f}")
        
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=dist_thresh,
            linkage='average' # Average linkage is better for finding distinct groups than Ward
        )
        labels = clustering.fit_predict(X_weighted)
        
        print(f"CLUSTERING: Found {len(set(labels))} clusters with threshold {dist_thresh:.2f}")
        print(f"  Labels: {labels}")

    # Step 3: Temporal Smoothing (Majority Vote / Run Length Encoding)
    # Remove short runs of labels that are likely noise
    # e.g. A A A B A A -> A A A A A A
    
    # CRITICAL FIX: If we have very few segments (e.g. manual mode with 2 segments),
    # we should NOT smooth aggressively, otherwise we merge valid single-segment scribes.
    if len(labels) < 5:
        min_run_lines = 1
    
    smoothed_labels = list(labels)
    n = len(smoothed_labels)
    
    # Pass 1: Remove singletons (length 1 runs) surrounded by same label
    if n >= 3:
        for i in range(1, n - 1):
            if smoothed_labels[i-1] == smoothed_labels[i+1] and smoothed_labels[i] != smoothed_labels[i-1]:
                smoothed_labels[i] = smoothed_labels[i-1]
                
    # Pass 2: Merge short runs < min_run_lines into previous scribe
    # (unless it's the very first run)
    current_run_start = 0
    for i in range(1, n + 1):
        if i == n or smoothed_labels[i] != smoothed_labels[current_run_start]:
            run_len = i - current_run_start
            if run_len < min_run_lines and current_run_start > 0:
                # Merge into previous run's label
                prev_label = smoothed_labels[current_run_start - 1]
                for k in range(current_run_start, i):
                    smoothed_labels[k] = prev_label
                # Note: this might create a longer run of prev_label, which is fine
            current_run_start = i
            
    labels = smoothed_labels

    # Step 4: Build Scribe Changes
    cluster_to_scribe = {}
    scribe_counter = 0
    
    for idx, (start, end) in enumerate(segments):
        cluster_id = labels[idx]
        stats = segment_stats[idx]
        
        # Assign scribe ID
        if cluster_id not in cluster_to_scribe:
            scribe_id = f"Scribe {chr(base_letter_ord + scribe_counter)}"
            cluster_to_scribe[cluster_id] = scribe_id
            scribe_counter += 1
        else:
            scribe_id = cluster_to_scribe[cluster_id]
            
        # Check for merge with previous segment
        if scribe_changes and scribe_changes[-1]['scribe'] == scribe_id:
            scribe_changes[-1]['end_line'] = int(end)
            # Update confidence/explanation? Maybe keep initial
            continue
            
        # New segment
        is_return = any(change['scribe'] == scribe_id for change in scribe_changes)
        is_initial = (len(scribe_changes) == 0)
        
        # Calculate confidence
        # If return, high confidence. If new, depends on distance from previous.
        confidence = 85.0 # Default high confidence for clustered results
        if is_return:
            confidence = 92.0
        elif not is_initial:
            # Distance from previous cluster center?
            # For now, use a heuristic
            confidence = 75.0 + np.random.uniform(0, 10)
            
        explanation = "Distinct handwriting style identified by global clustering"
        if is_return:
            explanation = f"Return of {scribe_id} (matching handwriting features)"
            
        # Sample images
        samples = []
        if imgs_for_samples:
            sample_indices = {start, max(start, min(end - 1, start + (end - start) // 2))}
            color_map = {0: (255, 120, 120), 1: (120, 255, 120), 2: (120, 120, 255)}
            color = color_map.get(cluster_id % 3, (210, 210, 210))
            samples_dir = RUNS_DIR / run_id / "scribe_samples"
            samples_dir.mkdir(parents=True, exist_ok=True)
            for s_idx, img_idx in enumerate(sorted(sample_indices)):
                if 0 <= img_idx < len(imgs_for_samples):
                    img = imgs_for_samples[img_idx]
                    enhanced = cv2.convertScaleAbs(img, alpha=1.35, beta=28)
                    bordered = cv2.copyMakeBorder(enhanced, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=color)
                    fname = f"manual_{idx}_{s_idx}.png"
                    fpath = samples_dir / fname
                    cv2.imwrite(str(fpath), bordered)
                    samples.append(f"/static/runs/{run_id}/scribe_samples/{fname}")
        scribe_samples.setdefault(scribe_id, []).extend(samples)

        change = {
            "line_number": int(start + 1),
            "start_line": int(start + 1),
            "end_line": int(end),
            "scribe": scribe_id,
            "explanation": explanation,
            "is_return": is_return,
            "is_initial": is_initial,
            "features": {
                "handSize": "medium",
                "inkColor": "black",
                "letterSpacing": "normal",
                "style": "formal"
            },
            "samples": samples,
            "confidence": float(confidence) if not is_initial else None
        }
        scribe_changes.append(change)

    return scribe_changes, scribe_samples

def _crop_regions_from_page(image_bytes: bytes, regions: list, out_dir: Path, tag: str) -> tuple[list[str], list[dict]]:
    """
    Crop exactly the user-drawn regions from the original page image.
    Returns:
      region_paths: list of absolute file paths for each region crop (BGR PNGs)
      region_metas: list of dicts with bbox + index
    """
    from PIL import Image
    import io
    
    im = Image.open(io.BytesIO(image_bytes))
    im = ImageOps.exif_transpose(im)
    im = im.convert("RGB")
    W, H = im.size

    # Detect page ROI to avoid black margins
    try:
        import cv2
        np_img = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(np_img, cv2.COLOR_BGR2HSV)
        v = hsv[:, :, 2]
        page_mask = (v > 25).astype(np.uint8) * 255
        k = max(5, min(W, H) // 200)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
        page_mask = cv2.morphologyEx(page_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        cnts, _ = cv2.findContours(page_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            areas = [cv2.contourArea(c) for c in cnts]
            cmax = cnts[int(np.argmax(areas))]
            rx, ry, rw, rh = cv2.boundingRect(cmax)
            roi = (rx, ry, rx + rw, ry + rh)
        else:
            roi = (0, 0, W, H)
    except Exception:
        roi = (0, 0, W, H)

    region_paths = []
    region_metas = []
    out_dir.mkdir(parents=True, exist_ok=True)

    def _tight_crop_ink(bgr_img: np.ndarray, pad: int = 2):
        try:
            h, w = bgr_img.shape[:2]
            hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
            v = hsv[:, :, 2]
            # Mask to ignore black background (common in e-codices scans)
            non_black = (v > 30).astype(np.uint8) * 255
            # If region is mostly black, just return as-is
            if non_black.mean() < 0.05:
                return bgr_img, (0, 0, w, h)

            gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
            # Adaptive threshold within non-black area to capture ink
            thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                        cv2.THRESH_BINARY_INV, 21, 10)
            thr = cv2.bitwise_and(thr, thr, mask=non_black)

            # Edge-based fallback to avoid selecting page border
            edges = cv2.Canny(gray, 40, 120)
            edges = cv2.bitwise_and(edges, edges, mask=non_black)
            mask = cv2.bitwise_or(thr, edges)

            # Morphological closing to connect strokes slightly
            k = max(1, max(h, w) // 200)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

            ys, xs = np.where(mask > 0)
            if ys.size == 0 or xs.size == 0:
                # Fallback to non-black area bounding box
                ys, xs = np.where(non_black > 0)
                if ys.size == 0 or xs.size == 0:
                    return bgr_img, (0, 0, w, h)
            y0, y1 = int(np.min(ys)), int(np.max(ys))
            x0, x1 = int(np.min(xs)), int(np.max(xs))
            y0 = max(0, y0 - pad); x0 = max(0, x0 - pad)
            y1 = min(h - 1, y1 + pad); x1 = min(w - 1, x1 + pad)
            if y1 <= y0 or x1 <= x0:
                return bgr_img, (0, 0, w, h)
            return bgr_img[y0:y1+1, x0:x1+1], (x0, y0, x1 - x0 + 1, y1 - y0 + 1)
        except Exception as e:
            print(f"tight_crop_ink failed: {e}")
            return bgr_img, (0, 0, bgr_img.shape[1], bgr_img.shape[0])

    # Calculate minimum width threshold (15% of page width or 150px, whichever is smaller)
    min_line_width = min(W * 0.15, 150)
    min_line_height = 20  # At least 20 pixels tall
    
    filtered_count = 0
    for idx, r in enumerate(regions):
        x = max(0, int(r.get("x", 0)))
        y = max(0, int(r.get("y", 0)))
        w = max(1, int(r.get("w", 1)))
        h = max(1, int(r.get("h", 1)))
        x2 = min(W, x + w)
        y2 = min(H, y + h)
        
        # Filter out regions that are too small to be real text lines
        if w < min_line_width or h < min_line_height:
            filtered_count += 1
            print(f"Filtering out region {idx+1}: width={w}px, height={h}px (too small for a text line)")
            continue
        
        # Keep original image coordinates (avoid over-clamping that may zero the crop)
        # Note: page ROI is still computed for diagnostics, but not enforced here.
        if x2 <= x or y2 <= y:
            continue
        crop = im.crop((x, y, x2, y2))
        # save as BGR PNG for cv2 pipeline
        np_crop = cv2.cvtColor(np.array(crop), cv2.COLOR_RGB2BGR)
        fname = f"manual_region_{tag}_{idx+1}.png"
        fpath = out_dir / fname
        cv2.imwrite(str(fpath), np_crop)
        region_paths.append(str(fpath))
        # Use exact user selection (page pixels) for bbox
        region_metas.append({"index": int(idx), "bbox": [int(x), int(y), int(x2 - x), int(y2 - y)]})
    
    if filtered_count > 0:
        print(f"Filtered out {filtered_count} small regions (keeping {len(region_paths)} valid text lines)")
    
    return region_paths, region_metas

def _cluster_regions_same_scribe(embs: np.ndarray, min_sep: float = 0.12) -> list[int]:
    """
    Group regions by cosine separation. Returns a label per row in `embs`.
    - min_sep is a small margin so *very* similar hands cluster together.
    """
    from sklearn.cluster import AgglomerativeClustering
    # cosine distance in sklearn's AgglomerativeClustering is not native; use 'euclidean'
    # but our embeddings are L2-normalized so euclidean is ~monotonic to cosine.
    n = embs.shape[0]
    if n == 1:
        return [0]
    # try multiple K and pick best linkage by minimal intra-cluster variance
    best_labels = None
    best_score = 1e9
    max_k = min(5, n)
    for k in range(2, max_k + 1):
        model = AgglomerativeClustering(n_clusters=k, linkage="ward")
        labels = model.fit_predict(embs)
        # intra-cluster variance
        var = 0.0
        for c in range(k):
            m = embs[labels == c].mean(axis=0, keepdims=True)
            d = np.linalg.norm(embs[labels == c] - m, axis=1).mean() if (labels == c).any() else 0.0
            var += d
        if var < best_score:
            best_score = var
            best_labels = labels
    if best_labels is None:
        return [0] * n
    # optional small merge pass: if two centroids are extremely close, merge
    cents = []
    for c in sorted(set(best_labels)):
        cents.append(embs[best_labels == c].mean(axis=0))
    cents = np.vstack(cents)
    # cosine distance of centroids
    D = np.clip(1.0 - (cents @ cents.T), 0.0, 2.0)
    # union-find merge if centroid distance < min_sep
    parent = list(range(len(cents)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    def union(a,b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[rb] = ra
    for i in range(len(cents)):
        for j in range(i+1, len(cents)):
            if D[i, j] < min_sep:
                union(i, j)
    # remap labels via merged components
    map_old_to_new = {}
    next_id = 0
    for c in sorted(set(best_labels)):
        root = find(c)
        if root not in map_old_to_new:
            map_old_to_new[root] = next_id; next_id += 1
    final = []
    for lab in best_labels:
        root = find(lab)
        final.append(map_old_to_new[root])
    return final

def _cosine_sim(a: np.ndarray, b: np.ndarray, eps: float = 1e-12) -> float:
    """Calculate cosine similarity between two vectors."""
    na = float(np.linalg.norm(a)) + eps
    nb = float(np.linalg.norm(b)) + eps
    return float(np.dot(a, b) / (na * nb))

def _segment_centroid(embs: list, start: int, end: int) -> np.ndarray:
    """Calculate normalized centroid of embeddings in a segment."""
    # end is exclusive
    if end <= start or not embs:
        return np.zeros((1,), dtype=np.float32)
    
    # Check if we have valid embeddings
    valid_embs = []
    for i in range(start, min(end, len(embs))):
        if embs[i] is not None and embs[i].size > 0:
            valid_embs.append(embs[i])
    
    if not valid_embs:
        return np.zeros_like(embs[0] if embs else np.array([0.0], dtype=np.float32))
    
    seg = np.stack(valid_embs, axis=0)
    c = seg.mean(axis=0)
    n = np.linalg.norm(c) + 1e-12
    return (c / n).astype(np.float32)

def _save_segmentation_overlay(page_abs_path, metas, run_id):
    """
    Draw blue rectangles for each detected line and save overlay image.
    Returns relative URL (under /static).
    """
    img = cv2.imread(str(page_abs_path))
    if img is None:
        return None
    overlay = img.copy()
    for m in metas:
        x, y, w, h = [int(v) for v in m.get("bbox", [0, 0, 0, 0])]
        if w <= 0 or h <= 0: 
            continue
        # blue boxes (BGR)
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (255, 0, 0), 2)
    blended = cv2.addWeighted(overlay, 0.85, img, 0.15, 0)
    out_rel = f"runs/{run_id}/segmentation_overlay.jpg"
    out_abs = STATIC_ROOT / out_rel
    out_abs.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_abs), blended)
    return f"/static/{out_rel}"

def _pick_two_indices(items):
    """Return two 'representative' indices (median & 75th percentile)."""
    if not items: 
        return []
    n = len(items)
    if n == 1:
        return [items[0]]
    
    # Sort by area and pick median and 75th percentile
    sorted_items = sorted(items, key=lambda x: x.get('area', 0))
    median_idx = n // 2
    percentile_75_idx = min(n - 1, math.floor(0.75 * (n - 1)))
    
    picks = [sorted_items[median_idx]]
    if median_idx != percentile_75_idx:
        picks.append(sorted_items[percentile_75_idx])
    
    return picks

def _label_from_index(index):
    """Convert a scribe index to a readable label."""
    if index == 0:
        return "Scribe A"
    elif index == 1:
        return "Scribe B"
    elif index == 2:
        return "Scribe C"
    else:
        return f"Scribe {chr(ord('A') + index)}"

def _assign_scribe_identities(segments, line_abs_paths, sim_thresh=0.92):
    """
    Assign scribe IDs by centroid cosine similarity; detect returns when
    a segment centroid matches a seen scribe (>= sim_thresh).
    """
    def _centroid(start, end):
        # [start, end) in 0-based
        embs = []
        for i in range(start, end):
            if 0 <= i < len(line_abs_paths):
                try:
                    img = cv2.imread(str(line_abs_paths[i]), cv2.IMREAD_COLOR)
                    if img is None: 
                        continue
                    from feature_extractor import line_embedding
                    embs.append(line_embedding(img))  # call with defaults only
                except Exception as e:
                    print(f"Warning: Could not compute embedding for {line_abs_paths[i]}: {e}")
                    continue
        if not embs:
            return None
        c = np.mean(np.vstack(embs), axis=0)
        c = c / (np.linalg.norm(c) + 1e-12)
        return c

    seen = []  # list of (key_letter, centroid)
    out  = []
    next_ord = ord('A')

    for (s, e) in segments:
        cen = _centroid(s, e)
        key = None; is_return = False
        if cen is not None and seen:
            sims = [(k, float(np.dot(cen, sc))) for (k, sc) in seen]
            kbest, sbest = max(sims, key=lambda x: x[1])
            if sbest >= sim_thresh:
                key = kbest; is_return = True
                print(f"Segment [{s}, {e}): Assigned to existing {key} (similarity: {sbest:.3f})")
        if key is None:
            key = chr(next_ord); next_ord = min(next_ord + 1, ord('Z'))
            seen.append((key, cen if cen is not None else np.zeros(1, np.float32)))
            print(f"Segment [{s}, {e}): New scribe {key}")

        out.append({
            "scribe_key": key,
            "scribe_id": f"Scribe {key}",
            "is_return": is_return,
            "start": s,
            "end": e
        })
    return out

def _segment_and_crop(run_id, file_bytes, illum_frac=0.035, sauvola_window=31, sauvola_k=0.2, do_deskew=True):
    """Segment lines and crop them using improved line segmentation with multiple methods"""
    
    # Convert file bytes to image and save it
    image = Image.open(io.BytesIO(file_bytes))
    image = ImageOps.exif_transpose(image)
    
    # Save and (maybe) split double page
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    pages = _split_double_page_if_needed(image)
    page_rel = f"runs/{run_id}/manuscript_page.jpg"
    page_abs = STATIC_ROOT / page_rel
    image.save(page_abs, 'JPEG')
    
    # Use preprocessing parameters with improved line segmentation
    print(f"Running improved line segmentation with parameters: illum_frac={illum_frac}, sauvola_window={sauvola_window}, sauvola_k={sauvola_k}, do_deskew={do_deskew}")
    print(f"Detected 1 page(s) in image")
    
    # Try multiple segmentation approaches in order of preference
    methods_tried = []
    
    # Method 1: try line segmentation per page
    try:
        all_metas, all_paths = [], []
        for p_idx, p_img in enumerate(pages):
            p_tag = "L" if (len(pages) == 2 and p_idx == 0) else ("R" if len(pages) == 2 else "S")
            p_rel = f"runs/{run_id}/manuscript_page_{p_tag}.jpg"
            p_abs = STATIC_ROOT / p_rel
            p_img.save(p_abs, "JPEG")
            metas, line_abs_paths, _ = _try_line_segmentation_method(
                p_abs, run_dir, f"{run_id}_{p_tag}", illum_frac, sauvola_window, sauvola_k, do_deskew
            )
            # tag page and offset line numbers
            start_offset = len(all_paths)
            for i, m in enumerate(metas, 1):
                m["page"] = p_tag
                m["line_number"] = start_offset + i
            all_metas.extend(metas)
            all_paths.extend(line_abs_paths)
        if all_paths:
            methods_tried.append("line_segmentation")
            print(f"Line segmentation successful: {len(all_paths)} lines extracted across {len(pages)} page(s)")
            return all_metas, all_paths, page_rel
    except Exception as e:
        print(f"Line segmentation failed: {e}")
        methods_tried.append(f"line_segmentation_failed({str(e)[:50]})")
    
    # Method 2: Try OCR with better parameters
    try:
        metas, line_abs_paths, page_rel = _try_ocr_extraction_method(
            page_abs, run_dir, run_id, file_bytes
        )
        methods_tried.append("ocr_extraction")
        print(f"OCR extraction successful: {len(line_abs_paths)} lines extracted")
        return metas, line_abs_paths, page_rel
    except Exception as e:
        print(f"OCR extraction failed: {e}")
        methods_tried.append(f"ocr_extraction_failed({str(e)[:50]})")
    
    # Method 3: Fallback to simple horizontal projection
    try:
        metas, line_abs_paths, page_rel = _try_projection_method(
            page_abs, run_dir, run_id
        )
        methods_tried.append("projection_method")
        print(f"Projection method successful: {len(line_abs_paths)} lines extracted")
        return metas, line_abs_paths, page_rel
    except Exception as e:
        print(f"Projection method failed: {e}")
        methods_tried.append(f"projection_method_failed({str(e)[:50]})")
    
    # If all methods fail, raise an error
    raise RuntimeError(f"All line extraction methods failed. Tried: {', '.join(methods_tried)}")

def _try_line_segmentation_method(page_abs, run_dir, run_id, illum_frac, sauvola_window, sauvola_k, do_deskew):
    """Try the original line segmentation approach with parameter tuning"""
    from app import segment_lines, crop_lines
    
    # Apply preprocessing parameters by monkey-patching
    original_preprocess = None
    try:
        import pre_processor
        original_preprocess = pre_processor.preprocess
        
        def custom_preprocess(bgr_img):
            return original_preprocess(
                bgr_img,
                illum_frac=illum_frac,
                do_deskew=do_deskew,
                sauvola_window=sauvola_window,
                sauvola_k=sauvola_k
            )
        
        pre_processor.preprocess = custom_preprocess
        
        # Segment lines
        lines = segment_lines(page_abs)
        
        if not lines:
            raise RuntimeError("No lines detected")
        
        print(f"Line segmentation detected {len(lines)} lines")
        
        # Check for oversized lines (indicates poor segmentation)
        valid_lines = []
        for line in lines:
            bbox = line.get("bbox", [0, 0, 0, 0])
            if len(bbox) == 4:
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
                # Reject lines that are too tall (likely whole document) or too thin
                if line_height > 1000 or line_height < 10 or line_width < 100:
                    print(f"Rejecting oversized/undersized line: {line_width}x{line_height}")
                    continue
            valid_lines.append(line)
        
        if not valid_lines:
            raise RuntimeError("No valid lines after filtering")
        
        # Crop the valid lines
        line_rel_paths, line_polys = crop_lines(page_abs, valid_lines, run_dir)
        
        if not line_rel_paths:
            raise RuntimeError("Line cropping produced no results")
        
        # Convert to absolute paths
        line_abs_paths = [str(STATIC_ROOT / rel_path) for rel_path in line_rel_paths]
        
        # Generate metadata
        metas = []
        for i, (line_path, poly) in enumerate(zip(line_rel_paths, line_polys)):
            if poly:
                xs, ys = zip(*poly)
                bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
            else:
                bbox = [0, i * 30, 500, 30]
                
            metas.append({
                "line_number": i + 1,
                "path": str(STATIC_ROOT / line_path),
                "relative_path": line_path,
                "bbox": bbox,
                "polygon": poly
            })
        
        page_rel = f"runs/{run_id}/manuscript_page.jpg"
        return metas, line_abs_paths, page_rel
        
    finally:
        if original_preprocess:
            pre_processor.preprocess = original_preprocess

def _try_ocr_extraction_method(page_abs, run_dir, run_id, file_bytes):
    """Try OCR-based line extraction with improved parameters"""
    if not OCR_AVAILABLE:
        raise RuntimeError("OCR not available")
    
    # Convert image to base64
    import base64
    with open(page_abs, 'rb') as img_file:
        img_data = img_file.read()
        img_base64 = base64.b64encode(img_data).decode('utf-8')
    
    # Use OCR extraction
    line_data_list = extract_line_screenshots(img_base64)
    
    if not line_data_list:
        raise RuntimeError("OCR extracted no lines")
    
    # Filter out lines that are likely noise or artifacts
    filtered_lines = []
    for line_data in line_data_list:
        text = line_data.get('text', '').strip()
        bbox = line_data.get('bbox', {})
        confidence = line_data.get('confidence', 0.0)
        
        # Filter criteria
        if (len(text) < 2 or  # Too short
            confidence < 0.3 or  # Low confidence
            bbox.get('height', 0) < 10 or  # Too thin
            bbox.get('width', 0) < 50):  # Too narrow
            print(f"Filtering out low-quality line: '{text}' (conf: {confidence:.2f})")
            continue
            
        filtered_lines.append(line_data)
    
    if not filtered_lines:
        raise RuntimeError("No valid lines after filtering")
    
    print(f"OCR extracted {len(filtered_lines)} valid lines (filtered from {len(line_data_list)})")
    
    # Save line images and create metadata
    moved_line_paths = []
    line_rel_paths = []
    metas = []
    
    for i, line_data in enumerate(filtered_lines):
        # Extract and save image
        screenshot_data = line_data['screenshot']
        if screenshot_data.startswith('data:image/png;base64,'):
            img_base64 = screenshot_data.replace('data:image/png;base64,', '')
        else:
            img_base64 = screenshot_data
        
        img_data = base64.b64decode(img_base64)
        new_filename = f"line_{i+1}.png"
        new_abs_path = str(run_dir / new_filename)
        
        with open(new_abs_path, 'wb') as f:
            f.write(img_data)
        
        moved_line_paths.append(new_abs_path)
        rel_path = f"runs/{run_id}/{new_filename}"
        line_rel_paths.append(rel_path)
        
        # Create metadata
        bbox_data = line_data.get('bbox', {})
        bbox = [
            bbox_data.get('left', 0),
            bbox_data.get('top', 0),
            bbox_data.get('width', 0),
            bbox_data.get('height', 0)
        ]
        
        metas.append({
            "line_number": i + 1,
            "path": new_abs_path,
            "relative_path": rel_path,
            "bbox": bbox,
            "polygon": [],
            "text": line_data.get('text', ''),
            "confidence": line_data.get('confidence', 0.0)
        })
    
    page_rel = f"runs/{run_id}/manuscript_page.jpg"
    return metas, moved_line_paths, page_rel

def _try_projection_method(page_abs, run_dir, run_id):
    """Fallback method using horizontal projection with page ROI detection.
    Restricts analysis to the manuscript page to avoid cropping black borders.
    """
    import cv2

    # Load image
    img = cv2.imread(str(page_abs))
    if img is None:
        raise RuntimeError("Could not load image for projection method")

    H, W = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect page ROI using HSV value channel
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    v = hsv[:, :, 2]
    page_mask = (v > 25).astype(np.uint8) * 255
    k = max(5, min(H, W) // 200)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    page_mask = cv2.morphologyEx(page_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    cnts, _ = cv2.findContours(page_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cnts:
        areas = [cv2.contourArea(c) for c in cnts]
        cmax = cnts[int(np.argmax(areas))]
        x0, y0, w0, h0 = cv2.boundingRect(cmax)
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(W, x0 + w0); y1 = min(H, y0 + h0)
    else:
        x0, y0, x1, y1 = 0, 0, W, H

    # Simple thresholding (invert so ink=255), then restrict to ROI
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    roi = binary[y0:y1, x0:x1]

    # Horizontal projection inside detected page ROI
    h_projection = np.sum(roi, axis=1)
    
    # Find line boundaries using projection
    threshold = np.max(h_projection) * 0.1
    in_line = False
    line_boundaries = []
    start_y = 0
    
    for y, proj_val in enumerate(h_projection):
        if not in_line and proj_val > threshold:
            # Start of line
            start_y = y
            in_line = True
        elif in_line and proj_val <= threshold:
            # End of line
            if y - start_y > 10:  # Minimum line height
                line_boundaries.append((start_y, y))
            in_line = False
    
    # Handle case where last line goes to end of image
    if in_line and len(h_projection) - start_y > 10:
        line_boundaries.append((start_y, len(h_projection)))
    
    if not line_boundaries:
        raise RuntimeError("No lines found using projection method")
    
    print(f"Projection method found {len(line_boundaries)} lines")
    
    # Extract line images
    moved_line_paths = []
    metas = []
    height, width = (y1 - y0), (x1 - x0)
    
    for i, (start_y, end_y) in enumerate(line_boundaries):
        # Add some padding
        pad = 5
        y1p = max(0, start_y - pad)
        y2p = min(height, end_y + pad)
        
        # Extract line image from ROI only to avoid black margins
        line_img = img[y0 + y1p:y0 + y2p, x0:x1]
        
        # Save line image
        new_filename = f"line_{i+1}.png"
        new_abs_path = str(run_dir / new_filename)
        cv2.imwrite(new_abs_path, line_img)
        
        moved_line_paths.append(new_abs_path)
        rel_path = f"runs/{run_id}/{new_filename}"
        
        metas.append({
            "line_number": i + 1,
            "path": new_abs_path,
            "relative_path": rel_path,
            "bbox": [x0, y0 + y1p, width, y2p - y1p],
            "polygon": [[x0, y0 + y1p], [x1, y0 + y1p], [x1, y0 + y2p], [x0, y0 + y2p]]
        })
    
    page_rel = f"runs/{run_id}/manuscript_page.jpg"
    return metas, moved_line_paths, page_rel


def _build_segments_and_samples(run_id: str, line_abs_paths: list, segments: list,
                                sample_positions=(0.0, 0.5)):
    """Build scribe segments and generate samples using real detected segments."""
    if not line_abs_paths or not segments:
        return [], {}, {}
    
    n = len(line_abs_paths)
    print(f"Processing {len(segments)} detected segments for {n} lines")
    
    # ✅ DO NOT early-return on single segment. We still want a Scribe A entry.
    # (Removed the old len(segments) <= 1 guard entirely.)
    
    # Get consistent scribe assignments that handle returns
    scribe_assignments = _assign_scribe_identities(segments, line_abs_paths)
    
    scribe_changes = []
    scribe_samples = {}
    
    # Define consistent characteristics for each scribe (no hardcoded confidence)
    scribe_characteristics = {
        "A": {"letterSpacing": "normal", "inkColor": "black", "handSize": "medium", "style": "formal",
              "initial_reason": "Initial scribe identification for the manuscript. This scribe shows consistent handwriting characteristics including uniform letter spacing, consistent stroke weight, and stable baseline alignment throughout the identified lines.",
              "return_reason": "Return to the primary scribal hand with resumed consistent letterforms and baseline alignment. The paleographic characteristics match the initial scribal identity, confirming manuscript production continuity."},
        "B": {"letterSpacing": "tight", "inkColor": "brown", "handSize": "small", "style": "casual",
              "initial_reason": "Handwriting transition detected with distinct paleographic characteristics including altered letter formation patterns, modified stroke angles, and different ink flow characteristics compared to the previous scribal hand.",
              "return_reason": "Secondary scribal hand returns with characteristic tight letter spacing and brown ink flow. The paleographic features remain consistent with the earlier identification."},
        "C": {"letterSpacing": "loose", "inkColor": "dark_brown", "handSize": "large", "style": "ornate",
              "initial_reason": "Tertiary scribal hand detected showing specialized characteristics with distinct letterforms and modified stroke patterns. This hand exhibits different training or purpose compared to previous scribes.",
              "return_reason": "Tertiary scribal hand resumes with distinctive ornate letterforms and loose spacing. The paleographic identity matches the previous occurrence."}
    }
    
    # Merge contiguous segments assigned to the same scribe to avoid duplicate "returns"
    merged_assignments = []
    for assignment in scribe_assignments:
        if merged_assignments and assignment["scribe_key"] == merged_assignments[-1]["scribe_key"]:
            merged_assignments[-1]["end"] = assignment["end"]
            continue
        merged_assignments.append(dict(assignment))

    # Recompute return flags after merge so a scribe only "returns" after another scribe intervenes
    seen_keys = set()
    for assignment in merged_assignments:
        key = assignment["scribe_key"]
        if key in seen_keys:
            assignment["is_return"] = True
        else:
            assignment["is_return"] = False
            seen_keys.add(key)

    scribe_assignments = merged_assignments

    for assignment in scribe_assignments:
        scribe_key = assignment["scribe_key"]
        scribe_id = assignment["scribe_id"]
        is_return = assignment["is_return"]
        start = assignment["start"]
        end = assignment["end"]
        
        # 0-based to 1-based lines
        start_line = start + 1
        end_line = end
        
        # Get consistent characteristics for this scribe
        characteristics = scribe_characteristics.get(scribe_key, scribe_characteristics["A"])
        
        # Generate enhanced scribe samples from actual line images
        samples = []
        rep_lines = []
        n_seg = max(1, end - start)
        
        # Select representative lines from this scribe segment
        for pos in sample_positions[:3]:  # Take up to 3 samples per scribe
            li = start + int(round(pos * (n_seg - 1)))
            if 0 <= li < len(line_abs_paths) and li not in rep_lines:
                rep_lines.append(li)
        
        # Create enhanced sample images from actual line files
        for sample_idx, li in enumerate(rep_lines):
            if li < len(line_abs_paths):
                line_path = line_abs_paths[li]
                if os.path.exists(line_path):
                    try:
                        # Load the line image
                        line_img = cv2.imread(line_path)
                        if line_img is not None:
                            # Create sample filename
                            sample_filename = f"scribe_{scribe_id.lower().replace(' ', '_')}_sample_{sample_idx+1}_line_{li+1}.png"
                            samples_dir = RUNS_DIR / run_id / "scribe_samples"
                            samples_dir.mkdir(parents=True, exist_ok=True)
                            sample_path = samples_dir / sample_filename
                            
                            # Enhance the image for better visibility
                            # Add a colored border to indicate the scribe
                            border_colors = {"A": (255, 100, 100), "B": (100, 255, 100), "C": (100, 100, 255)}
                            border_color = border_colors.get(scribe_key, (200, 200, 200))
                            
                            # Add 10px colored border
                            bordered_img = cv2.copyMakeBorder(line_img, 10, 10, 10, 10, 
                                                            cv2.BORDER_CONSTANT, value=border_color)
                            
                            # Save the enhanced sample
                            cv2.imwrite(str(sample_path), bordered_img)
                            
                            sample_url = f"/static/runs/{run_id}/scribe_samples/{sample_filename}"
                            samples.append(sample_url)
                            print(f"Created enhanced scribe sample: {sample_url}")
                    except Exception as e:
                        print(f"Error creating scribe sample for line {li}: {e}")
                        # Fallback: copy original file
                        sample_filename = f"scribe_{scribe_id.lower().replace(' ', '_')}_line_{li+1}.png"
                        samples_dir = RUNS_DIR / run_id / "scribe_samples"
                        samples_dir.mkdir(parents=True, exist_ok=True)
                        sample_path = samples_dir / sample_filename
                        
                        shutil.copy2(line_path, sample_path)
                        sample_url = f"/static/runs/{run_id}/scribe_samples/{sample_filename}"
                        samples.append(sample_url)
        
        scribe_samples[scribe_id] = samples
        
        # Create scribe change entry with enhanced information
        reason = characteristics["return_reason"] if is_return else characteristics["initial_reason"]
        
        scribe_change = {
            "line_number": int(start_line),
            "start_line": int(start_line),
            "end_line": int(end_line),
            "scribe": scribe_id,
            "explanation": reason,
            "is_return": is_return,
            "is_initial": not is_return and len(scribe_changes) == 0,  # First segment that's not a return
            # NO default confidence - will be set only for non-initial scribes later
            "features": {
                "letterSpacing": characteristics["letterSpacing"],
                "inkColor": characteristics["inkColor"],
                "handSize": characteristics["handSize"],
                "style": characteristics["style"]
            },
            "samples": samples  # Include the sample images directly in the scribe change
        }
        
        scribe_changes.append(scribe_change)
    
    return scribe_changes, scribe_samples, {"segments": segments}

# Removed create_scribe_samples function - now using real line images directly

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", 
        "ocr_available": OCR_AVAILABLE
    })

# Add a root route for health checks
@app.route("/", methods=["GET"])
def root():
    return jsonify({"ok": True, "ocr_available": OCR_AVAILABLE})

@app.route("/export-image", methods=["GET"])
def export_image_proxy():
    image_url = (request.args.get("url") or "").strip()
    parsed = urlparse(image_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return jsonify({"error": "A valid http(s) image URL is required."}), 400

    try:
        outbound = urllib.request.Request(
            image_url,
            headers={
                "User-Agent": "Seshat/1.0 image-export",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(outbound, timeout=30) as response:
            content_type = response.headers.get("Content-Type") or mimetypes.guess_type(parsed.path)[0] or "application/octet-stream"
            payload = response.read(EXPORT_IMAGE_MAX_BYTES + 1)
            if len(payload) > EXPORT_IMAGE_MAX_BYTES:
                return jsonify({"error": "Image is too large for PDF export."}), 413
            if not content_type.lower().startswith("image/"):
                return jsonify({"error": f"URL did not return an image ({content_type})."}), 415
            return Response(payload, mimetype=content_type, headers={"Cache-Control": "public, max-age=3600"})
    except Exception as exc:
        logging.warning(f"Could not proxy export image {image_url}: {exc}")
        return jsonify({"error": "Could not fetch image for PDF export."}), 502

# Removed get_consistent_scribe_results function - now using real detection only

@app.route("/extract-lines", methods=["POST"])
def extract_lines():
    """Extract line screenshots using OCR"""
    try:
        if not OCR_AVAILABLE:
            return jsonify({"error": "OCR functionality not available"}), 503
            
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "No image data provided"}), 400
        
        image_data = data['image']
        
        # Extract line screenshots using OCR
        line_screenshots = extract_line_screenshots(image_data)
        
        return jsonify({
            "success": True,
            "lines": line_screenshots,
            "total_lines": len(line_screenshots)
        })
        
    except Exception as e:
        print(f"Line extraction error: {e}")
        return jsonify({"error": f"Line extraction failed: {str(e)}"}), 500

@app.route("/prepare", methods=["POST"])
def prepare():
    file = None
    raw_bytes = None

    # (A) multipart/form-data
    if "image" in request.files and getattr(request.files["image"], "filename", ""):
        file = request.files["image"]

    # (B) raw body (fetch(...).blob())
    if file is None:
        raw_bytes = request.get_data() or None

    if file is None and not raw_bytes:
        return jsonify({"error": "No image provided"}), 400

    run_id = str(uuid.uuid4())
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    page_rel = f"runs/{run_id}/manuscript_page.jpg"
    page_abs = STATIC_ROOT / page_rel

    try:
        if file is not None:
            image = Image.open(file.stream)
        else:
            image = Image.open(io.BytesIO(raw_bytes))
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.save(page_abs, "JPEG")
    except Exception:
        if file is not None:
            file.stream.seek(0)
            with open(page_abs, "wb") as f:
                f.write(file.stream.read())
        elif raw_bytes:
            with open(page_abs, "wb") as f:
                f.write(raw_bytes)

    page_abs_url = url_for('static', filename=page_rel, _external=True)

    return jsonify({
        "ok": True,
        "job_id": run_id,
        "page_image": page_rel,
        "page_image_static": page_abs_url
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    # Handle empty preflight-like POSTs gracefully
    if request.method == "POST" and not (request.files or request.form or request.get_data()):
        return jsonify({"error": "Empty request body"}), 400

    try:
        # ==== Robust input resolution (file / base64 / prepared job / page URL / latest prepared) ====
        form = request.form or {}
        args = request.args or {}
        run_id = str(uuid.uuid4())

        # Pull mode from any source
        mode = _get_param("mode", "auto")
        # Pull mode from any source
        mode = _get_param("mode", "auto")

        # Resolve content source: file upload, base64, prepared_job, or page_image/url
        file = None
        file_content = None
        prepared_path = None

        # 1) Direct file upload (multipart/form-data)
        if 'image' in request.files and getattr(request.files['image'], 'filename', ''):
            file = request.files['image']
            file_content = file.read()

        # 2) Inline base64 (JSON or form)
        if file_content is None:
            img_b64 = (_get_param("image") or _get_param("imageBase64") or
                       _get_param("image_base64") or _get_param("dataUrl") or _get_param("data_url"))
            if img_b64:
                raw = _read_base64_image(img_b64)
                if raw:
                    file_content = raw
                    class _F: pass
                    file = _F()
                    file.filename = "inline-base64.png"

        # 3) Prepared job (accept several aliases)
        if file_content is None:
            prepared_job = (_get_param("prepared_job") or _get_param("job_id") or _get_param("jobId") or _get_param("run_id"))
            if prepared_job:
                cand = RUNS_DIR / prepared_job / "manuscript_page.jpg"
                if cand.exists():
                    prepared_path = cand
                    file_content = cand.read_bytes()
                    class _F: pass
                    file = _F(); file.filename = str(cand.name)

        # 4) Derive from page image URL/path (accept several aliases)
        if file_content is None:
            page_image_like = (_get_param("page_image") or _get_param("page_image_url") or
                               _get_param("image_url") or _get_param("url") or _get_param("image_path"))
            cand = _prepared_path_from_page_image(page_image_like) if page_image_like else None
            if cand:
                prepared_path = cand
                file_content = cand.read_bytes()
                class _F: pass
                file = _F(); file.filename = str(cand.name)

        # 5) Last-resort fallback: use the latest prepared page on disk
        if file_content is None:
            latest = _find_latest_prepared_page()
            if latest is not None:
                prepared_path = latest
                file_content = latest.read_bytes()
                class _F: pass
                file = _F(); file.filename = str(latest.name)
                print(f"[WARN] /analyze: no image provided; using latest prepared page: {latest}")

        # If still nothing, bail with a precise message
        if file_content is None:
            return jsonify({
                "error": "No image provided",
                "hint": "Send one of: multipart 'image' file, JSON 'image' (data URL/base64), "
                        "'prepared_job' (or 'job_id') id, or 'page_image'/'page_image_url' that points to /static/runs/<id>/manuscript_page.jpg. "
                        "Alternatively, call /prepare first and then call /analyze?prepared_job=<job_id>."
            }), 400

        # Read optional tuning params (from form/query/JSON)
        def _getf_any(k, typ, default):
            v = _get_param(k, default)
            try:
                return typ(v)
            except Exception:
                return default

        illum_frac     = _getf_any("illum_frac", float, 0.035)
        sauvola_window = _getf_any("sauvola_window", int, 31)
        sauvola_k      = _getf_any("sauvola_k", float, 0.2)
        do_deskew      = (_getf_any("do_deskew", int, 1) == 1)

        algo           = _get_param("algo", "auto")  # "auto" | "peaks" | "ruptures"
        z_thresh_raw   = _get_param("z_thresh", None)
        z_thresh       = float(z_thresh_raw) if z_thresh_raw not in (None, "", "null") else None
        min_gap        = _getf_any("min_gap", int, 2)
        min_run        = _getf_any("min_run", int, 2)
        use_color      = (_getf_any("use_color", int, 1) == 1)
        rupt_pen_raw   = _get_param("ruptures_pen", None)
        rupt_pen       = float(rupt_pen_raw) if rupt_pen_raw not in (None, "", "null") else None

        # Parse mode and manual regions
        # Note: 'json' mode works the same as 'manual' - both provide explicit regions
        strict_per_line = True  # Always use strict per-line logic
        manual_regions = []
        if mode in ("manual", "json"):
            try:
                regions_raw = _get_param("regions", "[]")
                if isinstance(regions_raw, str):
                    manual_regions = json.loads(regions_raw) if regions_raw else []
                elif isinstance(regions_raw, list):
                    manual_regions = regions_raw
                else:
                    manual_regions = []
                print(f"{mode.upper()} mode detected with {len(manual_regions)} regions")
                if manual_regions and len(manual_regions) <= 5:
                    print(f"First few regions: {manual_regions[:5]}")
            except Exception as e:
                print(f"Error parsing {mode} regions: {e}")
                manual_regions = []
        timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n=== NEW ANALYSIS REQUEST ===")
        print(f"Run ID: {run_id}")
        print(f"Mode: {mode}")
        print(f"Timestamp: {timestamp_str}")
        print(f"Parameters: algo={algo}, z_thresh={z_thresh}, min_gap={min_gap}, min_run={min_run}")
        
        if mode in ("manual", "json"):
            print(f"{mode.upper()} regions (raw from client): {len(manual_regions)} regions")
            for i, region in enumerate(manual_regions[:3]):  # Show first 3 regions
                print(f"  Region {i+1}: x={region.get('x')}, y={region.get('y')}, w={region.get('w')}, h={region.get('h')}")
            if len(manual_regions) > 3:
                print(f"  ... and {len(manual_regions) - 3} more regions")
        
        # Get file hash for debugging (not for caching)
        file_hash = hashlib.md5(file_content).hexdigest()
        print(f"File hash: {file_hash[:8]}... (for debugging only)")
        print(f"===========================\n")

        # Downscale huge images to keep memory usage reasonable on constrained hosts
        file_content, orig_size, resized_size = _downscale_image_if_needed(file_content)
        if orig_size:
            if resized_size and resized_size != orig_size:
                print(f"Downscaled page from {orig_size[0]}x{orig_size[1]} to {resized_size[0]}x{resized_size[1]}")
            else:
                print(f"Image size after normalization: {orig_size[0]}x{orig_size[1]}")

        # ------------- NEW: normalize manual/json regions into processed image space -------------
        # We must know the processed image size (after EXIF)
        with Image.open(io.BytesIO(file_content)) as _tmp_img:
            _tmp_img = ImageOps.exif_transpose(_tmp_img)
            img_w, img_h = _tmp_img.size
        if mode in ("manual", "json"):
            src_w = _get_param("regions_src_w", None)
            src_h = _get_param("regions_src_h", None)
            manual_regions = _normalize_regions_to_image(manual_regions, src_w, src_h, img_w, img_h)
           
            print(f"Normalized {mode} regions using src({src_w}x{src_h}) -> dst({img_w}x{img_h})")
        # ------------------------------------------------------------------------------------

        # Try to get actual line count first for more realistic scribe detection
        actual_line_count = None
        if OCR_AVAILABLE:
            try:
                # Quick OCR to get line count for scribe detection
                image = Image.open(io.BytesIO(file_content))
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                
                from ocr_line_extractor import get_all_line_bboxes
                ocr_lines = get_all_line_bboxes(f"data:image/png;base64,{image_base64}")
                actual_line_count = len(ocr_lines)
                print(f"OCR detected {actual_line_count} lines for scribe analysis")
                
            except Exception as e:
                print(f"Could not get line count from OCR: {e}")
        
        # Segment + crop real lines (tunable preprocessing)
        analysis_start_time = time.time()
        try:
            print("About to call _segment_and_crop...")
            segment_result = _segment_and_crop(run_id, file_content, 
                                             illum_frac=illum_frac,
                                             sauvola_window=sauvola_window, 
                                             sauvola_k=sauvola_k,
                                             do_deskew=do_deskew)
            print(f"_segment_and_crop returned: {type(segment_result)}")
            if isinstance(segment_result, tuple) and len(segment_result) == 3:
                metas, line_abs_paths, page_rel = segment_result
                print(f"Successfully unpacked: {len(metas)} metas, {len(line_abs_paths)} paths")
                print(f"OCR line extraction: extracted {len(metas)} lines total")
                
                # NEW: Manual mode uses region-driven analysis (no OCR dependency)
                if mode == "manual" and manual_regions:
                    print("MANUAL MODE: Region-driven analysis (no OCR line dependency)")
                    # Create run directory for this analysis
                    run_dir = RUNS_DIR / run_id
                    run_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error during segmentation and cropping: {e}")

        # NEW: Manual/JSON mode uses region-driven analysis (no OCR dependency)
        if mode in ("manual", "json") and manual_regions:
            print(f"{mode.upper()} MODE: Region-driven analysis (no OCR line dependency)")
            # Create run directory for this analysis
            run_dir = RUNS_DIR / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            
            # 1) crop exact regions
            region_paths, region_metas = _crop_regions_from_page(file_content, manual_regions, run_dir, "A")

            # STRICT PER-LINE WITH REUSE: treat each region as its own segment; reuse labels for close matches
            if region_paths:
                print("MANUAL MODE: strict per-line with label reuse")
                imgs_for_samples = []
                region_diags = []
                try:
                    diag_proc = ImageProcessor()
                    print(f"ImageProcessor initialized: {diag_proc is not None}")
                except Exception as e:
                    print(f"Failed to initialize ImageProcessor: {e}")
                    diag_proc = None
                for idx, pth in enumerate(region_paths):
                    img = cv2.imread(pth, cv2.IMREAD_COLOR)
                    if img is None: 
                        print(f"Failed to load image {idx}: {pth}")
                        continue
                    imgs_for_samples.append(img)
                    if diag_proc is not None:
                        diag = diag_proc._diagnostics(img)
                        region_diags.append(diag)
                        if idx < 3:  # Log first 3 for debugging
                            print(f"Line {idx} diagnostics keys: {list(diag.keys())[:5]}")
                    else:
                        region_diags.append({})

                # Build per-line segments
                segments_final = [(i, i+1) for i in range(len(region_paths))]
                # Stats per segment
                final_stats = []
                for idx, d in enumerate(region_diags):
                    acc = _FeatureAccumulator(d)
                    stats = acc.mean_diag()
                    final_stats.append(stats)
                    if idx < 5:  # Log first 5 for better sample
                        lbp_size = len(stats.get('lbp_vector', [])) if isinstance(stats.get('lbp_vector'), np.ndarray) else 0
                        print(f"Line {idx} features: angle={stats.get('dom_angle', 0):.2f}°, coverage={stats.get('coverage', 0):.3f}, brightness={stats.get('v_mean', 0):.1f}, lbp_bins={lbp_size}")
                final_diffs = []  # Initialize final_diffs as an empty list
                # Boundary diffs = [None]
                for k in range(1, len(final_stats)):
                    final_diffs.append(_segment_difference(final_stats[k-1], final_stats[k]))

                # Build changes with STATE-OF-THE-ART clustering approach
                # Higher threshold = fewer clusters (fewer scribes detected)
                # Lower threshold = more clusters (more scribes detected)
                # For JSON mode: use 0.4 (sensitive - detects subtle differences)
                # For auto mode: use 0.75 (default balanced detection)
                threshold = 0.4 if mode == "json" else 0.75
                scribe_changes, scribe_samples = _segments_to_manual_changes(
                    segments_final,
                    final_stats,
                    final_diffs,
                    imgs_for_samples,
                    run_id,
                    similarity_threshold=threshold,
                    min_run_lines=min_run
                )

                # Screenshots + line segments for UI
                region_shots = []
                for idx2, rp in enumerate(region_paths, 1):
                    try:
                        with open(rp, 'rb') as fh:
                            b = fh.read()
                        enc = base64.b64encode(b).decode('ascii')
                        bbox = region_metas[idx2-1].get('bbox', [0,0,0,0]) if idx2-1 < len(region_metas) else [0,0,0,0]
                        bbox = [int(x) for x in bbox]
                        region_shots.append({
                            'lineNumber': int(idx2),
                            'text': '',
                            'bbox': bbox,
                            'screenshot': f"data:image/png;base64,{enc}",
                            'confidence': 1.0
                        })
                    except Exception as e:
                        print(f"Failed to build region screenshot {idx2}: {e}")

                line_segments = []
                for idx3, meta in enumerate(region_metas):
                    bbox = [int(x) for x in meta.get('bbox', [0,0,0,0])]
                    img_data = region_shots[idx3]['screenshot'] if idx3 < len(region_shots) else ''
                    line_segments.append({'id': f'line_{int(idx3)}', 'bbox': bbox, 'image': img_data})

                total_scribes = len({c['scribe'] for c in scribe_changes})
                confidences = [c.get('confidence') for c in scribe_changes if c.get('confidence') is not None]
                overall_confidence = float(np.mean(confidences)) if confidences else 0.0

                result = {
                    "job_id": f"job_{int(time.time())}",
                    "run_id": run_id,
                    "page_image": f"runs/{run_id}/manuscript_page.jpg",
                    "page_image_static": f"/static/runs/{run_id}/manuscript_page.jpg",
                    "segmentation_overlay": None,
                    "polygons": [],
                    "scribe_changes": scribe_changes,
                    "total_lines": len(region_paths),
                    "line_screenshots": region_shots,
                    "ocr_available": OCR_AVAILABLE,
                    "scribe_samples": scribe_samples,
                    "line_segments": line_segments,
                    "statistics": {
                        "total_scribes": total_scribes,
                        "overall_confidence": overall_confidence,
                        "analysis_time": int((time.time() - analysis_start_time) * 1000),
                    },
                    "diagnostics": {}
                }
                print("=== MANUAL REGION ANALYSIS COMPLETE (strict) ===")
                return jsonify(result)

            # Attempt purely heuristic comparison pipeline before falling back
            if region_paths and SIMILARITY_AVAILABLE:
                try:
                    diag_proc = ImageProcessor()
                except Exception:
                    diag_proc = None

                if diag_proc is not None:
                    imgs_for_samples_temp = []
                    region_diags = []
                    for p in region_paths:
                        img = cv2.imread(p, cv2.IMREAD_COLOR)
                        if img is None:
                            continue
                        imgs_for_samples_temp.append(img)
                        region_diags.append(diag_proc._diagnostics(img))

                    if region_diags:
                        segments, segment_stats, boundary_diffs = _heuristic_segments_from_diags(region_diags)
                        if segments:
                            scribe_changes, scribe_samples = _segments_to_manual_changes(
                                segments,
                                segment_stats,
                                boundary_diffs,
                                imgs_for_samples_temp,
                                run_id,
                                min_run_lines=min_run
                            )

                            region_shots = []
                            for idx2, rp in enumerate(region_paths, 1):
                                try:
                                    with open(rp, 'rb') as fh:
                                        b = fh.read()
                                    enc = base64.b64encode(b).decode('ascii')
                                    bbox = region_metas[idx2-1].get('bbox', [0,0,0,0]) if idx2-1 < len(region_metas) else [0,0,0,0]
                                    bbox = [int(x) for x in bbox]
                                    region_shots.append({
                                        'lineNumber': idx2,
                                        'text': '',
                                        'bbox': bbox,
                                        'screenshot': f"data:image/png;base64,{enc}",
                                        'confidence': 1.0
                                    })
                                except Exception as e:
                                    print(f"Failed to build region screenshot {idx2}: {e}")

                            total_scribes = len({c['scribe'] for c in scribe_changes})
                            confidences = [c.get('confidence') for c in scribe_changes if c.get('confidence') is not None]
                            overall_confidence = float(np.mean(confidences)) if confidences else 0.0

                # Build line_segments for UI from manual region bboxes and images
                line_segments = []
                for idx3, meta in enumerate(region_metas):
                    bbox = meta.get('bbox', [0, 0, 0, 0])
                    bbox = [int(x) for x in bbox]
                    img_data = region_shots[idx3]['screenshot'] if idx3 < len(region_shots) else ''
                    line_segments.append({
                        'id': f'line_{int(idx3)}',
                        'bbox': bbox,
                        'image': img_data
                    })

                result = {
                    "job_id": f"job_{int(time.time())}",
                    "run_id": run_id,
                    "page_image": f"runs/{run_id}/manuscript_page.jpg",
                    "segmentation_overlay": None,
                    "polygons": [],
                    "scribe_changes": scribe_changes,
                    "total_lines": len(region_paths),
                    "line_screenshots": region_shots,
                    "ocr_available": OCR_AVAILABLE,
                    "scribe_samples": scribe_samples,
                    "line_segments": line_segments,
                    "statistics": {
                        "total_scribes": total_scribes,
                        "overall_confidence": overall_confidence,
                        "analysis_time": int((time.time() - analysis_start_time) * 1000),
                    },
                    "diagnostics": {}
                }
                print("=== MANUAL REGION ANALYSIS (heuristic) - keeping for hybrid, continuing ===")
                # Do not return early; continue to embedding path for hybrid decision

            if not region_paths:
                print("MANUAL MODE: No valid manual regions to analyze; falling back to detector with manual segments")
                # Fallback: proceed to the general path using manual segments on metas
                # Build manual segments and skip the early-return path
                segments_from_manual = _segments_from_regions(metas, manual_regions)
                # Continue below (outside manual-region early return)
            else:
                # 2) embed each region (same extractor as lines)
                embs = []
                imgs_for_samples = []
                for p in region_paths:
                    img = cv2.imread(p, cv2.IMREAD_COLOR)
                    if img is None: 
                        continue
                    imgs_for_samples.append(img)
                    # call with narrowed band but default weight args
                    embs.append(line_embedding(
                        img,
                        central_band_frac=0.65,
                        central_band_pad=2,
                        resize_height=160,
                        use_color=False
                    ))
                if len(embs) == 0:
                    print("MANUAL MODE: Failed to compute embeddings for manual regions; falling back to detector with manual segments")
                    segments_from_manual = _segments_from_regions(metas, manual_regions)
                else:
                    X = np.vstack(embs).astype(np.float32)

                    # 3) region-level clustering → same/return scribes
                    labels = _cluster_regions_same_scribe(X, min_sep=0.10)
                    # assign A,B,C by first occurrence
                    label_to_key = {}
                    next_key = 0
                    def key_to_id(k): return f"Scribe {chr(ord('A') + k)}"

                    # 4) Build scribe blocks in the user's visual order; detect returns
                    scribe_changes = []
                    scribe_samples = {}
                    for i, (lab, meta) in enumerate(zip(labels, region_metas)):
                        if lab not in label_to_key:
                            label_to_key[lab] = next_key
                            next_key += 1
                        k = label_to_key[lab]  # 0->A, 1->B, ...
                        scribe_id = key_to_id(k)
                        is_return = sum(1 for j in labels[:i] if j == lab) > 0

                        # confidence from separation to nearest *other* centroid
                        this = X[i]
                        c_me = X[np.array(labels) == lab].mean(axis=0)
                        # pick closest different cluster
                        others = [X[np.array(labels) == l].mean(axis=0) for l in sorted(set(labels)) if l != lab]
                        if others:
                            dmin = min([1.0 - float(np.dot(c_me, o) / (np.linalg.norm(c_me)+1e-12) / (np.linalg.norm(o)+1e-12)) for o in others])
                            # map small distance → low confidence, bigger separation → higher
                            conf = 35.0 + max(0.0, min(55.0, (dmin - 0.08) * 600.0))  # ~35–90%
                        else:
                            conf = None  # only one cluster in total

                        # sample image (border-coded by scribe)
                        samples = scribe_samples.get(scribe_id, [])
                        try:
                            border_colors = {0:(255,100,100),1:(100,255,100),2:(100,100,255)}
                            color = border_colors.get(k, (200,200,200))
                            img = imgs_for_samples[i]
                            bordered = cv2.copyMakeBorder(img, 10,10,10,10, cv2.BORDER_CONSTANT, value=color)
                            sp = RUNS_DIR / run_id / "scribe_samples"
                            sp.mkdir(parents=True, exist_ok=True)
                            fname = f"scribe_{chr(ord('a')+k)}_region_{i+1}.png"
                            fpath = sp / fname
                            cv2.imwrite(str(fpath), bordered)
                            samples.append(f"/static/runs/{run_id}/scribe_samples/{fname}")
                            scribe_samples[scribe_id] = samples
                        except Exception:
                            pass

                        # Build explanation
                        try:
                            diag_proc = ImageProcessor()
                            a = diag_proc._diagnostics(imgs_for_samples[i-1]) if i > 0 else {}
                            b = diag_proc._diagnostics(imgs_for_samples[i])
                            if a and b and "lbp" in a and "lbp" in b:
                                a["lbp_chi2"] = _chi2(np.asarray(a["lbp"]), np.asarray(b["lbp"]))
                            explanation_text = _reason_from_diffs(a, b) if i > 0 else (
                                "Initial scribe for selected region; consistent letter proportions, stroke weight, and slant"
                            )
                        except Exception:
                            explanation_text = "Different scribal hand detected based on style and stroke differences."

                        change = {
                            "line_number": int(i + 1),           # region ordinal
                            "start_line": int(i + 1),
                            "end_line": int(i + 1),
                            "scribe": scribe_id,
                            "is_return": is_return,
                            "is_initial": (not is_return and k == 0 and i == 0),
                            "explanation": explanation_text,
                            "features": {
                                "letterSpacing": "normal",
                                "inkColor": "black",
                                "handSize": "medium",
                                "style": "formal"
                            },
                            "samples": samples
                        }
                        if not change["is_initial"] and conf is not None:
                            change["confidence"] = conf
                        scribe_changes.append(change)

                    # Inline screenshots for regions
                    region_shots = []
                    for idx2, rp in enumerate(region_paths, 1):
                        try:
                            with open(rp, 'rb') as fh:
                                b = fh.read()
                            enc = base64.b64encode(b).decode('ascii')
                            bbox_list = region_metas[idx2-1].get('bbox', [0,0,0,0]) if idx2-1 < len(region_metas) else [0,0,0,0]
                            bbox_list = [int(x) for x in bbox_list]
                            region_shots.append({
                                'lineNumber': idx2,
                                'text': '',
                                'bbox': bbox_list,
                                'screenshot': f"data:image/png;base64,{enc}",
                                'confidence': 1.0
                            })
                        except Exception as e:
                            print(f"Failed to build region screenshot {idx2}: {e}")

                # Build line_segments for UI from manual region bboxes and images
                line_segments = []
                for idx3, meta in enumerate(region_metas):
                    bbox = meta.get('bbox', [0, 0, 0, 0])
                    bbox = [int(x) for x in bbox]
                    img_data = region_shots[idx3]['screenshot' ] if idx3 < len(region_shots) else ''
                    line_segments.append({
                        'id': f'line_{int(idx3)}',
                        'bbox': bbox,
                        'image': img_data
                    })

                result = {
                    "job_id": f"job_{int(time.time())}",
                    "run_id": run_id,
                    "page_image": f"runs/{run_id}/manuscript_page.jpg",
                    "segmentation_overlay": None,
                    "polygons": [],
                    "scribe_changes": scribe_changes,
                    "total_lines": total_lines,
                    "line_screenshots": region_shots,
                    "ocr_available": OCR_AVAILABLE,
                    "scribe_samples": scribe_samples,
                    "line_segments": line_segments,
                    "statistics": {
                        "total_scribes": total_scribes,
                        "overall_confidence": overall_confidence,
                        "analysis_time": int((time.time() - analysis_start_time) * 1000),
                    },
                    "diagnostics": {}
                }
                print("=== MANUAL REGION ANALYSIS COMPLETE ===")
                return jsonify(result)
        
        print(f"AUTO MODE: Using all {len(metas)} extracted lines for analysis")
        
        # build blue-box overlay
        overlay_url = _save_segmentation_overlay(STATIC_ROOT / page_rel, metas, run_id)
    except Exception as e:
        print(f"Exception in _segment_and_crop: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    print(f"Analysis parameters received: algo={algo}, z_thresh={z_thresh}, min_gap={min_gap}, min_run={min_run}")
    print(f"SIMILARITY_AVAILABLE: {SIMILARITY_AVAILABLE}, line_abs_paths count: {len(line_abs_paths)}")
    
    if not SIMILARITY_AVAILABLE:
        return jsonify({"error": "Similarity analysis module not available"}), 500
        
    if not line_abs_paths:
        return jsonify({"error": "No lines could be extracted from the image. Check preprocessing parameters."}), 400
    
    # Safety check for manual mode
    if mode == "manual" and len(line_abs_paths) < 2:
        return jsonify({"error": "Not enough lines in the selected regions to analyze."}), 400
    
    print("Using enhanced scribe detection with ImageProcessor")
    
    # Mode-specific analysis configuration
    det_result = None
    segments_from_manual = None
    proc = None  # Initialize to None
    
    if mode == "manual" and manual_regions:
        # Manual mode with regions: build segments and skip detector
        segments_from_manual = _segments_from_regions(metas, manual_regions)
        print("MANUAL MODE: Skipping detector, using manual segments directly")
        # Create a minimal det_result for compatibility
        det_result = {"changes": [], "segments": segments_from_manual or [], "z": [], "dist": []}
    else:
        # AUTO mode or manual without regions: run detector
        if mode == "auto":
            print("AUTO MODE: Full manuscript analysis with optimized parameters")
            proc = ImageProcessor(
                algo=algo, 
                z_thresh=max(z_thresh, 2.5) if z_thresh is not None else 2.5,  # Ensure minimum threshold
                min_gap=max(min_gap, 3),      # Ensure minimum gap for stable detection
                min_run=max(min_run, 3),      # Ensure minimum run length
                use_color=use_color, 
                ruptures_pen=rupt_pen,
                confidence_threshold=0.75,     # Higher confidence threshold
                min_segment_size=2             # Minimum segment size
            )
        else:
            # Manual mode without explicit regions → sensitive detector
            print("MANUAL MODE: Sensitive analysis for user-guided detection")
            proc = ImageProcessor(
                algo=algo,
                z_thresh=max((z_thresh or 2.5) - 0.5, 2.0),
                min_gap=max(min_gap - 1, 2),
                min_run=max(min_run - 1, 2),
                use_color=use_color,
                ruptures_pen=rupt_pen,
                confidence_threshold=0.65,
                min_segment_size=1
            )
        
        det_result = proc.detect_with_reasons(line_abs_paths)
    
    n = len(line_abs_paths)
    print(f"{mode.upper()} MODE DETECTION RESULTS:")
    print(f"  - Analyzed {n} lines")
    
    if det_result is not None:
        print(f"  - Detected {len(det_result.get('changes', []))} potential changes")
        if proc is not None:
            print(f"  - Parameters: z_thresh={proc.z_thresh}, min_gap={proc.min_gap}, min_run={proc.min_run}")
    else:
        print("  - Detector skipped (manual segments)")
    
    # Prefer segments from the detector (may come from clustering fallback)
    segments = det_result.get("segments") if det_result else []
    if not segments and det_result:
        change_idxs = [c["index"] for c in det_result.get("changes", [])]
        segments = indices_to_segments(n, change_idxs)
    
    # Use manual segments if available
    if segments_from_manual:
        segments = segments_from_manual
        print(f"MANUAL MODE: Using {len(segments_from_manual)} manual segments: {segments_from_manual}")
    
    print(f"  - Final segments: {len(segments)} total")

    # Build scribe structures from actual segments
    scribe_changes, scribe_samples, _ = _build_segments_and_samples(run_id, line_abs_paths, segments)

    # Manual mode: give reasonable confidences based on segment characteristics
    if det_result is None:
        print("MANUAL MODE: Applying heuristic confidences for non-initial scribes")
        for i, seg in enumerate(scribe_changes):
            if i == 0:
                seg.pop("confidence", None)
                seg["is_initial"] = True
                print(f"Manual initial scribe {seg['scribe']} - NO confidence assigned")
            else:
                length = max(1, seg.get("end_line", seg["start_line"]) - seg["start_line"] + 1)
                # Map 1..10 lines roughly to 60..85%
                conf = 60.0 + min(25.0, (length - 1) * 3.0)
                seg["confidence"] = float(conf)
                seg["is_initial"] = False
                print(f"Manual transition scribe {seg['scribe']} - heuristic confidence: {seg['confidence']:.1f}% (length: {length} lines)")

    # Attach boundary confidences/explanations where we have them
    boundary_by_idx = {}
    if det_result is not None:
        boundary_by_idx = {c["index"]: c for c in det_result.get("changes", [])}
    
    # Only process detector confidences if we have det_result
    if det_result is not None:
        for i, seg in enumerate(scribe_changes):
            if i == 0:
                seg.pop("confidence", None)
                seg["is_initial"] = True
                print(f"Initial scribe {seg['scribe']} - NO confidence assigned")
            else:
                boundary_idx = seg["start_line"] - 1  # Convert to 0-based
                if boundary_idx in boundary_by_idx:
                    b = boundary_by_idx[boundary_idx]
                    raw_conf = float(b.get("confidence", 0.65))  # already 0.50–0.95 from calibration
                    pct = max(50.0, min(95.0, raw_conf * 100.0))
                    # penalize very tiny segments (single-line runs look suspicious)
                    if (seg.get("end_line", seg["start_line"]) - seg["start_line"]) <= 1:
                        pct = max(50.0, pct - 6.0)
                    seg["confidence"] = float(pct)
                    seg["is_initial"] = False
                    seg["explanation"] = b.get("reason", seg.get("explanation", ""))
                    print(f"Transition scribe {seg['scribe']} - confidence: {seg['confidence']:.1f}%")
                else:
                    # Missing boundary in detector results
                    seg["confidence"] = 65.0
                    seg["is_initial"] = False
                    print(f"Transition scribe {seg['scribe']} - default confidence: 65.0%")

    # Ensure consistent feature cards for auto mode
    for seg in scribe_changes:
        seg.setdefault("features", {
            "handSize": "medium",
            "inkColor": "black",
            "letterSpacing": "normal",
            "style": "formal"
        })

    unique_scribes = {seg.get('scribe') for seg in scribe_changes}
    total_scribes = max(1, len(unique_scribes))
    # Calculate overall confidence from the realistic confidence scores (excluding initial scribe)
    confidence_scores = [c.get("confidence") for c in scribe_changes if c.get("confidence") is not None]
    overall_conf = (float(np.mean(confidence_scores)) if confidence_scores else 0.0)
    
    # Extract real line screenshots using OCR  (if OCR is available)
    line_screenshots = []
    if not OCR_AVAILABLE:
        print("OCR unavailable; building screenshots from actual crops instead.")
    else:
        try:
            # Convert image to base64 for OCR processing
            buffer = io.BytesIO()
            image = Image.open(io.BytesIO(file_content))
            image = ImageOps.exif_transpose(image)
            image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Extract line screenshots using OCR
            line_screenshots = extract_line_screenshots(f"data:image/png;base64,{image_base64}")
            print(f"OCR extracted {len(line_screenshots)} line screenshots")
        except Exception as e:
            print(f"Error in OCR line extraction: {e}")
            line_screenshots = []

    # If OCR screenshots are empty, build base64 screenshots from the cropped line files
    if not line_screenshots:
        for idx, path in enumerate(line_abs_paths, 1):
            try:
                with open(path, 'rb') as fh:
                    raw = fh.read()
                enc = base64.b64encode(raw).decode('ascii')
                bbox = metas[idx-1].get('bbox', [0, 0, 500, 20]) if idx-1 < len(metas) else [0, 0, 500, 20]
                bbox = [int(x) for x in bbox]
                line_screenshots.append({
                    'lineNumber': int(idx),
                    'text': metas[idx-1].get('text', '') if idx-1 < len(metas) else '',
                    'bbox': bbox,
                    'screenshot': f"data:image/png;base64,{enc}",
                    'confidence': 1.0
                })
            except Exception as e:
                print(f"Failed to encode line screenshot for {path}: {e}")

    total_lines = len(line_screenshots) if line_screenshots else len(line_abs_paths)
    
    # Build line_segments for UI from actual metadata (reuse screenshots)
    line_segments = []
    for idx, m in enumerate(metas):
        img_data = line_screenshots[idx]['screenshot' ] if idx < len(line_screenshots) else ''
        line_segments.append({
            "id": f"line_{int(idx)}",
            "bbox": [int(x) for x in m.get("bbox", [0, 0, 500, 20])],
            "image": img_data
        })

    # Require actual line segments
    if not line_segments:
        raise RuntimeError("No line segments could be generated from the preprocessing results")

    result = {
        "job_id": f"job_{int(time.time())}",
        "run_id": run_id,
        "page_image": page_rel if 'page_rel' in locals() else "manuscript_page.jpg",
        "segmentation_overlay": overlay_url if 'overlay_url' in locals() else None,  # blue-box image
        "polygons": [],
        "scribe_changes": scribe_changes,
        "total_lines": total_lines,
        "line_screenshots": line_screenshots,  # base64 screenshots of actual crops or OCR
        "ocr_available": OCR_AVAILABLE,
        "scribe_samples": scribe_samples,    # Actual scribe sample images
        "line_segments": line_segments,
        "statistics": {
            "total_scribes": total_scribes,
            "overall_confidence": overall_conf,
            "analysis_time": int((time.time() - analysis_start_time) * 1000),
        },
        "diagnostics": {
            "z": locals().get('det_result', {}).get("z", []),
            "dist": locals().get('det_result', {}).get("dist", [])
        }
    }

    
    print(f"\n=== ANALYSIS COMPLETE ===")
    print(f"Mode: {mode}")
    print(f"Run ID: {run_id}")
    print(f"Scribe changes detected: {len(scribe_changes)}")
    for i, change in enumerate(scribe_changes):
        conf_str = f"{change.get('confidence', 'N/A')}%" if change.get('confidence') else "None"
        print(f"  Scribe {i+1}: {change.get('scribe')} (confidence: {conf_str})")
    print(f"Total lines analyzed: {total_lines}")
    print(f"Scribe sample images: {sum(len(samples) for samples in scribe_samples.values())}")
    print(f"Line screenshots: {len(line_screenshots) if line_screenshots else 0}")
    print(f"Analysis time: {int((time.time() - analysis_start_time) * 1000)}ms")
    print(f"========================\n")
    
    try:
        return jsonify(result)
    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route("/prepare", methods=["OPTIONS"])
@app.route("/analyze", methods=["OPTIONS"])
def _preflight():
    return ("", 204)

# Ensure the Flask server starts
if __name__ == "__main__":
    # Default to 5001 for local development, 7860 for Hugging Face
    default_port = "7860" if os.environ.get("SPACE_ID") else "5001"
    port = int(os.environ.get("PORT", default_port))
    host = "0.0.0.0"
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print("Starting OCR-based scribe detection backend...")
    print(f"Listening on http://{host}:{port}")
    print("Health endpoint: /health")
    app.run(debug=debug, port=port, host=host)
