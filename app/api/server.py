from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import jobs, agent

app = FastAPI(
    title="Jobs Agent API",
    description="AI-powered agentic job tracker for fresher and entry-level roles",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(agent.router, prefix="/agent", tags=["Agent"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "jobs-agent"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
