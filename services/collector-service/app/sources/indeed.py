import os
import httpx


BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
BRIGHT_DATA_URL = os.getenv("BRIGHT_DATA_URL")
INDEED_JOBS_DATASET_ID = os.getenv("INDEED_JOBS_DATASET_ID")


async def collect_job_by_url(url: str) -> dict:

    if not BRIGHT_DATA_API_KEY:
        raise RuntimeError(
            "BRIGHT_DATA_API_KEY is not configured"
        )

    if not INDEED_JOBS_DATASET_ID:
        raise RuntimeError(
            "INDEED_JOBS_DATASET_ID is not configured"
        )

    params = {
        "dataset_id": INDEED_JOBS_DATASET_ID,
        "format": "json",
        "include_errors": "true",
    }

    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = [
        {
            "url": url,
        }
    ]

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            BRIGHT_DATA_URL,
            params=params,
            headers=headers,
            json=payload,
        )

        print("Bright Data Indeed status:", response.status_code)

        if response.status_code >= 400:
            print("Bright Data response:", response.text)

        response.raise_for_status()

        data = response.json()

    if not data:
        raise RuntimeError(
            f"Bright Data returned no data for {url}"
        )
    if data[0].get("error"):
        error_code = data[0].get("error_code", "unknown")
        error_message = data[0].get("error", "Unknown Bright Data error")

        raise RuntimeError(
            f"Indeed scraping failed [{error_code}]: {error_message}"
        )

    return data[0]