from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

KST = timezone(timedelta(hours=9))


@dataclass
class Item:
    keyword: str
    source: str
    title: str
    description: str
    link: str
    published_at: str | None


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def parse_naver_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y%m%d"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.astimezone(KST) if parsed.tzinfo else parsed.replace(tzinfo=KST)
        except ValueError:
            pass
    return None


def deduplicate(items: list[Item]) -> list[Item]:
    kept: list[Item] = []
    links: set[str] = set()
    for item in sorted(items, key=lambda x: x.published_at or "", reverse=True):
        normalized = re.sub(r"[^0-9a-z가-힣]", "", item.title.lower())
        if item.link in links:
            continue
        if any(SequenceMatcher(None, normalized, re.sub(r"[^0-9a-z가-힣]", "", x.title.lower())).ratio() >= 0.86 for x in kept):
            continue
        kept.append(item)
        links.add(item.link)
    return kept
