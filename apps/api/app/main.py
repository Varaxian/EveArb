from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.database import ensure_runtime_schema

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_runtime_schema()
    except Exception as e:
        print(f"[WARN] schema patch failed: {e}")
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok"}
