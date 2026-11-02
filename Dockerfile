# syntax=docker/dockerfile:1

# 1) Compile Tailwind CSS from the templates.
FROM node:22-slim AS css
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY petconnect ./petconnect
RUN npm run css:build

# 2) Python runtime.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY petconnect ./petconnect
COPY --from=css /app/petconnect/static/css/app.css ./petconnect/static/css/app.css
COPY scripts/start.sh ./scripts/start.sh

WORKDIR /app/petconnect
RUN SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput \
    && useradd --create-home --uid 1000 app \
    && mkdir -p media \
    && chown -R app /app/petconnect/media
USER app

EXPOSE 8000
CMD ["/app/scripts/start.sh"]
