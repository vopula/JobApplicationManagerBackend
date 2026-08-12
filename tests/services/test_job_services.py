from unittest.mock import MagicMock
from uuid import uuid4

from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate
from app.services.job_services import (
    createJob,
    deleteJob,
    get_job_by_url,
    readJobById,
    readJobs,
    updateJob,
)


def test_create_job_adds_commits_and_refreshes():
    db = MagicMock()

    job_data = JobCreate(
        job_url="https://example.com/job/123",
        job_title="Backend Engineer",
        company_name="Acme",
        location="Pune",
        work_mode="hybrid",
        job_description="Build backend systems.",
    )

    result = createJob(db, job_data)

    db.add.assert_called_once()
    added_job = db.add.call_args[0][0]
    assert isinstance(added_job, Job)
    assert added_job.job_url == "https://example.com/job/123"
    assert added_job.job_title == "Backend Engineer"
    assert added_job.company_name == "Acme"
    assert added_job.status == "saved"

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(added_job)
    assert result is added_job


def test_create_job_serializes_job_summary():
    db = MagicMock()

    job_data = JobCreate(
        job_url="https://example.com/job/456",
        job_summary={
            "required_experience": "3+ years",
            "key_skills": ["Python", "FastAPI"],
        },
    )

    createJob(db, job_data)

    added_job = db.add.call_args[0][0]
    assert added_job.job_summary == {
        "required_experience": "3+ years",
        "key_skills": ["Python", "FastAPI"],
    }


def test_read_jobs_returns_scalars():
    db = MagicMock()
    expected_jobs = [MagicMock(spec=Job), MagicMock(spec=Job)]
    db.execute.return_value.scalars.return_value.all.return_value = expected_jobs

    result = readJobs(db)

    db.execute.assert_called_once()
    assert result == expected_jobs


def test_read_job_by_id_returns_matching_job():
    db = MagicMock()
    expected_job = MagicMock(spec=Job)
    db.execute.return_value.scalar_one_or_none.return_value = expected_job

    result = readJobById(db, uuid4())

    assert result is expected_job


def test_read_job_by_id_returns_none_when_missing():
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    result = readJobById(db, uuid4())

    assert result is None


def test_update_job_applies_only_provided_fields():
    db = MagicMock()
    job = Job(job_url="https://example.com/job/123", job_title="Old Title", status="saved")

    updated_job = updateJob(db, job, JobUpdate(job_title="New Title"))

    assert updated_job.job_title == "New Title"
    assert updated_job.status == "saved"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(job)


def test_delete_job_calls_delete_and_commit():
    db = MagicMock()
    job = Job(job_url="https://example.com/job/123")

    deleteJob(db, job)

    db.delete.assert_called_once_with(job)
    db.commit.assert_called_once()


def test_get_job_by_url_returns_matching_job():
    db = MagicMock()
    expected_job = MagicMock(spec=Job)
    db.execute.return_value.scalar_one_or_none.return_value = expected_job

    result = get_job_by_url(db, "https://example.com/job/123")

    assert result is expected_job


def test_get_job_by_url_returns_none_when_missing():
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    result = get_job_by_url(db, "https://example.com/job/does-not-exist")

    assert result is None
