# 1. Базовый образ
FROM python:3.12-slim-bookworm

# 2. Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 3. Рабочая папка для сборки
WORKDIR /app

# 4. Установка зависимостей
COPY pyproject.toml .
# Создаем lock-файл и ставим библиотеки глобально
RUN uv lock && uv export --format requirements-txt --output-file requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

# 5. Копируем ВЕСЬ проект (как есть, с папкой omilab-application)
COPY . .

# 6. ВАЖНЫЙ ХОД:
# Меняем рабочую директорию прямо внутрь папки с кодом
WORKDIR /app/omilab-application

# 7. Открываем порт
EXPOSE 8000

# 8. Запускаем
# Теперь мы уже внутри папки, поэтому просто запускаем main:app
# Python найдет файл main.py прямо рядом с собой
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]