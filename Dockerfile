FROM python:3.12-slim

WORKDIR /app

# Copy dependency file
COPY pyproject.toml /app/

# Install dependencies (since we don't have a requirements.txt, we can use pip install .)
RUN pip install --no-cache-dir .

# Copy application code
COPY backend /app/backend

# Set python path
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
