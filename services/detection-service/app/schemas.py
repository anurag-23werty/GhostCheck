from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DetectionFeatures(BaseModel):
    staleness_score: float
    repost_score: float
    cross_source_score: float
    description_duplication_score: float
    headcount_drift_score: float
    detail_omission_score: float


class DetectionRequest(BaseModel):
    job_id: int


class DetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: int
    score: float
    model_version: str
    explanation: str
    features: DetectionFeatures
    calculated_at: datetime