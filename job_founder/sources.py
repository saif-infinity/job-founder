"""Connectors for public, official employer ATS job-board endpoints.

Only public Greenhouse and Lever board APIs are queried. No HTML scraping,
account access, application submission, or CAPTCHA handling is performed.
"""
from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser


_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        value = data.strip()
        if value:
            self.parts.append(value)


def _plain_text(value: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(value or "")
        return " ".join(parser.parts)
    except Exception:
        return html.unescape(re.sub(r"<[^>]*>", " ", value or "")).strip()


def _safe_json(url: str, timeout: int = 18):
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "JobFounder/0.1 (public job board API)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Réponse HTTP {response.status}")
        return json.loads(response.read(8_000_000).decode("utf-8"))


def parse_source_spec(line: str) -> tuple[str, str]:
    """Parse `greenhouse:board-token` or `lever:company-site` safely."""
    kind, separator, identifier = line.strip().partition(":")
    kind, identifier = kind.lower(), identifier.strip()
    if not separator or kind not in {"greenhouse", "lever"} or not _IDENTIFIER.fullmatch(identifier):
        raise ValueError("Format attendu : greenhouse:identifiant ou lever:identifiant")
    return kind, identifier


def _company_name(identifier: str) -> str:
    return re.sub(r"[-_]+", " ", identifier).strip().title()


def _iso_date(timestamp) -> str:
    try:
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp / (1000 if timestamp > 10_000_000_000 else 1), timezone.utc)
        else:
            dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        return dt.date().isoformat()
    except (ValueError, TypeError, OSError):
        return ""


def _score(job_text: str, profile: dict) -> tuple[int, list[str]]:
    skills = [part.strip() for part in re.split(r"[,;\n]", profile.get("skills", "")) if part.strip()]
    if not skills:
        return 50, []
    found = [skill for skill in skills if re.search(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", job_text, re.I)]
    score = min(95, 35 + round(60 * len(found) / len(skills)))
    return score, found


def _normalize(title: str, company: str, location: str, url: str, body: str, source: str, date_value="", contract="", remote="Sur site", salary="") -> dict:
    summary = _plain_text(body)[:1600]
    score, found = _score(f"{title} {summary}", {})
    return {
        "title": title.strip() or "Poste sans intitulé",
        "company": company,
        "city": location.strip() or "Lieu non précisé",
        "distance": "—",
        "contract": contract or "Non précisé",
        "salary": salary or "—",
        "source": source,
        "date": date_value or "Date inconnue",
        "score": score,
        "state": "À analyser",
        "remote": remote,
        "skills": found,
        "missing": [],
        "summary": summary or "Aucune description publiée.",
        "issues": [],
        "link": url,
        "is_demo": False,
    }


def fetch_source(line: str, profile: dict | None = None) -> list[dict]:
    kind, identifier = parse_source_spec(line)
    company = _company_name(identifier)
    jobs = []
    if kind == "greenhouse":
        quoted = urllib.parse.quote(identifier, safe="")
        payload = _safe_json(f"https://boards-api.greenhouse.io/v1/boards/{quoted}/jobs?content=true")
        raw_jobs = payload.get("jobs", [])
        for item in raw_jobs:
            location = (item.get("location") or {}).get("name", "")
            body = item.get("content", "")
            remote = "Télétravail" if re.search(r"\b(remote|anywhere|télétravail|telecommute)\b", location, re.I) else "Hybride" if re.search(r"\b(hybrid|hybride)\b", location, re.I) else "Sur site"
            job = _normalize(item.get("title", ""), company, location, item.get("absolute_url", ""), body, "Greenhouse", _iso_date(item.get("updated_at")), remote=remote)
            jobs.append(job)
    else:
        quoted = urllib.parse.quote(identifier, safe="")
        payload = _safe_json(f"https://api.lever.co/v0/postings/{quoted}?mode=json")
        if not isinstance(payload, list):
            raise RuntimeError("Réponse Lever inattendue")
        for item in payload:
            categories = item.get("categories") or {}
            location = categories.get("location", "")
            workplace = (item.get("workplaceType") or "").lower()
            remote = "Télétravail" if "remote" in workplace else "Hybride" if "hybrid" in workplace else "Sur site"
            salary_data = item.get("salaryRange") or {}
            salary = ""
            if salary_data:
                low, high = salary_data.get("min"), salary_data.get("max")
                currency = salary_data.get("currency", "")
                salary = f"{low or ''}–{high or ''} {currency}".strip(" –")
            job = _normalize(
                item.get("text", ""), company, location, item.get("hostedUrl", ""),
                item.get("descriptionPlain") or item.get("description", ""), "Lever",
                _iso_date(item.get("createdAt")), categories.get("commitment", ""), remote, salary,
            )
            jobs.append(job)
    profile = profile or {}
    for job in jobs:
        score, found = _score(f"{job['title']} {job['summary']}", profile)
        job["score"] = score
        job["skills"] = found
    return jobs


def search_configured_sources(source_lines: list[str], profile: dict) -> tuple[list[dict], list[str]]:
    """Fetch each configured employer board, deduplicating by canonical URL."""
    results, errors, seen = [], [], set()
    for line in source_lines:
        if not line.strip():
            continue
        try:
            kind, identifier = parse_source_spec(line)
            found_jobs = fetch_source(line, profile)
            for job in found_jobs:
                url = job["link"].rstrip("/").lower()
                if url and url not in seen:
                    job["source"] = f"{kind.title()} · {identifier}"
                    results.append(job)
                    seen.add(url)
        except Exception as exc:
            errors.append(f"{line.strip()} : {exc}")
    return results, errors
