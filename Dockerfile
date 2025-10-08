# =============================================================================
# ARGs (tweak as needed)
# =============================================================================
ARG PYTHON_VERSION=3.13

# =============================================================================
# Stage 0: Base runtime (no build toolchain)
# - small, contains only what's needed at runtime
# =============================================================================
FROM python:${PYTHON_VERSION}-slim AS base-runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_CACHE_DIR=/opt/uv-cache \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# runtime-only utilities (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
    && rm -rf /var/lib/apt/lists/*

# install uv (package manager)
RUN pip install --no-cache-dir uv && \
    mkdir -p /opt/uv-cache && chmod 777 /opt/uv-cache

# non-root user
RUN groupadd --gid 1000 appuser && \
    useradd  --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# =============================================================================
# Stage 1: Base build (adds toolchain for native deps)
# - we keep compilers only here, not in the final image
# =============================================================================
FROM base-runtime AS base-build

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Stage 2: Resolve & install PROD dependencies
# - resolve lock INSIDE Docker to match linux/amd64|arm64
# - no dev deps
# =============================================================================
FROM base-build AS deps

# Copy only dep files first for better caching
COPY pyproject.toml uv.lock README.md ./

# 1) Re-lock for Linux image (ensures correct wheels/versions)
# 2) Install prod deps into .venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv lock --upgrade && \
    uv sync --frozen --no-dev --no-install-project && \
    rm -rf /opt/uv-cache/*

# =============================================================================
# Stage 3: Resolve & install DEV dependencies
# =============================================================================
FROM deps AS deps-dev
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen && \
    rm -rf /opt/uv-cache/*

# =============================================================================
# Stage 4: Production image (tiny, no compilers)
# =============================================================================
FROM base-runtime AS production

# bring in the ready .venv (deps) from deps stage
COPY --from=deps /app/.venv /app/.venv
COPY --from=deps /app/pyproject.toml /app/uv.lock /app/

# app sources
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser README.md ./
COPY --chown=appuser:appuser secrets/ ./secrets/

# install the project into the existing .venv now that sources are present
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

# dirs
RUN mkdir -p /app/logs /app/htmlcov && chown -R appuser:appuser /app
USER appuser

# runtime cache dir (writable)
ENV UV_CACHE_DIR=/tmp/uv-cache

EXPOSE 8000

# Health check (adjust path if your docs route differs)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/api/docs || exit 1

# Start with Granian (make sure it's in your deps)
CMD ["uv","run","granian","src.main:app","--host","0.0.0.0","--port","8000","--workers","4"]

# =============================================================================
# Stage 5: Development image (hot reload, dev deps)
# =============================================================================
FROM base-runtime AS development

# bring in dev .venv
COPY --from=deps-dev /app/.venv /app/.venv
COPY --from=deps-dev /app/pyproject.toml /app/uv.lock /app/

# sources & extras
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser tests/ ./tests/
COPY --chown=appuser:appuser docs/ ./docs/
COPY --chown=appuser:appuser Makefile ./
COPY --chown=appuser:appuser README.md ./
COPY --chown=appuser:appuser secrets/ ./secrets/

# install project with dev deps for hot reload/dev tools
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen

RUN mkdir -p /app/logs /app/htmlcov && chown -R appuser:appuser /app
USER appuser
ENV UV_CACHE_DIR=/tmp/uv-cache

EXPOSE 8000
# no healthcheck in dev
HEALTHCHECK NONE
CMD ["uv","run","uvicorn","src.main:app","--host","0.0.0.0","--port","8000","--reload"]

# =============================================================================
# Stage 6: Testing image (pytest, coverage)
# =============================================================================
FROM base-runtime AS testing

# bring in dev .venv (has test deps)
COPY --from=deps-dev /app/.venv /app/.venv
COPY --from=deps-dev /app/pyproject.toml /app/uv.lock /app/

# sources & tests
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser tests/ ./tests/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser Makefile ./
COPY --chown=appuser:appuser README.md ./
COPY --chown=appuser:appuser secrets/ ./secrets/

# install project with dev/test deps
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen

RUN mkdir -p /app/logs /app/htmlcov && chown -R appuser:appuser /app
USER appuser
ENV UV_CACHE_DIR=/tmp/uv-cache \
    SETUPTOOLS_USE_DISTUTILS=stdlib

# if some tools are missing in your dev group, you can keep these;
# ideally ensure they’re in [dependency-groups.dev] in pyproject
# RUN uv pip install pytest-cov pytest-asyncio aiosqlite

# no healthcheck in test images
HEALTHCHECK NONE
CMD ["uv","run","pytest","tests/","-v","--cov=src","--cov-report=html","--cov-report=term"]
