from app.client import submit_job
from app.normalization.jobs import (
    normalize_linkedin_job,
    normalize_indeed_job,
    normalize_glassdoor_job,
)
from app.queue import dequeue_collection
from app.sources.linkedin import collect_job_by_url as collect_linkedin
from app.sources.indeed import collect_job_by_url as collect_indeed
from app.sources.glassdoor import collect_job_by_url as collect_glassdoor
from app.sources.router import detect_source


async def process_collection(job: dict):

    print("Processing collection:", job)

    url = job["url"]

    source = detect_source(url)

    print("Detected source:", source)

    if source == "linkedin":

        raw_job = await collect_linkedin(url)

        normalized_job = normalize_linkedin_job(raw_job)

    elif source == "indeed":

        raw_job = await collect_indeed(url)

        normalized_job = normalize_indeed_job(raw_job)

    elif source == "glassdoor":

        raw_job = await collect_glassdoor(url)

        normalized_job = normalize_glassdoor_job(raw_job)

    else:

        raise ValueError(
            f"Collector for source '{source}' "
            "is not implemented yet"
        )

    result = await submit_job(normalized_job)

    print("Job submitted:", result)