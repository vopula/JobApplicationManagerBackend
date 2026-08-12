FROM python:3.11-slim AS base

WORKDIR /code

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y pip setuptools wheel

# Copy source code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY main.py .

FROM base AS test
COPY tests ./tests

FROM base AS final
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]