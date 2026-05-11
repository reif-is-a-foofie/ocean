# Backend image
FROM python:3.11-slim
WORKDIR /app

# Install runtime deps
RUN python -m pip install --upgrade pip     && pip install fastapi[all] uvicorn

# Copy backend only
COPY backend ./backend

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
