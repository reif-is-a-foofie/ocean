# First Sprint - OCEAN Generated App

## Quick Start

### Backend
```bash
# Install dependencies
pip install -e .
pip install fastapi[all] uvicorn pytest httpx

# Run backend
uvicorn backend.app:app --reload
```

### Frontend
```bash
# Serve UI (from project root)
python -m http.server -d ui 5173
```

### Testing
```bash
# Run tests
pytest

# Run specific test
pytest backend/tests/test_healthz.py -v
```

## What's Generated

- **Backend**: FastAPI app with `/healthz` endpoint
- **Frontend**: Responsive HTML with health check
- **Tests**: pytest suite for backend endpoints
- **CI/CD**: GitHub Actions workflow
- **Docker**: Containerization ready
- **Deploy**: Render deployment config

## Next Steps

1. Customize `backend/app.py` with your business logic
2. Update `ui/index.html` with your design
3. Add more tests in `backend/tests/`
4. Deploy with `ocean deploy --dry-run` to see the plan
