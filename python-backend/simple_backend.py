#!/usr/bin/env python3
# simple_backend.py - JSON API using segmentation + similarity pipeline (repo-aligned)
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import time
import random
import hashlib
import base64
import io
from PIL import Image
import uuid
from pathlib import Path
import math
import cv2
import numpy as np

# Local modules matching the GitHub pipeline
from pre_processor import preprocess
from line_segmentor import LineSegmentor
from similarity import ImageProcessor, indices_to_segments

app = Flask(__name__)
CORS(app)  # Enable CORS for Vue.js frontend

# Create static directory for serving scribe samples
STATIC_DIR = Path(__file__).parent / "static"
RUNS_DIR = STATIC_DIR / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

# Heuristics to filter/save reasonable line crops (align with repo app.py)
# Strongly relaxed to avoid over-filtering; we'll post-filter visually later
MIN_LINE_WIDTH = 10
MAX_LINE_HEIGHT = 5000

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)

def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def _to_bgr_from_bytes(b: bytes) -> np.ndarray:
    arr = np.frombuffer(b, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

def _b64_jpeg(img: np.ndarray, quality: int = 90) -> str:
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    ok, enc = cv2.imencode('.jpg', img, encode_param)
    if not ok:
        _, enc = cv2.imencode('.jpg', img)
    b64 = base64.b64encode(enc.tobytes()).decode('ascii')
    return f"data:image/jpeg;base64,{b64}"

def _label_from_index(i: int) -> str:
    # Scribe A, B, C, ...
    return f"Scribe {chr(ord('A') + i)}"

def _segment_and_crop(run_id: str, image_bytes: bytes):
    """Run preprocessing + line segmentation and save real line crops for this run.
    Returns (line_meta_list, line_abs_paths)
    line_meta_list: [{lineNumber, bbox:[l,u,r,d], url, base64}]
    """
    run_dir = RUNS_DIR / run_id
    lines_dir = run_dir / "lines"
    _ensure_dir(lines_dir)

    # Decode
    bgr = _to_bgr_from_bytes(image_bytes)
    if bgr is None:
        raise RuntimeError("Failed to decode image")

    # Save page copy for UI
    page_path = run_dir / "page.jpg"
    cv2.imwrite(str(page_path), bgr)

    # Preprocess + segment (bw: ink=255, background=0)
    bw = preprocess(bgr)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    H, W = gray.shape[:2]
    metas = []
    abs_paths = []
    idx = 1
    # Primary: projection-based segmentation (robust across scans)
    def _projection_segment_lines(bin_img: np.ndarray):
        h, w = bin_img.shape[:2]
        ink = (bin_img > 0).astype(np.uint8)
        # optional denoise vertically
        vk = max(3, (h // 400) * 2 + 1)
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, vk)))
        row_sum = ink.sum(axis=1)
        # Active rows: at least a tiny fraction of width has ink
        min_row_ink = max(2, int(0.002 * w))
        active = row_sum >= min_row_ink
        idx_rows = np.where(active)[0]
        if idx_rows.size == 0:
            return []
        # Group contiguous rows (blank row splits groups)
        cuts = np.where(np.diff(idx_rows) > 1)[0]
        runs = np.split(idx_rows, cuts + 1)
        boxes = []
        for run in runs:
            u = int(run[0]); d = int(run[-1])
            if d - u < 8:
                continue
            band = ink[u:d+1, :]
            col_sum = band.sum(axis=0)
            cols = np.where(col_sum > 0)[0]
            if cols.size == 0:
                continue
            l = int(cols[0]); r = int(cols[-1])
            pad = 4
            l = max(0, l - pad); r = min(w - 1, r + pad)
            boxes.append((l, u, r, d))
        return boxes

    boundaries = _projection_segment_lines(bw)
    # Fallback to classic segmentor if projection fails
    if len(boundaries) < 2:
        try:
            seg = LineSegmentor(gray, bw)
            boundaries = list(getattr(seg, 'lines_boundaries', [])) or boundaries
        except Exception:
            pass

    produced = 0
    for (l, u, r, d) in boundaries:
        # Clamp and filter
        l = max(0, int(l)); r = min(W-1, int(r))
        u = max(0, int(u)); d = min(H-1, int(d))
        if r < l or d < u: 
            continue
        # Use inclusive bounds from segmentor
        crop = bgr[u:d+1, l:r+1]
        h, w = crop.shape[:2]
        if w < MIN_LINE_WIDTH or h > MAX_LINE_HEIGHT:
            continue
        out_name = f"line_{idx}.jpg"
        out_path = lines_dir / out_name
        cv2.imwrite(str(out_path), crop)
        url = f"/static/runs/{run_id}/lines/{out_name}"
        metas.append({
            "lineNumber": idx,
            "bbox": [l, u, r, d],
            "url": url,
            "screenshot": _b64_jpeg(crop)
        })
        abs_paths.append(str(out_path))
        idx += 1
        produced += 1

    # Salvage pass: if nothing produced, try again without width/height filtering
    if produced == 0 and boundaries:
        idx = 1
        metas.clear(); abs_paths.clear()
        for (l, u, r, d) in boundaries:
            l = max(0, int(l)); r = min(W-1, int(r))
            u = max(0, int(u)); d = min(H-1, int(d))
            if r < l or d < u:
                continue
            crop = bgr[u:d+1, l:r+1]
            if crop.size == 0:
                continue
            out_name = f"line_{idx}.jpg"
            out_path = lines_dir / out_name
            cv2.imwrite(str(out_path), crop)
            url = f"/static/runs/{run_id}/lines/{out_name}"
            metas.append({
                "lineNumber": idx,
                "bbox": [l, u, r, d],
                "url": url,
                "screenshot": _b64_jpeg(crop)
            })
            abs_paths.append(str(out_path))
            idx += 1

    # Fallback: if still nothing, treat the whole page as one line
    if not metas:
        out_name = "line_1.jpg"
        out_path = lines_dir / out_name
        cv2.imwrite(str(out_path), gray)
        metas.append({"lineNumber": 1, "bbox": [0, 0, W-1, H-1], "url": f"/static/runs/{run_id}/lines/{out_name}", "screenshot": _b64_jpeg(gray)})
        abs_paths.append(str(out_path))

    return metas, abs_paths, str(page_path.relative_to(STATIC_DIR)).replace("\\", "/")

