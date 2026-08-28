from datetime import datetime

from pydantic import BaseModel, ConfigDict,HttpUrl

class CollectionRequest(BaseModel):
    url: str
class JobCreate(BaseModel):
    company_name: str
    company_domain: str | None = None
    external_id: str | None = None
    


    title: str
    location: str | None = None
    employment_type: str | None = None

    source: str
    source_url: str

    description: str | None = None
    salary: str | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int

    canonical_title: str
    canonical_location: str | None
    employment_type: str | None

    first_seen_at: datetime
    last_seen_at: datetime

    is_active: bool


class JobSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int

    source: str
    source_url: str

    title: str
    description: str | None
    location: str | None
    salary: str | None

    captured_at: datetime

class SourceObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    source: str
    observed_at: datetime
    is_present: bool
    source_url: str | None


class JobHistoryResponse(BaseModel):
    job: JobResponse
    snapshots: list[JobSnapshotResponse]
    observations: list[SourceObservationResponse]
