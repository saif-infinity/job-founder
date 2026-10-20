"""Safe job-page inspection primitives and optional Playwright adapter.

This module only inspects pages. It never logs in, solves CAPTCHAs, submits forms,
or attempts to evade access controls.
"""
from __future__ import annotations

import ipaddress
import re
from dataclasses import asdict, dataclass
from urllib.parse import urljoin, urlparse


@dataclass
class PageReport:
    url: str
    page_title: str = ""
    platform: str = "site_entreprise"
    application_url: str = ""
    required_fields: list[str] | None = None
    blockers: list[str] | None = None
    expired: bool = False
    multi_step: bool = False
    form_found: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _is_public_http_url(url: str) -> bool:
    """Reject non-web URLs and localhost/private literal IPs before navigation."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        host = parsed.hostname.lower().rstrip(".")
        if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
            return False
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return True
        return address.is_global
    except (ValueError, TypeError):
        return False


def diagnose_page(
    url: str,
    page_title: str,
    text: str,
    anchors: list[dict[str, str]],
    fields: list[dict[str, str | bool]],
    *,
    form_found: bool = False,
    multi_step: bool = False,
) -> PageReport:
    """Classify a rendered page from observable text, links, and form metadata."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    title = page_title or ""
    content = f"{title}\n{text}".lower()
    platform = "site_entreprise"
    if any(token in host for token in ("linkedin.", "welcometothejungle.", "indeed.", "glassdoor.")):
        platform = "reseau_ou_agregateur"
    elif any(token in host for token in ("workday.", "greenhouse.", "lever.", "smartrecruiters.", "ashbyhq.")):
        platform = "ats"
    elif host.endswith(".gouv.fr") or host.endswith(".gov") or host.endswith(".gov.uk"):
        platform = "institutionnel"
    elif any(token in host for token in ("job", "career", "emploi")):
        platform = "site_carriere"

    apply_terms = re.compile(r"(postuler|candidater|apply now|apply for|submit application|déposer ma candidature)", re.I)
    application_url = ""
    for anchor in anchors:
        name = anchor.get("text", "")
        href = anchor.get("href", "")
        if href and apply_terms.search(name):
            target = urljoin(url, href)
            if _is_public_http_url(target):
                application_url = target
                break

    blockers: list[str] = []
    captcha_terms = ("captcha", "recaptcha", "hcaptcha", "verify you are human", "vérifiez que vous êtes humain", "robot or human")
    login_terms = ("sign in to apply", "log in to apply", "connectez-vous pour postuler", "connexion requise", "create an account to apply")
    expired_terms = ("job is no longer available", "position has been filled", "this job has expired", "offre expirée", "offre n'est plus disponible", "recrutement clôturé", "poste déjà pourvu")
    if any(token in content for token in captcha_terms):
        blockers.append("captcha_detecte")
    if any(token in content for token in login_terms) or any(str(field.get("type", "")).lower() == "password" for field in fields):
        blockers.append("login_requis")
    expired = any(token in content for token in expired_terms)
    if expired:
        blockers.append("offre_expiree")
    if multi_step:
        blockers.append("formulaire_multietapes")
    if not application_url and not form_found and not expired:
        blockers.append("lien_candidature_introuvable")

    required_fields = []
    for field in fields:
        if field.get("required"):
            name = str(field.get("label") or field.get("name") or field.get("type") or "champ requis").strip()
            if name and name not in required_fields:
                required_fields.append(name)
    return PageReport(
        url=url,
        page_title=title,
        platform=platform,
        application_url=application_url,
        required_fields=required_fields,
        blockers=blockers,
        expired=expired,
        multi_step=multi_step,
        form_found=form_found,
    )


def analyze_with_playwright(url: str, timeout_ms: int = 20000) -> PageReport:
    """Load and inspect one public web page using an installed Playwright browser."""
    if not _is_public_http_url(url):
        raise ValueError("Seules les URL HTTP/HTTPS publiques sont acceptées.")
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright n’est pas installé. Ajoutez-le à l’installation de l’application.") from exc

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception as exc:
            raise RuntimeError("Chromium Playwright est introuvable. Le navigateur doit être inclus dans l’installation.") from exc
        try:
            page = browser.new_page()
            page.set_default_timeout(timeout_ms)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            except PlaywrightTimeoutError:
                # Some job boards keep long-running requests alive; inspect the DOM already loaded.
                pass
            page.wait_for_timeout(500)
            title = page.title()
            text = page.locator("body").inner_text(timeout=3000)[:120000]
            anchors = page.locator("a").evaluate_all("els => els.map(a => ({text: (a.innerText || a.getAttribute('aria-label') || '').trim(), href: a.href || ''}))")
            fields = page.locator("input, select, textarea").evaluate_all("els => els.map(e => { const id=e.id; const label=id ? document.querySelector('label[for=\"'+CSS.escape(id)+'\"]') : null; return {name:e.name || '', label:(label?.innerText || e.getAttribute('aria-label') || e.placeholder || '').trim(), type:e.type || e.tagName.toLowerCase(), required:!!(e.required || e.getAttribute('aria-required')==='true')}; })")
            form_found = page.locator("form").count() > 0
            multi_step = bool(page.get_by_text(re.compile(r"step\s*\d+\s*(of|sur)\s*\d+|étape\s*\d+", re.I)).count())
            return diagnose_page(url, title, text, anchors, fields, form_found=form_found, multi_step=multi_step)
        finally:
            browser.close()
