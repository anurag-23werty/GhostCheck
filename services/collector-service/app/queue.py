import json
import os

import redis.asyncio as redis


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379",
)

QUEUE_NAME = "ghostcheck:collection"


redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_timeout = None,
    socket_connect_timeout = 5,
)


async def enqueue_collection(payload: dict):
    await redis_client.rpush(
        QUEUE_NAME,
        json.dumps(payload),
    )


async def dequeue_collection():
    result = await redis_client.blpop(
        QUEUE_NAME,
        timeout=0,
    )

    if result is None:
        return None

    _, payload = result

    return json.loads(payload)