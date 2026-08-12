from fastapi.testclient import TestClient
import pytest
import requests
from bs4 import BeautifulSoup

from app.services.ingestion_service import extract_job_data_from_url

from app.main import app

client = TestClient(app)


def test_preview_job_ingest_success(monkeypatch):
    def mock_preview_job_ingestion(job_url: str):
        return {
            "job_url": job_url,
            "job_title": "Backend Engineer",
            "company_name": "Acme",
            "location": "Pune",
            "work_mode": "hybrid",
            "job_description_preview": "Build backend systems using Python.",
            "job_summary": None
        }

    monkeypatch.setattr(
        "app.routes.jobs.preview_job_ingestion",
        mock_preview_job_ingestion,
    )

    response = client.post(
        "/jobs/ingest/preview",
        json={"job_url": "https://example.com/job/123"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["job_url"] == "https://example.com/job/123"
    assert data["job_title"] == "Backend Engineer"
    assert data["company_name"] == "Acme"
    assert data["location"] == "Pune"
    assert data["work_mode"] == "hybrid"
    assert data["job_description_preview"] == "Build backend systems using Python."
    assert data["job_summary"] is None


def test_preview_job_ingest_fetch_failure(monkeypatch):
    def mock_preview_job_ingestion(job_url: str):
        raise requests.exceptions.RequestException("Connection failed")

    monkeypatch.setattr(
        "app.routes.jobs.preview_job_ingestion",
        mock_preview_job_ingestion,
    )

    response = client.post(
        "/jobs/ingest/preview",
        json={"job_url": "https://example.com/job/123"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Failed to fetch job page: Connection failed"
    }


def test_preview_job_ingest_low_content(monkeypatch):
    def mock_preview_job_ingestion(job_url: str):
        raise ValueError("Could not extract meaningful job content from the page.")

    monkeypatch.setattr(
        "app.routes.jobs.preview_job_ingestion",
        mock_preview_job_ingestion,
    )

    response = client.post(
        "/jobs/ingest/preview",
        json={"job_url": "https://example.com/job/123"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Could not extract meaningful job content from the page."
    }


def test_ingest_job_success(monkeypatch):
    def mock_ingest_job_url(db, job_url: str):
        return {
            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "job_url": job_url,
            "job_title": "Backend Engineer",
            "company_name": "Acme",
            "location": "Pune",
            "work_mode": "hybrid",
            "job_description": "Build backend systems using Python.",
            "date_posted": None,
            "status": "saved",
            "created_at": "2026-05-06T10:00:00Z",
            "updated_at": "2026-05-06T10:00:00Z",
        }

    monkeypatch.setattr(
        "app.routes.jobs.ingest_job_url",
        mock_ingest_job_url,
    )

    response = client.post(
        "/jobs/ingest",
        json={"job_url": "https://example.com/job/456"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["job_url"] == "https://example.com/job/456"
    assert data["job_title"] == "Backend Engineer"
    assert data["company_name"] == "Acme"
    assert data["location"] == "Pune"
    assert data["work_mode"] == "hybrid"
    assert data["status"] == "saved"


def test_ingest_job_duplicate_url_returns_existing_job(monkeypatch):
    def mock_ingest_job_url(db, job_url: str):
        return {
            "id": "11111111-1111-1111-1111-111111111111",
            "job_url": job_url,
            "job_title": "Existing Backend Engineer",
            "company_name": "Existing Co",
            "location": "Bengaluru",
            "work_mode": "remote",
            "job_description": "Existing saved job description.",
            "date_posted": None,
            "status": "saved",
            "created_at": "2026-05-06T10:00:00Z",
            "updated_at": "2026-05-06T10:00:00Z",
        }

    monkeypatch.setattr(
        "app.routes.jobs.ingest_job_url",
        mock_ingest_job_url,
    )

    response = client.post(
        "/jobs/ingest",
        json={"job_url": "https://example.com/job/existing"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "11111111-1111-1111-1111-111111111111"
    assert data["job_url"] == "https://example.com/job/existing"
    assert data["job_title"] == "Existing Backend Engineer"
    assert data["company_name"] == "Existing Co"


def test_ingest_job_fetch_failure(monkeypatch):
    def mock_ingest_job_url(db, job_url: str):
        raise requests.exceptions.RequestException("Connection failed")

    monkeypatch.setattr(
        "app.routes.jobs.ingest_job_url",
        mock_ingest_job_url,
    )

    response = client.post(
        "/jobs/ingest",
        json={"job_url": "https://example.com/job/456"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Failed to fetch job page: Connection failed"
    }


def test_ingest_job_low_content(monkeypatch):
    def mock_ingest_job_url(db, job_url: str):
        raise ValueError("Could not extract meaningful job content from the page.")

    monkeypatch.setattr(
        "app.routes.jobs.ingest_job_url",
        mock_ingest_job_url,
    )

    response = client.post(
        "/jobs/ingest",
        json={"job_url": "https://example.com/job/456"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Could not extract meaningful job content from the page."
    }


def test_preview_job_ingest_debug_success(monkeypatch):
    def mock_preview_job_ingestion_debug(job_url: str):
        return {
            "rule_based_data": {
                "job_url": job_url,
                "job_title": "Backend Engineer",
                "company_name": None,
                "location": None,
                "work_mode": "hybrid",
                "date_posted": None,
                "job_description": "Rule-based extracted text",
            },
            "ai_extracted_data": {
                "company_name": "Acme",
                "job_title": "Backend Engineer",
                "location": "Pune",
                "date_posted": None,
                "job_summary": "Backend role focused on APIs and service development.",
            },
            "merged_data": {
                "job_url": job_url,
                "job_title": "Backend Engineer",
                "company_name": "Acme",
                "location": "Pune",
                "work_mode": "hybrid",
                "date_posted": None,
                "job_description": "Rule-based extracted text",
                "job_summary": "Backend role focused on APIs and service development.",
            },
        }

    monkeypatch.setattr(
        "app.routes.jobs.preview_job_ingestion_debug",
        mock_preview_job_ingestion_debug,
    )

    response = client.post(
        "/jobs/ingest/preview/debug",
        json={"job_url": "https://example.com/job/debug"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "rule_based_data" in data
    assert "ai_extracted_data" in data
    assert "merged_data" in data

    assert data["rule_based_data"]["job_title"] == "Backend Engineer"
    assert data["ai_extracted_data"]["company_name"] == "Acme"
    assert data["merged_data"]["company_name"] == "Acme"
    assert data["merged_data"]["location"] == "Pune"
    assert data["merged_data"]["job_summary"] == "Backend role focused on APIs and service development."

