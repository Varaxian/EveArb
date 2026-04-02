FROM python:3.12-slim

WORKDIR /app

COPY . /app

ENV PYTHONPATH=/app

RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir fastapi uvicorn sqlalchemy asyncpg psycopg2-binary pydantic requests python-dotenv

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
