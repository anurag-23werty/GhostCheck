from pydantic import BaseModel


class CollectedJob(BaseModel):
    company_name: str
    company_domain: str | None = None

    title: str
    location: str | None = None
    employment_type: str | None = None

    source: str
    source_url: str

    description: str | None = None
    salary: str | None = None