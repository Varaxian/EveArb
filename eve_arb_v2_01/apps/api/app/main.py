
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "service": "eve-arb-v2.01"}

@app.get("/health")
def health():
    return {"health": "green"}
