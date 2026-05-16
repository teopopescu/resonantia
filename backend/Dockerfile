FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md alembic.ini ./

RUN uv sync --frozen --no-dev

COPY src/ ./src/
COPY alembic/ ./alembic/

RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "resonantia.main:app", "--host", "0.0.0.0", "--port", "8000"]
