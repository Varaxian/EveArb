FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e ./packages/utils -e ./packages/auth -e ./packages/esi -e ./packages/db -e ./packages/core -e ./apps/api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "apps/api"]
