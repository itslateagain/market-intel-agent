"""Pure parsing functions: bytes in, validated RawItem records out. No network, no Spark.

Keeping these pure is what makes them unit-testable offline.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone

import feedparser
from pydantic import BaseModel

from ..ids import content_hash, normalize_url

MAX_BODY_CHARS = 5000


class RawItem(BaseModel):
    raw_id: str
    source_name: str
    company: str
    item_url: str
    title: str
    body: str
    published_at: datetime | None
    content_hash: str


class ParseResult(BaseModel):
    items: list[RawItem]
    rejected: int  # entries dropped for missing link/title


def _clean(text: str | None) -> str:
    """Strip tags/entities and collapse whitespace."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def make_raw_id(source_name: str, url: str, chash: str) -> str:
    """Same source + same URL + same content = same raw_id, so re-fetches are no-ops."""
    key = f"{source_name}|{normalize_url(url)}|{chash}"
    return "raw_" + hashlib.sha256(key.encode()).hexdigest()[:16]


def _item(source_name: str, company: str, url: str, title: str, body: str,
          published: datetime | None) -> RawItem:
    body = body[:MAX_BODY_CHARS]
    chash = content_hash(f"{title}\n{body}")
    return RawItem(raw_id=make_raw_id(source_name, url, chash), source_name=source_name,
                   company=company, item_url=url, title=title, body=body,
                   published_at=published, content_hash=chash)


def parse_rss(content: bytes, source_name: str, company: str, max_items: int) -> ParseResult:
    """Parse RSS or Atom. Entries without a link or title are counted as rejected."""
    feed = feedparser.parse(content)
    items: list[RawItem] = []
    rejected = 0
    for e in feed.entries[:max_items]:
        url, title = (e.get("link") or "").strip(), _clean(e.get("title"))
        if not url or not title:
            rejected += 1
            continue
        body = _clean(e.get("summary") or (e.get("content") or [{}])[0].get("value"))
        ts = e.get("published_parsed") or e.get("updated_parsed")
        published = datetime(*ts[:6], tzinfo=timezone.utc) if ts else None
        items.append(_item(source_name, company, url, title, body, published))
    return ParseResult(items=items, rejected=rejected)


_SEC_FORMS = {"8-K", "10-K", "10-Q", "6-K", "S-1"}


def parse_sec_submissions(content: bytes, source_name: str, company: str,
                          max_items: int) -> ParseResult:
    """Parse the SEC EDGAR submissions JSON into recent material filings."""
    data = json.loads(content)
    cik = str(int(data["cik"]))
    recent = data["filings"]["recent"]
    items: list[RawItem] = []
    rejected = 0
    for i, form in enumerate(recent["form"]):
        if form not in _SEC_FORMS:
            continue
        if len(items) >= max_items:
            break
        acc, doc = recent["accessionNumber"][i], recent["primaryDocument"][i]
        if not acc or not doc:
            rejected += 1
            continue
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{doc}"
        desc = _clean(recent.get("primaryDocDescription", [""] * (i + 1))[i]) or form
        filed = datetime.strptime(recent["filingDate"][i], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        title = f"{data.get('name', company)} files {form}: {desc}"
        items.append(_item(source_name, company, url, title, title, filed))
    return ParseResult(items=items, rejected=rejected)


PARSERS = {"rss": parse_rss, "sec_edgar": parse_sec_submissions}
