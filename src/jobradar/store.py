"""Keep jobs in DuckDB. A job is 'new' the first time its job_id is seen, so alerts are sent once."""
from pathlib import Path

import duckdb
import pandas as pd

from .models import Job

COLUMNS = ["job_id", "source", "title", "company", "location", "remote", "posted_at", "url", "skills", "score", "first_seen", "last_seen"]


def connect(path: Path) -> duckdb.DuckDBPyConnection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    con.execute("""CREATE TABLE IF NOT EXISTS jobs (job_id VARCHAR PRIMARY KEY, source VARCHAR, title VARCHAR, company VARCHAR,
        location VARCHAR, remote BOOLEAN, posted_at TIMESTAMP, url VARCHAR, skills VARCHAR, score DOUBLE,
        first_seen TIMESTAMP, last_seen TIMESTAMP)""")
    return con


def upsert(con, jobs: list[Job], now) -> list[Job]:
    """Insert new jobs and refresh known ones. Returns only the jobs seen for the first time."""
    known = {r[0] for r in con.execute("SELECT job_id FROM jobs").fetchall()}
    new = [j for j in jobs if j.job_id not in known]
    for j in jobs:
        r = j.to_row()
        if j.job_id in known:
            con.execute("UPDATE jobs SET last_seen = ?, score = ?, skills = ? WHERE job_id = ?", [now, r["score"], r["skills"], r["job_id"]])
        else:
            con.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        [r["job_id"], r["source"], r["title"], r["company"], r["location"], r["remote"], r["posted_at"],
                         r["url"], r["skills"], r["score"], now, now])
    return new


def export(con, path: Path) -> int:
    df: pd.DataFrame = con.execute("SELECT * FROM jobs ORDER BY score DESC, posted_at DESC").df()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return len(df)
