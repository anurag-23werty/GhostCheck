from fastapi import FastAPI

from app.routers.jobs import router as jobs_router


app = FastAPI(
    title="GhostCheck API",
    description="API Gateway for the GhostCheck platform",
    version="0.1.0",
)


app.include_router(jobs_router)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "api-gateway",
    }


@app.get("/")
def root():
    return {
        "message": "GhostCheck API",
        "version": "0.1.0",
    }