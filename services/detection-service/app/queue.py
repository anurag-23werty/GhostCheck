import json
import os

import redis.asyncio as redis


# ============================================================
# Redis configuration
# ============================================================

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379",
)

DETECTION_QUEUE_NAME = "ghostcheck:detection"


# ============================================================
# Redis client
# ============================================================

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_timeout=None,
    socket_connect_timeout=5,
)


# ============================================================
# Enqueue detection job
# ============================================================

async def enqueue_detection(
    job_id: int,
    source: str = "linkedin",
    trigger: str = "job_collected",
) -> None:
    """
    Add a job to the detection queue.

    Message format:

    {
        "job_id": 123,
        "source": "linkedin",
        "trigger": "job_collected"
    }
    """

    message = {
        "job_id": job_id,
        "source": source,
        "trigger": trigger,
    }

    await redis_client.rpush(
        DETECTION_QUEUE_NAME,
        json.dumps(message),
    )


# ============================================================
# Dequeue detection job
# ============================================================

async def dequeue_detection() -> dict | None:
    """
    Block until a detection job becomes available.

    Returns:

    {
        "job_id": 123,
        "source": "linkedin",
        "trigger": "job_collected"
    }
    """

    result = await redis_client.blpop(
        DETECTION_QUEUE_NAME,
        timeout=0,
    )

    if result is None:
        return None

    _, payload = result

    return json.loads(payload)


# ============================================================
# Close Redis connection
# ============================================================

async def close_redis() -> None:
    """
    Close the Redis connection cleanly.
    """

    await redis_client.aclose()