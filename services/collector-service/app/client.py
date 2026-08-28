import os

import httpx

from app.schemas import CollectedJob


API_GATEWAY_URL = os.getenv(
    "API_GATEWAY_URL",
    "http://localhost:8000",
)


async def submit_job(job: CollectedJob):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_GATEWAY_URL}/api/v1/jobs",
            json=job.model_dump(),
        )

        response.raise_for_status()

        return response.json()