from fastapi import FastAPI

from app.queue import enqueue_collection


app = FastAPI(
    title="GhostCheck Collector",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "collector-service",
    }


@app.post("/collect")
async def collect(payload: dict):
    await enqueue_collection(payload)

    return {
        "status": "queued",
        "message": "Collection job added to queue",
    }