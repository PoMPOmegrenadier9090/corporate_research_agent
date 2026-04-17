FROM python:3.14-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

# Install dependencies first with lockfile + cache to speed up rebuilds.
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --frozen --no-install-project

COPY . .

# Install the local project after sources are copied.
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --frozen

CMD ["uv", "run", "-m", "mcp_server.main"]
