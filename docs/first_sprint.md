# First Sprint

- Run backend: `uvicorn backend.app:app --reload`
- Health check: `curl http://127.0.0.1:8000/healthz`
- Open UI: open `ui/index.html` in a browser or serve via:
  - `python -m http.server -d ui 5173` then go to http://127.0.0.1:5173

