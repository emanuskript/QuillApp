#!/usr/bin/env python3
# simple_backend.py - Simplified scribe detection backend for testing
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for Vue.js frontend

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        # Check if file is present
        if 'image' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({"error": "No file selected"}), 400
        
        # Generate consistent results based on file content
        import hashlib
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        
        # Create hash for consistent results
        file_hash = hashlib.md5(file_content).hexdigest()
        random.seed(file_hash)  # Seed random with file hash for consistency
        
        # Simulate processing time
        time.sleep(1)
        
        # Generate realistic-looking results based on image analysis
        # This simulates what real scribe detection would return
        num_changes = random.randint(1, 3)  # Always have some changes for testing
        scribe_changes = []
        
        scribe_names = ["Scribe A", "Scribe B", "Scribe C", "Different Hand"]
        
        for i in range(num_changes):
            confidence = random.uniform(0.7, 0.95)
            line_start = random.randint(5, 20) + (i * 6)
            line_end = line_start + random.randint(1, 3)
            
            scribe_changes.append({
                "line_number": line_start,
                "start_line": line_start,
                "end_line": line_end,
                "scribe": random.choice(scribe_names),
                "confidence": confidence,
                "explanation": f"Handwriting change detected at lines {line_start}-{line_end}. Analysis shows different ink flow and letter formation patterns.",
                "distance": random.uniform(0.3, 0.8),
                "z_score": random.uniform(1.5, 3.0)
            })
        
        total_lines = random.randint(25, 35)
        
        result = {
            "job_id": f"job_{int(time.time())}",
            "page_image": "manuscript_page.jpg", 
            "polygons": [],
            "scribe_changes": scribe_changes,
            "total_lines": total_lines,
            "line_segments": [
                {
                    "id": f"line_{i}",
                    "bbox": [0, i*20, 500, (i+1)*20],
                    "image": f"line_{i}.jpg"
                }
                for i in range(total_lines)
            ]
        }
        
        print(f"Analysis complete: {len(scribe_changes)} scribe changes detected in {total_lines} lines")
        return jsonify(result)
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

if __name__ == "__main__":
    print("Starting simplified scribe detection backend...")
    print("Backend will be available at: http://localhost:5001")
    print("Health check: http://localhost:5001/health")
    print("Analysis endpoint: http://localhost:5001/analyze")
    app.run(debug=True, port=5001, host='0.0.0.0')
