"""Send new high-scoring jobs to Telegram. Does nothing when the bot settings are missing."""
import json
import os
import urllib.request

from .models import Job


def format_job(job: Job) -> str:
    where = "Remote" if job.remote else job.location
    return f"{job.score:.0f}  {job.title}\n{job.company}, {where}\n{', '.join(job.skills[:6])}\n{job.url}"


def send(jobs: list[Job], min_score: float, limit: int = 10, log=print) -> int:
    chosen = sorted([j for j in jobs if j.score >= min_score], key=lambda j: -j.score)[:limit]
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not chosen:
        return 0
    if not (token and chat):
        log("Telegram not configured; showing matches here instead:")
        for j in chosen:
            log(format_job(j) + "\n")
        return len(chosen)
    text = f"Job Radar: {len(chosen)} new match(es)\n\n" + "\n\n".join(format_job(j) for j in chosen)
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage",
                                 data=json.dumps({"chat_id": chat, "text": text[:4000], "disable_web_page_preview": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=15)
    return len(chosen)
