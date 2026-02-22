FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala uv
RUN pip install uv

# Dependências primeiro (cache)
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev

# Código
COPY . .

# Diretório do banco SQLite
RUN mkdir -p /data

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]