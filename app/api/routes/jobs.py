from fastapi import APIRouter, Query

from app.core import tracker

router = APIRouter()


@router.get("/")
def list_jobs(limit: int = Query(default=20, le=100)):
    return tracker.get_recent_jobs(limit)


@router.get("/recent")
def recent_jobs():
    return tracker.get_recent_jobs(5)


@router.get("/count")
def job_count():
    return {"total": tracker.get_seen_count()}


@router.get("/search")
def search_tracked_jobs(q: str, limit: int = Query(default=20, le=100)):
    return tracker.search_jobs_by_keyword(q, limit)
