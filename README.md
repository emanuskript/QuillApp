# quill_1.0

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

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).

## Scribe detection backend

The Scribe Detection popup calls a Python backend at `VUE_APP_BACKEND_URL` (default `http://localhost:5001`).

1) Start the backend (from `python-backend/`):
	- Create/activate a venv and install deps (Flask, flask-cors, opencv-python, numpy, pillow, scikit-image, scipy, requests)
	- Run `python3 simple_backend.py` (serves on port 5001)

2) Configure the frontend to reach the backend:
	- Create `.env.local` with:
	  - `VUE_APP_BACKEND_URL=http://localhost:5001`

3) Run the app:
```
npm run serve
```

The popup will now display neat, backend-segmented line crops and scribe sample images.
