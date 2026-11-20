from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Job:
    source: str                 # greenhouse, lever, ashby, arbeitnow, remotive
    source_id: str
    title: str
    company: str
    location: str
    remote: bool
    posted_at: datetime | None
    url: str
    description: str            # plain text
    skills: list[str] = field(default_factory=list)
    score: float = 0.0
    duplicate_of: str | None = None

    @property
    def job_id(self) -> str:
        return f"{self.source}:{self.source_id}"

    def to_row(self) -> dict:
        d = asdict(self)
        d["job_id"] = self.job_id
        d["skills"] = ", ".join(self.skills)
        return d
