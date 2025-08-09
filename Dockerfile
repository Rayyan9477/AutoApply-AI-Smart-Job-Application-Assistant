FROM python:3.12-slim

WORKDIR /app

# System deps for playwright and browsers; keep minimal for headless runs
RUN apt-get update && apt-get install -y \
    curl unzip wget gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /app

# Install Python deps
RUN pip install --no-cache-dir -r job_application_automation/requirements.txt \
    && pip install --no-cache-dir uv \
    && python -m pip install --no-cache-dir playwright \
    && python -m playwright install --with-deps chromium

# Create data dirs
RUN mkdir -p job_application_automation/data/logs job_application_automation/data/sessions job_application_automation/data/generated_cover_letters

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/app/job_application_automation/data

WORKDIR /app

# Default to API; UI available on 8501; override CMD to run CLI if desired
EXPOSE 8000 8501
ENV APP_MODE=api
CMD bash -lc 'if [ "$APP_MODE" = "ui" ]; then streamlit run job_application_automation/src/ui_app.py --server.address 0.0.0.0 --server.port 8501; else uvicorn job_application_automation.src.app:api_app --factory --host 0.0.0.0 --port 8000; fi'

