# app.py
from __future__ import annotations
import os, io, json, uuid, time, shutil, logging
import mimetypes
import urllib.request
from urllib.parse import urlparse
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

import cv2
import numpy as np
from flask import Flask, request, render_template, jsonify, abort, send_file, Response
from werkzeug.utils import secure_filename
from flask_cors import CORS

from similarity import ImageProcessor
from pre_processor import preprocess
from line_segmentor import LineSegmentor
from advanced_scribe_detector import AdvancedScribeDetector
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# ------------------ Helper Functions ------------------
def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return 0.0  # Sanitize NaN/Inf values
    return obj

def assign_scribe_name(index: int) -> str:
    """Generate alphabetic hand labels (A, B, C... Z, then Hand 27, 28, etc.)"""
    if index < 26:
        return f"Hand {chr(ord('A') + index)}"
    return f"Hand {index + 1}"

# ------------------ Config ------------------
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"
JOBS_DIR = STATIC_DIR / "jobs"

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf"}
MAX_CONTENT_LENGTH = 60 * 1024 * 1024  # 60MB
MAX_IMAGE_DIM = int(os.getenv("SESHAT_MAX_IMAGE_DIM", "0"))  # 0 = disabled
EXPORT_IMAGE_MAX_BYTES = int(os.getenv("SESHAT_EXPORT_IMAGE_MAX_BYTES", str(80 * 1024 * 1024)))

# ------------------ Morphological Line Segmentation ------------------
def _ink_mask(binary: np.ndarray) -> np.ndarray:
    # binary is {0,255}; we want 255=ink for morphology
    return ((binary == 0).astype(np.uint8) * 255)