def _build_segments_and_samples(run_id: str, line_abs_paths: list):
    """Use ImageProcessor to detect changes, convert to segments, and pick sample images per scribe."""
    proc = ImageProcessor()
    result = proc.detect_with_reasons(line_abs_paths)
    n = len(line_abs_paths)
    change_idxs = [c["index"] for c in result.get("changes", [])]
    segments = indices_to_segments(n, change_idxs)

    # Label scribes A, B, C ...
    scribe_changes = []
    samples_map = {}
    samples_dir = RUNS_DIR / run_id / "scribe_samples"
    _ensure_dir(samples_dir)

    for si, (start, end) in enumerate(segments):
        # 0-based to 1-based lines
        start_line = start + 1
        end_line = end
        scribe = _label_from_index(si)

        # Explanation: use reason at boundary after this segment, if exists
        boundary_idx = end - 1  # change between boundary_idx and boundary_idx+1
        reason = None
        for c in result.get("changes", []):
            if c["index"] == boundary_idx:
                reason = c.get("reason")
                break
        if reason is None:
            reason = "Consistent handwriting within this segment."

        # Representative samples: include start, mid, and optionally end-1
        rep_lines = [start]
        mid = start + (end - start) // 2
        if mid not in rep_lines:
            rep_lines.append(mid)
        if end - start >= 4 and (end - 1) not in rep_lines:
            rep_lines.append(end - 1)

        urls = []
        for li in rep_lines:
            if 0 <= li < n:
                src = Path(line_abs_paths[li])
                dst = samples_dir / f"{scribe.replace(' ', '_').lower()}_line_{li+1}.jpg"
                try:
                    img = cv2.imread(str(src), cv2.IMREAD_COLOR)
                    if img is not None:
                        cv2.imwrite(str(dst), img)
                        urls.append(f"/static/runs/{run_id}/scribe_samples/{dst.name}")
                except Exception:
                    pass
        samples_map[scribe] = urls

        scribe_changes.append({
            "line_number": start_line,
            "start_line": start_line,
            "end_line": end_line,
            "scribe": scribe,
            "confidence": 0.9 if si < len(segments)-1 else 0.8,
            "explanation": reason,
        })

    return scribe_changes, samples_map, result

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/extract-lines", methods=["POST"])
def extract_lines():
    """Extract real line screenshots using segmentation (repo-aligned)."""
    try:
        data = request.files or {}
        file = data.get('image') if 'image' in data else None
        if file is None:
            # Also support JSON base64 image for flexibility
            j = request.get_json(silent=True) or {}
            img_b64 = j.get('image')
            if not img_b64:
                return jsonify({"error": "No image provided"}), 400
            if img_b64.startswith('data:image'):
                img_b64 = img_b64.split(',')[1]
            image_bytes = base64.b64decode(img_b64)
        else:
            image_bytes = file.read()

        run_id = str(uuid.uuid4())
        metas, _paths, _page_rel = _segment_and_crop(run_id, image_bytes)
        return jsonify({"success": True, "lines": metas, "total_lines": len(metas), "run_id": run_id})
    except Exception as e:
        print(f"Line extraction error: {e}")
        return jsonify({"error": f"Line extraction failed: {str(e)}"}), 500

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        # Check if file is present
        if 'image' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({"error": "No file selected"}), 400
        
        # Generate unique run ID and hash
        run_id = str(uuid.uuid4())
        file_bytes = file.read()
        file_hash = hashlib.md5(file_bytes).hexdigest()
        # Segment + crop real lines
        metas, line_abs_paths, page_rel = _segment_and_crop(run_id, file_bytes)
        # Detect changes, build segments and samples
        scribe_changes, scribe_samples, det = _build_segments_and_samples(run_id, line_abs_paths)

        # Build line_segments for UI
        line_segments = []
        for m in metas:
            l, u, r, d = m["bbox"]
            line_segments.append({
                "id": f"line_{m['lineNumber']}",
                "bbox": [l, u, r, d],
                "image": m["url"],
            })

        # Attach samples to scribe_changes for convenience
        for ch in scribe_changes:
            ch["samples"] = scribe_samples.get(ch["scribe"], [])

        result = {
            "job_id": f"job_{int(time.time())}",
            "run_id": run_id,
            "page_image": page_rel,
            "polygons": [],
            "scribe_changes": scribe_changes,
            "total_lines": len(metas),
            "line_screenshots": metas,  # base64 screenshots of actual crops
            "ocr_available": False,
            "scribe_samples": scribe_samples,
            "line_segments": line_segments,
        }

        print(f"Analysis complete: {len(scribe_changes)} scribe segments across {len(metas)} lines")
        return jsonify(result)
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

if __name__ == "__main__":
    print("Starting scribe detection backend (repo-aligned pipeline)...")
    print("Backend: http://localhost:5001")
    print("GET /health | POST /analyze | POST /extract-lines")
    # Run without the reloader to keep a single stable process when backgrounded
    app.run(debug=False, port=5001, host='0.0.0.0', use_reloader=False)
