from fastapi import FastAPI

from app.database import engine
from app.models import Base
app = FastAPI(
    title="GhostCheck API",
    description="API Gateway for the GhostCheck platform",
    version="0.1.0",
)
Base.metadata.create_all(bind=engine)

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