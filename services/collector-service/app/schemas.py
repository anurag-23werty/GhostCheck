from datetime import datetime

from pydantic import BaseModel


class CollectedJob(BaseModel):
    external_id: str

    company_name: str
    company_domain: str | None = None
    company_url: str | None = None

    title: str
    location: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None

    source: str
    source_url: str

    description: str | None = None
    salary: str | None = None

    posted_at: datetime | None = None
    applicant_count: int | None = None

    application_url: str | None = None
    application_available: bool | None = None
    easy_apply: bool | None = None

    country_code: str | None = None