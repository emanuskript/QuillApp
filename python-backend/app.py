# app.py
from __future__ import annotations
import os, json, uuid, time, shutil, logging
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

import cv2
import numpy as np
from flask import Flask, request, render_template, jsonify, abort, send_file
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

# ------------------ Config ------------------
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"
JOBS_DIR = STATIC_DIR / "jobs"

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB

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
def segment_lines(img_path: Path) -> List[Dict]:
    """
    Segment lines using our custom line segmentation algorithm
    """
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError("Failed to read uploaded image")
    
    # Preprocess the image
    binary = preprocess(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Create line segmentor
    segmentor = LineSegmentor(gray, binary)
    
    # Get line boundaries
    lines = []
    H, W = img.shape[:2]
    
    # Check if any lines were detected
    print(f"LineSegmentor detected {len(segmentor.lines_boundaries) if segmentor.lines_boundaries else 0} line boundaries")
    if not segmentor.lines_boundaries:
        # If no lines detected, treat entire image as one line
        print(f"No line boundaries detected, using entire image as one line: {W}x{H}")
        lines.append({
            "id": "line_0",
            "boundary": [[0, 0], [W-1, 0], [W-1, H-1], [0, H-1]],
            "bbox": [0, 0, W-1, H-1]
        })
    else:
        print(f"Processing {len(segmentor.lines_boundaries)} detected line boundaries:")
        for i, boundary_tuple in enumerate(segmentor.lines_boundaries):
            print(f"  Line {i}: boundary_tuple = {boundary_tuple}")
            # Ensure we have exactly 4 values
            if len(boundary_tuple) != 4:
                continue
                
            l, u, r, d = boundary_tuple
            
            # Create boundary polygon (simple rectangle for now)
            boundary = [
                [l, u], [r, u], [r, d], [l, d]
            ]
            
            lines.append({
                "id": f"line_{i}",
                "boundary": boundary,
                "bbox": [l, u, r, d]
            })
    
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
    page_abs_path = str(STATIC_DIR / page_image)
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
            <b>Change #{i+1} - Line {change['line_number']}</b><br/>
            Confidence: {change['confidence']:.1%}<br/>
            Explanation: {change['explanation']}<br/>
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
    
    return str(pdf_path.relative_to(STATIC_DIR)).replace("", "/")

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
    page_img_path = STATIC_DIR / page_image
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
    
    return str(pdf_path.relative_to(STATIC_DIR))

# ------------------ Routes ------------------
@app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": "File too large (max 20 MB)."}), 413

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/analyze", methods=["POST"])
def analyze():
    cleanup_old_jobs()

    # Check if file is present
    if 'image' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['image']
    if not file or not file.filename:
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    job_id = new_job_id()
    paths = job_paths(job_id)

    # save upload (also copy to job root so front-end can display it)
    fname = secure_filename(file.filename)
    ext = Path(fname).suffix.lower()
    up_path = UPLOADS_DIR / f"{job_id}{ext}"
    file.save(str(up_path))
    page_copy = paths["root"] / f"page{ext}"
    shutil.copy(str(up_path), str(page_copy))
    page_rel = str(page_copy.relative_to(STATIC_DIR)).replace("\\", "/")

    # run line segmentation + crop
    try:
        lines = segment_lines(up_path)
        line_rel_paths, polygons = crop_lines(up_path, lines, paths["lines"])
    except Exception as e:
        log.error(f"Segmentation failed: {e}")
        return jsonify({"error": f"Segmentation failed: {str(e)}"}), 500

    # detect scribe changes + build reasons
    processor = ImageProcessor()
    advanced_detector = AdvancedScribeDetector()
    line_abs_paths = [str(STATIC_DIR / rp) for rp in line_rel_paths]
    
    # Load line images for advanced analysis
    line_images = []
    for line_path in line_abs_paths:
        try:
            img = cv2.imread(line_path)
            if img is not None:
                line_images.append(img)
            else:
                log.warning(f"Could not load line image: {line_path}")
                # Create a dummy image
                line_images.append(np.ones((30, 100, 3), dtype=np.uint8) * 255)
        except Exception as e:
            log.warning(f"Error loading line image {line_path}: {e}")
            line_images.append(np.ones((30, 100, 3), dtype=np.uint8) * 255)
    
    # Use advanced scribe detection
    if len(line_images) >= 2:
        try:
            advanced_changes = advanced_detector.detect_scribe_changes_advanced(
                line_images, window_size=3, sensitivity=0.6
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
                "line_number": ch["index"] + 2,  # 1-indexed + next line
                "confidence": ch["confidence"],
                "explanation": ch["reason"],
                "distance": ch.get("distance", 0.0),
                "z_score": ch.get("z_score", 0.0)
            }
            for ch in result["changes"]
        ]
    else:
        scribe_changes = advanced_changes

    # Generate PDF report with new format
    try:
        pdf_path = generate_pdf_report_advanced(job_id, scribe_changes, page_rel, line_rel_paths)
    except Exception as e:
        log.error(f"PDF generation failed: {e}")
        pdf_path = None

    return jsonify({
        "job_id": job_id,
        "page_image": page_rel,
        "polygons": polygons,
        "scribe_changes": scribe_changes,
        "total_lines": len(line_rel_paths),
        "line_segments": [
            {
                "id": f"line_{i}",
                "bbox": lines[i]["bbox"] if i < len(lines) else [0, 0, 100, 20],
                "image": f"/static/{line_rel_paths[i]}" if i < len(line_rel_paths) else ""
            }
            for i in range(len(line_rel_paths))
        ],
        "pdf_report": pdf_path
    })

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

if __name__ == "__main__":
    # Change default port if 5000 is busy
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)
