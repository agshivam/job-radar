"""Collectors for public job APIs. Each parser is a pure function from the API's JSON to Job objects, so it can be tested
with a saved response. The fetch functions only add the network call. All sources are public endpoints meant for reuse.
Be polite: one request per company, a short pause between calls, and a clear User-Agent."""
import html
import json
import re
import time
import urllib.request
from datetime import datetime, timezone

from .models import Job

UA = "job-radar/1.0 (personal portfolio project; https://github.com/agshivam/job-radar)"


def strip_html(raw: str | None) -> str:
    text = html.unescape(raw or "")
    text = re.sub(r"<(br|/p|/li|/h\d)\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", text)).strip()


def _ts(value) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(tzinfo=None)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)


def _remote(*texts) -> bool:
    return any("remote" in (t or "").lower() for t in texts)


def parse_greenhouse(data: dict, company: str) -> list[Job]:
    return [Job("greenhouse", str(j["id"]), j["title"], company, (j.get("location") or {}).get("name", ""),
                _remote((j.get("location") or {}).get("name"), j["title"]), _ts(j.get("updated_at")),
                j["absolute_url"], strip_html(j.get("content"))) for j in data.get("jobs", [])]


def parse_lever(data: list, company: str) -> list[Job]:
    out = []
    for j in data:
        cat = j.get("categories") or {}
        out.append(Job("lever", j["id"], j["text"], company, cat.get("location", ""),
                       _remote(cat.get("location"), j.get("workplaceType")), _ts(j.get("createdAt")),
                       j["hostedUrl"], j.get("descriptionPlain") or strip_html(j.get("description"))))
    return out


def parse_ashby(data: dict, company: str) -> list[Job]:
    return [Job("ashby", j["id"], j["title"], company, j.get("location", ""), bool(j.get("isRemote")),
                _ts(j.get("publishedAt")), j["jobUrl"], j.get("descriptionPlain") or strip_html(j.get("descriptionHtml")))
            for j in data.get("jobs", [])]


def parse_arbeitnow(data: dict, company: str = "") -> list[Job]:
    return [Job("arbeitnow", j["slug"], j["title"], j["company_name"], j.get("location", ""), bool(j.get("remote")),
                _ts(j.get("created_at")), j["url"], strip_html(j.get("description"))) for j in data.get("data", [])]


def parse_remotive(data: dict, company: str = "") -> list[Job]:
    return [Job("remotive", str(j["id"]), j["title"], j["company_name"], j.get("candidate_required_location", "Remote"),
                True, _ts(j.get("publication_date")), j["url"], strip_html(j.get("description"))) for j in data.get("jobs", [])]


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


ENDPOINTS = {
    "greenhouse": ("https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true", parse_greenhouse),
    "lever": ("https://api.lever.co/v0/postings/{token}?mode=json", parse_lever),
    "ashby": ("https://api.ashbyhq.com/posting-api/job-board/{token}", parse_ashby),
}
OPEN_FEEDS = {
    "arbeitnow": ("https://www.arbeitnow.com/api/job-board-api", parse_arbeitnow),
    # Remotive asks API users to call it at most a few times a day and to link back to the job URL.
    "remotive": ("https://remotive.com/api/remote-jobs?category=data&limit=100", parse_remotive),
}


def collect(config: dict, pause: float = 1.0, log=print) -> list[Job]:
    """Fetch every configured source. A failing source is logged and skipped, never fatal."""
    jobs: list[Job] = []
    for kind, companies in (config.get("boards") or {}).items():
        url_t, parser = ENDPOINTS[kind]
        for c in companies or []:
            try:
                jobs += parser(_get(url_t.format(token=c["token"])), c["name"])
            except Exception as exc:
                log(f"skip {kind}/{c['token']}: {exc}")
            time.sleep(pause)
    for name in config.get("feeds") or []:
        url, parser = OPEN_FEEDS[name]
        try:
            jobs += parser(_get(url))
        except Exception as exc:
            log(f"skip feed {name}: {exc}")
        time.sleep(pause)
    return jobs
