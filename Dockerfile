# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Системные зависимости (минимум). При необходимости можно добавить ca-certificates и tzdata
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Установка Python-зависимостей
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники
COPY . .

# Гарантируем наличие директории логов
RUN mkdir -p /app/logs

# Опционально: выставить таймзону через переменную окружения, например TZ
# ENV TZ=UTC

CMD ["python", "-u", "main.py"]


