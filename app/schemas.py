from pydantic import BaseModel
from typing import Optional


class Job(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    posted_at: str
    apply_link: str
    seen_at: Optional[str] = None


class AgentStatus(BaseModel):
    state: str
    last_cycle: str
    new_this_session: int
    total_tracked: int
    poll_interval_minutes: int
    keywords: list[str]
    location: str


class SearchRequest(BaseModel):
    keyword: str


class SearchResponse(BaseModel):
    message: str
    keyword: str
