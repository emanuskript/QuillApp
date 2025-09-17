# QuillApp - Manuscript Analysis Tool

A Vue.js application for manuscript analysis with advanced scribe detection capabilities.

## Project setup
```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Lints and fixes files
```
npm run lint
```

## Scribe Detection Backend

### Setup
1. Navigate to the backend directory:
```bash
cd python-backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the backend server:
```bash
python3 simple_backend.py
```

The backend will be available at: http://localhost:5001

### Optional tuning
The popup sends optional fields to `/analyze`:
- `z_thresh` (float, e.g. 2.0), `min_gap` (int), `min_run` (int),
- `illum_frac` (float, default 0.035), `sauvola_window` (int, default 31),
- `algo` = `auto` | `peaks` | `ruptures`, plus optional `ruptures_pen` (float).

Install extras:
```bash
pip install -r python-backend/requirements.txt
```

### Frontend Configuration
Set the backend URL in your environment:
```bash
echo VUE_APP_BACKEND_URL=http://localhost:5001 > .env.local
```

## Features

### Scribe Detection
- **Robust Analysis**: Uses adaptive peak detection with ruptures fallback for complex manuscripts
- **Explainable Results**: Hover over confidence percentages to see detailed explanations
- **Parameter Controls**: Adjust sensitivity, gaps, preprocessing settings via UI
- **Deterministic Sampling**: Always shows exactly 2 representative samples per scribe
- **PDF Export**: Export analysis results as PDF reports

### Technical Details
- **OCR Integration**: Uses pytesseract for precise line detection
- **Change Point Detection**: Implements ruptures library for principled scribe boundary detection
- **Feature Extraction**: Combines LBP textures, HOG descriptors, and color statistics
- **Preprocessing**: Configurable illumination correction, binarization, and deskewing

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).
