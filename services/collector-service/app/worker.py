import asyncio

from app.queue import dequeue_collection


async def process_collection(job: dict):
    print("Processing collection:", job)

    # Real Bright Data collection will be added later.
    await asyncio.sleep(1)

    print("Collection completed:", job)


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