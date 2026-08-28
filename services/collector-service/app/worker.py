import asyncio

from app.client import submit_job
from app.normalization.jobs import normalize_linkedin_job
from app.queue import dequeue_collection
from app.sources.linkedin import collect_job_by_url


async def process_collection(job: dict):
    print("Processing collection:", job)

    url = job["url"]

    raw_job = await collect_job_by_url(url)

    normalized_job = normalize_linkedin_job(raw_job)

    result = await submit_job(normalized_job)

    print("Job submitted:", result)


async def worker():
    print("Collector worker started")

    while True:
        job = await dequeue_collection()

        if job is None:
            continue

        try:
            await process_collection(job)

        except Exception as exc:
            print("Collection failed:", exc)


if __name__ == "__main__":
    asyncio.run(worker())