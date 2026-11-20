"""The whole run: collect, filter to data roles, extract skills, dedupe, score, store, alert on new matches."""
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import collectors, notify, store
from .dedupe import dedupe
from .scoring import is_data_role, load_profile, score_job
from .skills import extract_skills

ROOT = Path(__file__).resolve().parent.parent.parent


def process(jobs, profile):
    jobs = [j for j in jobs if is_data_role(j)]
    for j in jobs:
        j.skills = extract_skills(f"{j.title}\n{j.description}")
    jobs = dedupe(jobs)
    for j in jobs:
        j.score = score_job(j, profile)
    return jobs


def run(config_path=ROOT / "config" / "companies.yaml", profile_path=ROOT / "config" / "profile.yaml",
        db_path=ROOT / "data" / "jobs.duckdb", export_path=ROOT / "app_data" / "jobs.parquet", raw_jobs=None, log=print):
    config = yaml.safe_load(open(config_path))
    profile = load_profile(profile_path)
    raw = raw_jobs if raw_jobs is not None else collectors.collect(config, log=log)
    jobs = process(raw, profile)
    con = store.connect(Path(db_path))
    new = store.upsert(con, jobs, datetime.now(timezone.utc).replace(tzinfo=None))
    total = store.export(con, Path(export_path))
    sent = notify.send(new, profile.get("alert_min_score", 60), log=log)
    summary = {"collected": len(raw), "kept_after_dedupe": len(jobs), "new": len(new), "alerts": sent, "stored_total": total}
    log(summary)
    con.close()
    return summary
