FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml .
RUN uv lock && uv export --format requirements-txt --output-file requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

WORKDIR /app/omilab-application

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]