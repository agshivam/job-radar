import json
from datetime import datetime
from pathlib import Path

from jobradar import collectors, store
from jobradar.dedupe import dedupe
from jobradar.models import Job
from jobradar.pipeline import process
from jobradar.scoring import load_profile, score_job
from jobradar.skills import extract_skills

FX = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).parent.parent
PROFILE = load_profile(ROOT / "config" / "profile.yaml")
NOW = datetime(2026, 11, 20)


def fx(name):
    return json.load(open(FX / name))


def test_strip_html_decodes_and_removes_tags():
    assert collectors.strip_html("&lt;p&gt;Hello &amp; welcome&lt;/p&gt;") == "Hello & welcome"
    assert "Spark" in collectors.strip_html("<ul><li>Spark</li></ul>")


def test_parsers_produce_jobs():
    gh = collectors.parse_greenhouse(fx("greenhouse.json"), "Acme")
    assert len(gh) == 3 and gh[0].remote and gh[0].job_id == "greenhouse:101"
    lv = collectors.parse_lever(fx("lever.json"), "Beta")
    assert lv[0].source == "lever" and lv[0].remote
    an = collectors.parse_arbeitnow(fx("arbeitnow.json"))
    assert an[0].company == "Gamma GmbH" and "Kafka" in an[0].description


def test_skill_extraction_uses_word_boundaries():
    assert set(extract_skills("We use Snowflake, dbt and Python")) >= {"Snowflake", "dbt", "Python"}
    assert "SQL" not in extract_skills("NoSQLish stuff")        # not a standalone word
    assert "Spark" in extract_skills("PySpark jobs")


def test_dedupe_same_role_on_two_sources_keeps_earliest():
    a = Job("lever", "1", "Senior Data Engineer", "Beta", "Remote", True, datetime(2026, 11, 1), "u1", "")
    b = Job("greenhouse", "2", "Sr Data Engineer (Remote)", "Beta", "Remote", True, datetime(2026, 11, 5), "u2", "")
    c = Job("lever", "3", "Senior Data Engineer", "Other Co", "Remote", True, datetime(2026, 11, 5), "u3", "")
    d = Job("lever", "4", "Senior Data Engineer", "Beta", "Remote", True, datetime(2026, 11, 6), "u1", "")  # same URL
    kept = dedupe([b, a, c, d])
    ids = {j.job_id for j in kept}
    assert ids == {"lever:1", "lever:3"}      # b and d dropped, other company kept
    assert b.duplicate_of == "lever:1" and d.duplicate_of == "lever:1"


def test_dedupe_keeps_different_roles_at_same_company():
    a = Job("lever", "1", "Senior Data Engineer", "Beta", "", True, None, "u1", "")
    b = Job("lever", "2", "Data Analyst", "Beta", "", True, None, "u2", "")
    assert len(dedupe([a, b])) == 2


def test_scoring_orders_matches_sensibly():
    good = Job("x", "1", "Senior Data Engineer", "A", "Remote", True, datetime(2026, 11, 18), "u", "", ["Snowflake", "dbt", "Python"])
    weak = Job("x", "2", "Junior Data Engineer", "B", "Berlin", False, datetime(2026, 9, 1), "u2", "", ["Spark", "Kafka", "Azure"])
    assert score_job(good, PROFILE, NOW) > 90
    assert score_job(weak, PROFILE, NOW) < 25
    assert 0 <= score_job(weak, PROFILE, NOW) <= 100


def test_scoring_without_skills_does_not_crash():
    j = Job("x", "1", "Data Engineer", "A", "", False, None, "u", "")
    assert score_job(j, PROFILE, NOW) >= 0


def test_process_filters_non_data_roles_and_scores():
    raw = collectors.parse_greenhouse(fx("greenhouse.json"), "Acme")
    out = process(raw, PROFILE)
    titles = {j.title for j in out}
    assert "Marketing Manager" not in titles and "Senior Data Engineer" in titles
    top = max(out, key=lambda j: j.score)
    assert top.title == "Senior Data Engineer" and "Snowflake" in top.skills


def test_store_reports_new_jobs_only_once(tmp_path):
    con = store.connect(tmp_path / "j.duckdb")
    jobs = process(collectors.parse_lever(fx("lever.json"), "Beta"), PROFILE)
    assert len(store.upsert(con, jobs, NOW)) == len(jobs)
    assert store.upsert(con, jobs, NOW) == []          # second run: nothing new, so no repeat alerts
    assert store.export(con, tmp_path / "out.parquet") == len(jobs)
