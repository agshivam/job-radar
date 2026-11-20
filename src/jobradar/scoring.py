"""Score a job from 0 to 100 against a resume profile.

score = 70 x skill coverage + 15 x seniority fit + 10 x location fit + 5 x freshness
  skill coverage  = weight of the job's skills that I have / weight of all the job's skills
  seniority fit   = 1 for senior, lead, principal or staff, 0.4 for a plain title, 0 for junior or intern
  (a junior or intern title also cuts the whole score to 40%)
  location fit    = 1 for remote or a preferred location, otherwise 0
  freshness       = 1 when posted in the last 7 days, falling to 0 at 30 days
"""
import re
from datetime import datetime, timezone

import yaml

from .models import Job
from .skills import WEIGHTS

SENIOR = re.compile(r"\b(senior|sr\.?|lead|principal|staff|architect)\b", re.I)
JUNIOR = re.compile(r"\b(junior|jr\.?|intern|internship|trainee|graduate|entry)\b", re.I)


def load_profile(path) -> dict:
    return yaml.safe_load(open(path))


def score_job(job: Job, profile: dict, now: datetime | None = None) -> float:
    mine = set(profile["skills"])
    total = sum(WEIGHTS[s] for s in job.skills)
    coverage = sum(WEIGHTS[s] for s in job.skills if s in mine) / total if total else 0.0
    if JUNIOR.search(job.title):
        seniority = 0.0
    elif SENIOR.search(job.title):
        seniority = 1.0
    else:
        seniority = 0.4
    places = [p.lower() for p in profile.get("locations", [])]
    location = 1.0 if job.remote or any(p in job.location.lower() for p in places) else 0.0
    fresh = 0.0
    if job.posted_at:
        age = ((now or datetime.now(timezone.utc).replace(tzinfo=None)) - job.posted_at).days
        fresh = 1.0 if age <= 7 else max(0.0, (30 - age) / 23)
    raw = 70 * coverage + 15 * seniority + 10 * location + 5 * fresh
    return round(raw * 0.4 if seniority == 0.0 else raw, 1)   # junior and intern roles are a poor fit: cut the score


def is_data_role(job: Job) -> bool:
    return bool(re.search(r"\b(data|analytics|etl|warehouse|dbt|snowflake|bi)\b", job.title, re.I))
