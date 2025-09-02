# Deployment (Stub)

This is a placeholder deployment guide. Replace placeholders with your chosen platform (Render, Railway, etc.).

- Build image: `docker build -t ocean:latest .`
- Run locally: `docker run -p 8000:8000 ocean:latest`
- Health check: `curl http://localhost:8000/healthz`
- Render: see `devops/render.yaml` and configure service.

Environment variables (examples):
- `PORT=8000`
- `ENV=production`

Use `ocean deploy --dry-run` to preview steps.

