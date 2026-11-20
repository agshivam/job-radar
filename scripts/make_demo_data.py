"""Build app_data/jobs.parquet from the saved sample responses, so the report works without any network call.
Run: python scripts/make_demo_data.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from jobradar import collectors  # noqa: E402
from jobradar.pipeline import run  # noqa: E402

fx = ROOT / "tests" / "fixtures"
raw = (collectors.parse_greenhouse(json.load(open(fx / "greenhouse.json")), "Acme Health")
       + collectors.parse_lever(json.load(open(fx / "lever.json")), "Beta Data")
       + collectors.parse_arbeitnow(json.load(open(fx / "arbeitnow.json"))))
run(db_path=ROOT / "data" / "demo.duckdb", raw_jobs=raw)
