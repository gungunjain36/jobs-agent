from fastapi import APIRouter

from app.core import config as cfg
from app.core import tracker
from app.schemas import AgentStatus, SearchRequest, SearchResponse
from app import state

router = APIRouter()


@router.get("/status", response_model=AgentStatus)
def get_status():
    with state.status_lock:
        return AgentStatus(
            state="paused" if state.paused.is_set() else "running",
            last_cycle=state.last_cycle_time,
            new_this_session=state.total_new_this_session,
            total_tracked=tracker.get_seen_count(),
            poll_interval_minutes=cfg.POLL_INTERVAL_MINUTES,
            keywords=cfg.SEARCH_KEYWORDS,
            location=cfg.LOCATION_FILTER,
        )


@router.post("/pause")
def pause_agent():
    state.paused.set()
    return {"message": "Agent paused successfully"}


@router.post("/resume")
def resume_agent():
    state.paused.clear()
    return {"message": "Agent resumed successfully"}


@router.post("/search", response_model=SearchResponse)
def trigger_search(req: SearchRequest):
    state.search_queue.put(req.keyword)
    return SearchResponse(message="Search queued successfully", keyword=req.keyword)
