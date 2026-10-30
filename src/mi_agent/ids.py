"""Durable identifiers and content hashes.

Why: dedupe must be deterministic and survive re-ingestion. The same article fetched
twice (or via two feeds, or with different tracking params) must map to one event_id.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                    "gclid", "fbclid", "mc_cid", "mc_eid", "ref", "source"}


def normalize_url(url: str) -> str:
    """Lowercase host, drop fragment, tracking params and trailing slash; sort the query."""
    p = urlparse(url.strip())
    query = sorted((k, v) for k, v in parse_qsl(p.query) if k.lower() not in _TRACKING_PARAMS)
    path = p.path.rstrip("/") or "/"
    return urlunparse((p.scheme.lower() or "https", p.netloc.lower(), path, "", urlencode(query), ""))


def normalize_title(title: str) -> str:
    """Collapse whitespace and case so cosmetic edits do not create a new event."""
    return re.sub(r"\s+", " ", title).strip().lower()


def event_id(company: str, url: str, title: str) -> str:
    """Stable ID: hash of company + normalized URL + normalized title."""
    key = "|".join([company.strip().lower(), normalize_url(url), normalize_title(title)])
    return "evt_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def content_hash(text: str) -> str:
    """Hash of body text, used to detect silent edits to an already-seen item."""
    return hashlib.sha256(re.sub(r"\s+", " ", text).strip().encode("utf-8")).hexdigest()
