"""Remove duplicate postings: the same job on two sources, or the same role posted for several locations."""
import re

from rapidfuzz import fuzz

from .models import Job

THRESHOLD = 92


def _norm(text: str) -> str:
    text = re.sub(r"\(.*?\)|\[.*?\]", " ", text.lower())          # drop things like "(Remote)"
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\b(sr|snr)\b", "senior", text)
    text = re.sub(r"\b(jr|jnr)\b", "junior", text)
    return re.sub(r"\s+", " ", text).strip()


def dedupe(jobs: list[Job]) -> list[Job]:
    """Keep the earliest posting of each job. Duplicates get duplicate_of set and are dropped from the result.
    Two jobs are the same when the URL matches, or the company matches and the titles are nearly identical."""
    ordered = sorted(jobs, key=lambda j: (j.posted_at is None, j.posted_at or 0))
    kept: list[Job] = []
    by_url: dict[str, Job] = {}
    by_company: dict[str, list[Job]] = {}
    for job in ordered:
        if job.url in by_url:
            job.duplicate_of = by_url[job.url].job_id
            continue
        company = _norm(job.company)
        title = _norm(job.title)
        match = next((k for k in by_company.get(company, []) if fuzz.token_set_ratio(title, _norm(k.title)) >= THRESHOLD), None)
        if match:
            job.duplicate_of = match.job_id
            continue
        kept.append(job)
        by_url[job.url] = job
        by_company.setdefault(company, []).append(job)
    return kept
