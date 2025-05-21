# ── 1. builder ────────────────────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# requirements лежит в backend/requirements.txt
COPY backend/requirements.txt .  
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt

# ── 2. production ────────────────────────────────────────────────
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=foodgram.settings

WORKDIR /app

# подхватываем пакеты из builder
COPY --from=builder /install /usr/local

# копируем код проекта
# — сначала всё из backend/, чтобы внутри /app/ оказался manage.py, foodgram/, api/, recipes/, users/
COPY backend/ .  

# копируем папку data/ (ингредиенты)
COPY data/    ./data/

# копируем entrypoint (в infra/)
COPY backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
