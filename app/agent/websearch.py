import hashlib
from datetime import datetime

from ddgs import DDGS

_JOB_BOARDS = [
    "site:linkedin.com/jobs",
    "site:internshala.com",
    "site:naukri.com",
    "site:instahyre.com",
]


def _make_id(url: str) -> str:
    return "web_" + hashlib.md5(url.encode()).hexdigest()[:12]


def _parse_title_company(title: str) -> tuple[str, str]:
    for sep in (" at ", " - ", " | "):
        if sep in title:
            parts = title.split(sep, 1)
            return parts[0].strip(), parts[1].split("|")[0].strip()
    return title.strip(), "Unknown"


def search_jobs(keyword: str, location: str, max_results: int = 10) -> list[dict]:
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    def _fetch(query: str, limit: int):
        try:
            results = list(DDGS().text(query, max_results=limit))
        except Exception:
            results = []
        for r in results:
            url = r.get("href", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            title_raw = r.get("title", "")
            title, company = _parse_title_company(title_raw)
            jobs.append({
                "job_id": _make_id(url),
                "title": title,
                "company": company,
                "location": location,
                "posted_at": datetime.utcnow().strftime("%Y-%m-%d"),
                "apply_link": url,
                "source": "web",
            })

    _fetch(f"site:linkedin.com/jobs {keyword} {location}", max_results)

    if len(jobs) < 3:
        for board in _JOB_BOARDS[1:]:
            if len(jobs) >= max_results:
                break
            _fetch(f"{board} {keyword} {location} fresher", max_results - len(jobs))

    return jobs[:max_results]
