import asyncio
import json

from app.sources.linkedin import collect_job_by_url

from app.normalization.jobs import normalize_linkedin_job
async def main():
    url = "https://www.linkedin.com/jobs/view/4399880402/"

    result = await collect_job_by_url(url)
    job = normalize_linkedin_job(result)

    print(
        job.model_dump_json(
        indent=2
        )
    )


if __name__ == "__main__":
    asyncio.run(main())