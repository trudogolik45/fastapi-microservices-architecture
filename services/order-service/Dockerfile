# Stage 1: The Builder
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_HTTP_TIMEOUT=120
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY services/order-service/pyproject.toml services/order-service/
RUN uv sync --package order-service --frozen --no-dev
COPY . .

# Stage 2: The Final Image
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
CMD ["fastapi", "run", "services/order-service/main.py", "--port", "8000", "--host", "0.0.0.0"]
