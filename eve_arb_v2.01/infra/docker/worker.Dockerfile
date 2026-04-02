FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e ./packages/utils -e ./packages/auth -e ./packages/esi -e ./packages/db -e ./packages/core -e ./apps/worker
CMD ["python", "apps/worker/worker.py", "--mode", "run_once"]
