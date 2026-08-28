from datetime import datetime

from app.schemas import CollectedJob


def normalize_linkedin_job(data: dict) -> CollectedJob:
    return CollectedJob(
        external_id=data["job_posting_id"],

        company_name=data["company_name"],
        company_url=data.get("company_url"),

        title=data["job_title"],
        location=data.get("job_location"),
        employment_type=data.get("job_employment_type"),
        seniority_level=data.get("job_seniority_level"),

        source="linkedin",
        source_url=data["url"],

        description=data.get("job_summary"),
        salary=data.get("job_base_pay_range"),

        posted_at=(
            datetime.fromisoformat(
                data["job_posted_date"].replace("Z", "+00:00")
            )
            if data.get("job_posted_date")
            else None
        ),

        applicant_count=data.get("job_num_applicants"),

        application_url=data.get("apply_link"),
        application_available=data.get(
            "application_availability"
        ),
        easy_apply=data.get("is_easy_apply"),

        country_code=data.get("country_code"),
    )