def _segment_lines_morph(binary: np.ndarray) -> List[Tuple[int,int,int,int]]:
    """
    RLSA-style line grouping: returns list of bboxes [L,U,R,D] for the WHOLE page/column.
    Works on noisy parchment, rubrics, initials.
    """
    H, W = binary.shape[:2]
    if H == 0 or W == 0:
        return []

    ink = _ink_mask(binary)

    # Smooth horizontally to connect letters within a line (dynamic kernel).
    kx = max(25, W // 40)      # ~2.5% of page width
    hx = cv2.getStructuringElement(cv2.MORPH_RECT, (kx, 1))
    merged = cv2.dilate(ink, hx, 1)
    merged = cv2.erode(merged, hx, 1)

    # Light vertical shrink to avoid line merging (descenders/ascenders).
    ky = max(3, H // 120)      # ~0.8% of page height
    vy = cv2.getStructuringElement(cv2.MORPH_RECT, (1, ky))
    separated = cv2.erode(merged, vy, 1)

    # Connected components → candidate lines
    num, labels, stats, _ = cv2.connectedComponentsWithStats((separated > 0).astype(np.uint8), 8)
    boxes = []
    # Heuristics by relative size (avoids giant page-spanning blobs and tiny noise)
    min_h = max(8, H // 200)               # avoid tiny slivers
    max_h = max(min(H // 6, 180), min_h)   # avoid blocks that are too tall
    min_w = max(40, W // 8)                # at least 12.5% page width

    for i in range(1, num):
        x, y, w, h, area = stats[i]
        if h < min_h or h > max_h or w < min_w:
            continue
        # expand a few px to include edges
        L = max(0, x - 2); U = max(0, y - 2)
        R = min(W-1, x + w + 2); D = min(H-1, y + h + 2)
        boxes.append([L, U, R, D])

    # sort by Y (top to bottom)
    boxes.sort(key=lambda b: b[1])
    return boxes

# heuristics for cropping lines
MIN_LINE_WIDTH = 150
MAX_LINE_HEIGHT = 800  # Increased to allow larger line segments

JOB_TTL_SEC = 6 * 60 * 60  # cleanup old jobs after 6h

# ------------------ App ------------------
app = Flask(__name__)
CORS(app)  # Enable CORS for Vue.js frontend
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

for d in (STATIC_DIR, UPLOADS_DIR, JOBS_DIR):
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("scribe-app")

# ------------------ Utils ------------------
def allowed_file(name: str) -> bool:
    return Path(name).suffix.lower() in ALLOWED_EXT

def new_job_id() -> str:
    return uuid.uuid4().hex[:12]

def job_paths(job_id: str) -> Dict[str, Path]:
    root = JOBS_DIR / job_id
    lines_dir = root / "lines"
    root.mkdir(parents=True, exist_ok=True)
    lines_dir.mkdir(parents=True, exist_ok=True)
    return {"root": root, "lines": lines_dir}

def cleanup_old_jobs(ttl: int = JOB_TTL_SEC):
    now = time.time()
    for p in JOBS_DIR.glob("*"):
        try:
            if p.is_dir() and (now - p.stat().st_mtime) > ttl:
                shutil.rmtree(p, ignore_errors=True)
        except Exception:
            pass

def clamp_bbox(x0, y0, x1, y1, W, H):
    x0 = max(0, min(int(x0), W - 1)); x1 = max(0, min(int(x1), W))
    y0 = max(0, min(int(y0), H - 1)); y1 = max(0, min(int(y1), H))
    if x1 <= x0: x1 = min(W, x0 + 1)
    if y1 <= y0: y1 = min(H, y0 + 1)
    return x0, y0, x1, y1

# ------------------ Line segmentation ------------------
def _column_or_page_regions(binary: np.ndarray) -> List[Tuple[int,int]]:
    """Stable vertical split: returns [(xL,xR), ...] for columns/pages."""
    ink_col = np.sum((binary == 0).astype(np.uint8), axis=0).astype(np.float32)
    if ink_col.size == 0:
        return [(0, binary.shape[1])]
    # smooth to ignore small gaps (gutter/illumination)
    k = np.ones(31, np.float32) / 31.0
    smooth = np.convolve(ink_col, k, mode="same")
    th = max(8.0, 0.08 * float(smooth.max()))   # 8% of max ink
    blocks = []
    in_blk, s = False, 0
    for x, v in enumerate(smooth):
        if not in_blk and v > th:
            in_blk, s = True, x
        elif in_blk and v <= th:
            if x - s >= 40:
                blocks.append((s, x))
            in_blk = False
    if in_blk and (len(smooth) - s) >= 40:
        blocks.append((s, len(smooth)))
    return blocks if blocks else [(0, binary.shape[1])]

def segment_lines(img_path: Path) -> List[Dict]:
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError("Failed to read uploaded image")

    binary = preprocess(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    H, W = gray.shape[:2]

    lines: List[Dict] = []
    idx = 0

    # Split into vertical regions (columns/pages) first
    regions = _column_or_page_regions(binary)

    for (xL, xR) in regions:
        sub_bin  = binary[:, xL:xR]
        sub_gray = gray[:,   xL:xR]

        # 1) Morphological (RLSA) line grouping
        bboxes = _segment_lines_morph(sub_bin)

        # 2) If too few or too messy, fallback to the old LineSegmentor
        if len(bboxes) < 2:
            try:
                from line_segmentor import LineSegmentor
                seg = LineSegmentor(sub_gray, sub_bin)
                for (l,u,r,d) in (seg.lines_boundaries or []):
                    if (r - l) >= 10 and (d - u) >= 8:
                        bboxes.append([l, u, r, d])
            except Exception:
                pass

        # Re-offset to full image coords and collect
        for (l,u,r,d) in bboxes:
            L = max(0, l + xL); R = min(W-1, r + xL)
            U = max(0, u);      D = min(H-1, d)
            idx += 1
            lines.append({
                "id": f"line_{idx-1}",
                "boundary": [[L,U],[R,U],[R,D],[L,D]],
                "bbox": [L,U,R,D]
            })

    if not lines:
        lines.append({
            "id": "line_0",
            "boundary": [[0,0],[W-1,0],[W-1,H-1],[0,H-1]],
            "bbox": [0,0,W-1,H-1]
        })
    # sort globally by top y (just in case regions overlapped a bit)
    lines.sort(key=lambda ln: ln["bbox"][1])
    return lines

def crop_lines(img_path: Path, lines: List[Dict], out_dir: Path) -> Tuple[List[str], List[List[Tuple[int,int]]]]:
    """Save line crops and also return their polygon boundaries (for animation)."""
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if img is None: raise RuntimeError("Failed to read uploaded image")
    H, W = img.shape[:2]

    rel_paths: List[str] = []
    polys: List[List[Tuple[int,int]]] = []

    idx = 1
    for ln in lines:
        boundary = ln.get("boundary")
        if not boundary or not isinstance(boundary, list) or len(boundary) < 2: 
            print(f"Line {idx}: Skipping - invalid boundary: {boundary}")
            continue
        xs = [pt[0] for pt in boundary]; ys = [pt[1] for pt in boundary]
        x0, y0, x1, y1 = clamp_bbox(min(xs), min(ys), max(xs), max(ys), W, H)
        crop = img[y0:y1, x0:x1]
        if crop.size == 0: 
            print(f"Line {idx}: Skipping - empty crop")
            continue
        
        h, w = crop.shape[:2]
        print(f"Line {idx}: dimensions w={w}, h={h} (MIN_WIDTH={MIN_LINE_WIDTH}, MAX_HEIGHT={MAX_LINE_HEIGHT})")
        if w < MIN_LINE_WIDTH: 
            print(f"Line {idx}: Skipping - width {w} < {MIN_LINE_WIDTH}")
            continue
        if h > MAX_LINE_HEIGHT: 
            print(f"Line {idx}: Skipping - height {h} > {MAX_LINE_HEIGHT}")
            continue

        print(f"Line {idx}: Accepted - saving as line_{idx}.jpg")
        out_name = f"line_{idx}.jpg"
        cv2.imwrite(str(out_dir / out_name), crop)
        rel_paths.append(str((out_dir / out_name).relative_to(STATIC_DIR)).replace("\\", "/"))

        # normalize polygon points to ints and clamp
        poly = [(int(max(0, min(px, W-1))), int(max(0, min(py, H-1)))) for px, py in boundary]
        polys.append(poly)
        idx += 1

    return rel_paths, polys

def draw_segmentation_overlay(img_path: Path, lines: List[Dict], out_path: Path) -> None:
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if img is None:
        return
    overlay = img.copy()
    for ln in lines:
        b = ln.get("bbox", [0,0,0,0])
        L,U,R,D = b if len(b)==4 else (0,0,0,0)
        cv2.rectangle(
            overlay, (L,U), (R,D),
            color=(255, 0, 0),  # BGR: pure blue
            thickness=2
        )
    # semi-transparent draw
    out = cv2.addWeighted(overlay, 0.65, img, 0.35, 0)
    cv2.imwrite(str(out_path), out)

def generate_pdf_report_advanced(job_id: str, scribe_changes: List[Dict], page_image: str, line_rel_paths: List[str]) -> str:
    """
    Generate enhanced PDF report with advanced scribe detection results
    """
    paths = job_paths(job_id)
    pdf_path = paths["root"] / "scribe_analysis_report.pdf"
    
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Advanced Scribe Detection Analysis Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Timestamp
    timestamp = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
    story.append(timestamp)
    story.append(Spacer(1, 0.3*inch))
    
    # Summary
    summary_text = f"""
    <b>Analysis Summary:</b><br/>
    • Total lines analyzed: {len(line_rel_paths)}<br/>
    • Scribe changes detected: {len(scribe_changes)}<br/>
    • Number of different scribes: {len(scribe_changes) + 1}<br/>
    • Detection method: Advanced multi-algorithm analysis
    """
    summary = Paragraph(summary_text, styles['Normal'])
    story.append(summary)
    story.append(Spacer(1, 0.3*inch))
    
    # Original page image
    page_abs_path = str(STATIC_DIR / page_image) if not page_image.startswith("/static/") else str(STATIC_DIR / page_image.replace("/static/", ""))
    if Path(page_abs_path).exists():
        story.append(Paragraph("<b>Original Manuscript Page:</b>", styles['Heading2']))
        page_img = RLImage(page_abs_path, width=5*inch, height=6*inch)
        story.append(page_img)
        story.append(Spacer(1, 0.3*inch))
    
    # Detailed changes
    if scribe_changes:
        story.append(Paragraph("<b>Detected Scribe Changes:</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        for i, change in enumerate(scribe_changes):
            change_text = f"""
            <b>Change #{i+1} - Line {change.get('line_number', i+1)}</b><br/>
            Confidence: {change.get('confidence', 0.0):.1f}%<br/>
            Explanation: {change.get('explanation','')}<br/>
            Statistical Distance: {change.get('distance', 0):.3f}<br/>
            Z-Score: {change.get('z_score', 0):.2f}<br/>
            """
            
            if 'methods_detected' in change:
                change_text += f"Detection Methods: {', '.join(change['methods_detected'])}<br/>"
            
            change_para = Paragraph(change_text, styles['Normal'])
            story.append(change_para)
            story.append(Spacer(1, 0.2*inch))
    else:
        no_changes = Paragraph("No significant scribe changes detected in this manuscript.", styles['Normal'])
        story.append(no_changes)
    
    # Methodology
    story.append(Spacer(1, 0.3*inch))
    methodology_text = """
    <b>Analysis Methodology:</b><br/><br/>
    1. <b>Line Segmentation:</b> The manuscript is automatically segmented into individual text lines
    using advanced computer vision techniques.<br/><br/>
    
    2. <b>Feature Extraction:</b> Multiple handwriting characteristics are analyzed for each line:
    • Stroke width and consistency
    • Curvature and angularity patterns  
    • Letter spacing and word spacing
    • Writing slant angle and consistency
    • Pressure simulation through ink density
    • Letter size consistency
    • Baseline straightness<br/><br/>
    
    3. <b>Multi-Algorithm Detection:</b> Three complementary algorithms analyze the features:
    • Sliding window comparison for local changes
    • Clustering analysis for global patterns
    • Statistical change point detection<br/><br/>
    
    4. <b>Confidence Scoring:</b> Changes are ranked by statistical significance and
    consensus across multiple detection methods.
    """
    methodology = Paragraph(methodology_text, styles['Normal'])
    story.append(methodology)
    
    doc.build(story)
    log.info(f"Advanced PDF report generated: {pdf_path}")
    
    # Return a static URL path for the generated PDF
    rel = str(pdf_path.relative_to(STATIC_DIR)).replace("\\", "/")
    return f"/static/{rel}"

def generate_pdf_report(job_id: str, cards: List[Dict], page_image: str) -> str:
    """Generate PDF report for scribe detection results"""
    paths = job_paths(job_id)
    pdf_path = paths["root"] / "scribe_analysis_report.pdf"
    
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Scribe Detection Analysis Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Summary
    summary_text = f"Analysis completed on {time.strftime('%Y-%m-%d %H:%M:%S')}<br/>"
    summary_text += f"Number of detected scribe changes: {len(cards)}<br/><br/>"
    
    if len(cards) == 0:
        summary_text += "No significant scribe changes were detected in this manuscript. This suggests consistent handwriting throughout the analyzed text."
    else:
        summary_text += "The following potential scribe changes were identified:"
    
    summary = Paragraph(summary_text, styles['Normal'])
    story.append(summary)
    story.append(Spacer(1, 12))
    
    # Add page image if available
    page_img_path = STATIC_DIR / (page_image.replace("/static/","") if page_image.startswith("/static/") else page_image)
    if page_img_path.exists():
        try:
            img_width = 6 * inch
            story.append(Paragraph("Original Manuscript Image:", styles['Heading2']))
            story.append(RLImage(str(page_img_path), width=img_width, height=img_width*0.7))
            story.append(Spacer(1, 12))
        except Exception as e:
            log.warning(f"Could not add image to PDF: {e}")
    
    # Detailed results
    if cards:
        story.append(Paragraph("Detailed Analysis:", styles['Heading2']))
        
        for i, card in enumerate(cards, 1):
            # Change details
            change_text = f"<b>Change #{i}</b><br/>"
            change_text += f"Confidence Level: {card['score']}%<br/>"
            change_text += f"Analysis: {card['reason']}<br/><br/>"
            
            change_para = Paragraph(change_text, styles['Normal'])
            story.append(change_para)
            
            # Add comparison images if available
            left_img_path = STATIC_DIR / card['left']
            right_img_path = STATIC_DIR / card['right']
            
            if left_img_path.exists() and right_img_path.exists():
                try:
                    story.append(Paragraph("Line Comparison:", styles['Heading3']))
                    
                    # Create a simple table-like layout with images
                    img_width = 2.5 * inch
                    story.append(Paragraph("Before:", styles['Normal']))
                    story.append(RLImage(str(left_img_path), width=img_width, height=img_width*0.3))
                    story.append(Paragraph("After:", styles['Normal']))
                    story.append(RLImage(str(right_img_path), width=img_width, height=img_width*0.3))
                    story.append(Spacer(1, 12))
                except Exception as e:
                    log.warning(f"Could not add comparison images to PDF: {e}")
    
    # Methodology
    methodology_text = """
    <b>Methodology:</b><br/>
    This analysis uses computer vision and machine learning techniques to detect changes in handwriting patterns:
    <br/><br/>
    1. <b>Line Segmentation:</b> The manuscript is automatically segmented into individual text lines
    <br/>
    2. <b>Feature Extraction:</b> Each line is analyzed for texture patterns (LBP), stroke orientations (HOG), and ink characteristics
    <br/>
    3. <b>Statistical Analysis:</b> Consecutive lines are compared using distance metrics and statistical tests
    <br/>
    4. <b>Change Detection:</b> Significant deviations in handwriting features indicate potential scribe changes
    <br/><br/>
    The confidence scores represent the statistical significance of detected changes, with higher scores indicating more certain scribe transitions.
    """
    
    methodology = Paragraph(methodology_text, styles['Normal'])
    story.append(methodology)
    
    # Build PDF
    doc.build(story)
    
    rel = str(pdf_path.relative_to(STATIC_DIR)).replace("\\", "/")
    return f"/static/{rel}"

def _normalize_regions_to_image(regions, src_w, src_h, dst_w, dst_h):
    """Map regions from frontend source space to actual image pixel space."""
    out = []
    if not regions:
        return out
    try:
        src_w, src_h = int(src_w or 0), int(src_h or 0)
    except Exception:
        src_w, src_h = 0, 0

    if src_w <= 0 or src_h <= 0:
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

def crop_manual_regions(image_path, regions, output_dir, src_w=0, src_h=0):
    """Crop user-drawn regions from the image with size filtering. Returns list of crop file paths."""
    from PIL import Image, ImageOps
    im = Image.open(image_path)
    im = ImageOps.exif_transpose(im)
    im = im.convert("RGB")
    W, H = im.size

    # Normalize regions from frontend to image space
    norm_regions = _normalize_regions_to_image(regions, src_w, src_h, W, H)

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    min_line_width = min(W * 0.15, 150)
    min_line_height = 20

    for idx, r in enumerate(norm_regions):
        x = max(0, r["x"])
        y = max(0, r["y"])
        w = max(1, r["w"])
        h = max(1, r["h"])
        x2, y2 = min(W, x + w), min(H, y + h)

        # Filter out regions too small to be real text lines
        if w < min_line_width or h < min_line_height:
            log.info(f"Filtering region {idx}: {w}x{h}px (too small)")
            continue
        if x2 <= x or y2 <= y:
            continue

        crop = im.crop((x, y, x2, y2))
        np_crop = cv2.cvtColor(np.array(crop), cv2.COLOR_RGB2BGR)
        fpath = output_dir / f"manual_region_{idx}.png"
        cv2.imwrite(str(fpath), np_crop)
        paths.append(str(fpath))
    return paths

def _extract_pages_from_pdf(pdf_bytes, output_dir):
    """Extract PDF pages as JPEG images. Returns list of (page_index, path) tuples."""
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=200)
        img_path = output_dir / f"page_{i + 1}.jpg"
        pix.save(str(img_path))
        pages.append((i + 1, img_path))
    doc.close()
    return pages

def _find_latest_prepared_page():
    """Find the most recently modified manuscript_page.jpg in JOBS_DIR. Returns Path or None."""
    best, best_mtime = None, 0
    if not JOBS_DIR.exists():
        return None
    for d in JOBS_DIR.iterdir():
        if not d.is_dir():
            continue
        cand = d / "manuscript_page.jpg"
        if cand.exists():
            mt = cand.stat().st_mtime
            if mt > best_mtime:
                best, best_mtime = cand, mt
    return best

def _read_base64_image(data):
    """Decode a base64 or data-URL string to raw image bytes. Returns bytes or None."""
    import base64
    if not data:
        return None
    if "," in data:
        data = data.split(",", 1)[1]
    try:
        return base64.b64decode(data)
    except Exception:
        return None

def _split_double_page_if_needed(pil_image):
    """Return [PIL.Image] list: [full] or [left, right] if a central gutter is detected."""
    img = np.array(pil_image.convert("RGB"))[:, :, ::-1]
    bw = preprocess(img)
    ink = (bw == 0).astype(np.uint8)
    vproj = ink.sum(axis=0)
    W = vproj.shape[0]
    if W < 200:
        return [pil_image]
    c0, c1 = int(0.3 * W), int(0.7 * W)
    mid_slice = vproj[c0:c1]
    if mid_slice.size == 0:
        return [pil_image]
    gutter = c0 + int(np.argmin(mid_slice))
    left_ink = vproj[:gutter].mean()
    right_ink = vproj[gutter:].mean()
    gutter_ink = vproj[gutter:gutter + max(3, W // 200)].mean()
    if gutter_ink < 0.25 * max(left_ink, right_ink) and min(left_ink, right_ink) > 0.15 * max(vproj):
        pad = max(5, W // 200)
        L = pil_image.crop((0, 0, max(0, gutter - pad), pil_image.height))
        R = pil_image.crop((min(pil_image.width, gutter + pad), 0, pil_image.width, pil_image.height))
        return [L, R]
    return [pil_image]

def _downscale_image_if_needed(file_bytes, max_dim=MAX_IMAGE_DIM):
    """Downscale large images to avoid exhausting memory. Returns (new_bytes, orig_size, new_size)."""
    if not max_dim or max_dim <= 0:
        return file_bytes, None, None
    try:
        from PIL import Image as PILImage, ImageOps as PILImageOps
        with PILImage.open(io.BytesIO(file_bytes)) as img:
            img = PILImageOps.exif_transpose(img)
            orig_size = img.size
            if max(orig_size) <= max_dim:
                return file_bytes, orig_size, orig_size
            scale = max_dim / float(max(orig_size))
            new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
            resample = getattr(getattr(PILImage, "Resampling", PILImage), "LANCZOS", PILImage.BICUBIC)
            img = img.resize(new_size, resample).convert("RGB")
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=90, optimize=True)
            return out.getvalue(), orig_size, new_size
    except Exception as e:
        log.warning(f"Downscale failed: {e}")
    return file_bytes, None, None

# ------------------ Routes ------------------
@app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": "File too large (max 20 MB)."}), 413

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

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
        log.warning(f"Could not proxy export image {image_url}: {exc}")
        return jsonify({"error": "Could not fetch image for PDF export."}), 502

@app.route("/prepare", methods=["POST"])
def prepare():
    """Upload image(s) or PDF for later analysis. Returns job_id and page list."""
    from PIL import Image as PILImage, ImageOps as PILImageOps

    job_id = new_job_id()
    paths = job_paths(job_id)

    # Collect all uploaded files (supports multiple via getlist)
    files = request.files.getlist("image")
    files = [f for f in files if f and getattr(f, "filename", "")]

    # Fallback: raw body bytes (single image)
    raw_bytes = None
    if not files:
        raw_bytes = request.get_data() or None

    if not files and not raw_bytes:
        return jsonify({"error": "No image provided"}), 400

    page_entries = []  # list of {index, path, rel}

    def _save_image(img_bytes, index):
        """Save image bytes as page_{index}.jpg, returns path."""
        page_path = paths["root"] / f"page_{index}.jpg"
        try:
            img = PILImage.open(io.BytesIO(img_bytes))
            img = PILImageOps.exif_transpose(img).convert("RGB")
            img.save(str(page_path), "JPEG")
        except Exception:
            page_path.write_bytes(img_bytes)
        return page_path

    if files:
        page_idx = 1
        for f in files:
            fname = f.filename or ""
            ext = Path(fname).suffix.lower()
            f_bytes = f.read()

            if ext == ".pdf":
                # Extract pages from PDF
                try:
                    pdf_pages = _extract_pages_from_pdf(f_bytes, paths["root"])
                    for _, pdf_page_path in pdf_pages:
                        rel = str(pdf_page_path.relative_to(STATIC_DIR)).replace("\\", "/")
                        page_entries.append({"index": page_idx, "image": rel, "image_static": f"/static/{rel}"})
                        page_idx += 1
                except Exception as e:
                    log.error(f"PDF extraction failed: {e}")
                    return jsonify({"error": f"Failed to extract PDF pages: {str(e)}"}), 500
            else:
                # Regular image
                page_path = _save_image(f_bytes, page_idx)
                rel = str(page_path.relative_to(STATIC_DIR)).replace("\\", "/")
                page_entries.append({"index": page_idx, "image": rel, "image_static": f"/static/{rel}"})
                page_idx += 1
    else:
        # Raw bytes — single image
        page_path = _save_image(raw_bytes, 1)
        rel = str(page_path.relative_to(STATIC_DIR)).replace("\\", "/")
        page_entries.append({"index": 1, "image": rel, "image_static": f"/static/{rel}"})

    # Backward compatible: manuscript_page.jpg = copy of first page
    if page_entries:
        first_abs = STATIC_DIR / page_entries[0]["image"]
        compat_path = paths["root"] / "manuscript_page.jpg"
        if not compat_path.exists() or str(first_abs) != str(compat_path):
            shutil.copy(str(first_abs), str(compat_path))

    first_rel = page_entries[0]["image"] if page_entries else ""

    return jsonify({
        "ok": True,
        "job_id": job_id,
        "page_count": len(page_entries),
        "pages": page_entries,
        "page_image": first_rel,
        "page_image_static": f"/static/{first_rel}"
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    cleanup_old_jobs()

    # Resolve image source: direct upload or prepared job
    file_content = None
    original_filename = None

    # 1) Direct file upload
    if 'image' in request.files and getattr(request.files['image'], 'filename', ''):
        f = request.files['image']
        original_filename = f.filename
        if not allowed_file(original_filename):
            return jsonify({"error": "Unsupported file type"}), 400
        file_content = f.read()

    # 2) Prepared job reuse (supports page_index for multi-page jobs)
    if file_content is None:
        prepared_job = request.form.get('prepared_job') or request.args.get('prepared_job')
        if prepared_job:
            page_index = int(request.form.get('page_index', 0) or request.args.get('page_index', 0) or 0)
            job_dir = JOBS_DIR / prepared_job
            cand = None
            if page_index > 0:
                cand = job_dir / f"page_{page_index}.jpg"
            if cand is None or not cand.exists():
                cand = job_dir / "manuscript_page.jpg"
            if cand.exists():
                file_content = cand.read_bytes()
                original_filename = cand.name

    # 3) Base64 inline image
    if file_content is None:
        img_b64 = (request.form.get('image') or request.form.get('imageBase64') or
                   request.form.get('image_base64') or request.form.get('dataUrl') or
                   request.form.get('data_url'))
        raw = _read_base64_image(img_b64)
        if raw:
            file_content = raw
            original_filename = "inline-base64.png"

    # 4) Last-resort: latest prepared page on disk
    if file_content is None:
        latest = _find_latest_prepared_page()
        if latest:
            file_content = latest.read_bytes()
            original_filename = latest.name
            log.warning(f"No image provided; using latest prepared page: {latest}")

    if file_content is None:
        return jsonify({"error": "No image provided. Send 'image' file, 'prepared_job' ID, or base64 data."}), 400

    # Downscale if configured
    file_content, _, _ = _downscale_image_if_needed(file_content)

    job_id = new_job_id()
    paths = job_paths(job_id)

    # save upload (also copy to job root so front-end can display it)
    ext = Path(original_filename).suffix.lower() if original_filename else ".jpg"
    up_path = UPLOADS_DIR / f"{job_id}{ext}"
    up_path.write_bytes(file_content)
    page_copy = paths["root"] / f"page{ext}"
    shutil.copy(str(up_path), str(page_copy))
    page_rel = str(page_copy.relative_to(STATIC_DIR)).replace("\\", "/")
    page_url = f"/static/{page_rel}"

    # Parse mode and manual regions
    mode = request.form.get('mode', 'auto')
    manual_regions = []
    if mode in ('manual', 'json'):
        import json as _json
        regions_raw = request.form.get('regions', '[]')
        try:
            manual_regions = _json.loads(regions_raw) if regions_raw else []
        except Exception:
            manual_regions = []
        src_w = int(request.form.get('regions_src_w', 0) or 0)
        src_h = int(request.form.get('regions_src_h', 0) or 0)

    if mode in ('manual', 'json') and manual_regions:
        # Manual mode: crop user-drawn regions
        line_abs_paths = crop_manual_regions(up_path, manual_regions, paths["lines"], src_w, src_h)
        line_rel_paths = [str(Path(p).relative_to(STATIC_DIR)) for p in line_abs_paths]
        overlay_url = None
        lines = []
        polygons = []
    else:
        # Auto mode: run line segmentation + crop
        try:
            lines = segment_lines(up_path)
            line_rel_paths, polygons = crop_lines(up_path, lines, paths["lines"])

            # make overlay image
            overlay_path = paths["root"] / "overlay.jpg"
            draw_segmentation_overlay(up_path, lines, overlay_path)
            overlay_rel = str(overlay_path.relative_to(STATIC_DIR)).replace("\\", "/")
            overlay_url = f"/static/{overlay_rel}"
        except Exception as e:
            log.error(f"Segmentation failed: {e}")
            return jsonify({"error": f"Segmentation failed: {str(e)}"}), 500
        line_abs_paths = [str(STATIC_DIR / rp) for rp in line_rel_paths]

    # detect scribe changes + build reasons
    processor = ImageProcessor()
    advanced_detector = AdvancedScribeDetector()
    
    # Load line images for advanced analysis
    line_images = []
    line_features = []  # Store features for each line

    for line_path in line_abs_paths:
        try:
            img = cv2.imread(line_path)
            if img is not None:
                line_images.append(img)
                # Extract features for this line
                features = advanced_detector.extract_writing_features(img)
                line_features.append(features)
            else:
                log.warning(f"Could not load line image: {line_path}")
                line_images.append(np.ones((30, 100, 3), dtype=np.uint8) * 255)
                line_features.append(advanced_detector._default_features(is_fallback=True))
        except Exception as e:
            log.warning(f"Error loading line image {line_path}: {e}")
            line_images.append(np.ones((30, 100, 3), dtype=np.uint8) * 255)
            line_features.append(advanced_detector._default_features(is_fallback=True))
    
    # Use advanced scribe detection
    if len(line_images) >= 2:
        try:
            advanced_changes = advanced_detector.detect_scribe_changes_advanced(
                line_images, window_size=3, sensitivity=0.4 if mode == 'json' else 0.6
            )
            log.info(f"Advanced detector found {len(advanced_changes)} changes")
        except Exception as e:
            log.error(f"Advanced detection failed: {e}")
            advanced_changes = []
    else:
        advanced_changes = []
    
    # Fallback to original detection if advanced fails
    if not advanced_changes:
        result = processor.detect_with_reasons(line_abs_paths)
        scribe_changes = [
            {
                "line_number": ch["index"] + 2,  # boundary after line i → change at i+1
                "confidence": ch["confidence"],
                "explanation": ch["reason"],
                "distance": ch.get("distance", 0.0),
                "z_score": ch.get("z_score", 0.0)
            }
            for ch in result["changes"]
        ]
    else:
        scribe_changes = advanced_changes

    # Assign scribe names and aggregate features per scribe segment
    scribe_segments = []

    # Create segments based on scribe changes
    if scribe_changes:
        # Sort changes by line number
        sorted_changes = sorted(scribe_changes, key=lambda x: x.get('line_number', 0))

        # First scribe: from line 1 to first change
        first_change_line = sorted_changes[0].get('line_number', 1)
        scribe_segments.append({
            'scribe': assign_scribe_name(0),
            'start_line': 1,
            'end_line': first_change_line - 1,
            'is_initial': True
        })

        # Subsequent scribes
        for i, change in enumerate(sorted_changes):
            start = change.get('line_number', 1)
            end = sorted_changes[i + 1].get('line_number', len(line_features) + 1) - 1 if i + 1 < len(sorted_changes) else len(line_features)

            scribe_segments.append({
                'scribe': assign_scribe_name(i + 1),
                'start_line': start,
                'end_line': end,
                'confidence': change.get('confidence', 0),
                'explanation': change.get('explanation', ''),
                'distance': change.get('distance', 0),
                'z_score': change.get('z_score', 0),
                'methods_detected': change.get('methods_detected', []),
                'is_initial': False
            })
    else:
        # Single scribe - entire document
        scribe_segments.append({
            'scribe': assign_scribe_name(0),
            'start_line': 1,
            'end_line': len(line_features),
            'is_initial': True
        })

    # Aggregate features for each scribe segment
    for segment in scribe_segments:
        start_idx = max(0, segment['start_line'] - 1)
        end_idx = min(len(line_features), segment['end_line'])
        segment_features = line_features[start_idx:end_idx]

        if segment_features:
            # Filter out fallback features
            valid_features = [f for f in segment_features if not f.get('_is_fallback', False)]

            if valid_features:
                aggregated = {}
                for key in valid_features[0].keys():
                    if key.startswith('_'):
                        continue
                    values = [f.get(key, 0) for f in valid_features if key in f]
                    if values:
                        aggregated[key] = {
                            'mean': float(np.mean(values)),
                            'std': float(np.std(values)) if len(values) > 1 else 0.0,
                            'min': float(np.min(values)),
                            'max': float(np.max(values))
                        }
                segment['features'] = aggregated
            else:
                segment['features'] = None
        else:
            segment['features'] = None

    # Calculate overall statistics
    unique_scribes = set(seg['scribe'] for seg in scribe_segments)
    avg_confidence = np.mean([seg.get('confidence', 0) for seg in scribe_segments if seg.get('confidence')]) if any(seg.get('confidence') for seg in scribe_segments) else None

    # Replace scribe_changes with enriched segments
    scribe_changes = scribe_segments

    # Generate PDF report with new format
    try:
        pdf_url = generate_pdf_report_advanced(job_id, scribe_changes, page_rel, line_rel_paths)
    except Exception as e:
        log.error(f"PDF generation failed: {e}")
        pdf_url = None

    # Define feature names for frontend
    feature_names = [
        "avg_stroke_width", "stroke_width_variance", "curvature_avg",
        "angularity_score", "letter_spacing", "word_spacing",
        "slant_angle", "slant_consistency", "pressure_avg",
        "pressure_variance", "letter_height_avg", "letter_height_variance",
        "baseline_straightness"
    ]

    return jsonify(convert_numpy_types({
        "job_id": job_id,
        "page_image": page_url,
        "segmentation_overlay": overlay_url,
        "polygons": polygons,
        "scribe_changes": scribe_changes,
        "total_lines": len(line_rel_paths),
        "line_segments": [
            {
                "id": f"line_{i}",
                "bbox": lines[i]["bbox"] if i < len(lines) else [0, 0, 100, 20],
                "image": f"/static/{line_rel_paths[i]}" if i < len(line_rel_paths) else "",
                "features": line_features[i] if i < len(line_features) else None
            }
            for i in range(len(line_rel_paths))
        ],
        "feature_names": feature_names,
        "statistics": {
            "total_scribes": len(unique_scribes),
            "overall_confidence": round(avg_confidence * 100, 1) if avg_confidence is not None else None,
            "total_changes": len([s for s in scribe_segments if not s.get('is_initial', False)])
        },
        "pdf_report": pdf_url
    }))

@app.route("/download_pdf/<job_id>")
def download_pdf(job_id):
    paths = job_paths(job_id)
    pdf_path = paths["root"] / "scribe_analysis_report.pdf"
    
    if not pdf_path.exists():
        abort(404)
    
    return send_file(
        str(pdf_path),
        as_attachment=True,
        download_name=f"scribe_analysis_{job_id}.pdf",
        mimetype='application/pdf'
    )

@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files"""
    file_path = STATIC_DIR / filename
    if not file_path.exists():
        abort(404)
    return send_file(str(file_path))

@app.route("/prepare", methods=["OPTIONS"])
@app.route("/analyze", methods=["OPTIONS"])
def _preflight():
    return ("", 204)

if __name__ == "__main__":
    # Change default port if 5000 is busy
    port = int(os.getenv("PORT", "5001"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
