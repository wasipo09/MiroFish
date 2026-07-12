"""Low-noise RSS/Atom briefing CLI for PilkQuant News Intelligence.

Feed documents are untrusted data: their text is normalized and passed only to the
local deterministic analysis contract. This module never executes feed content.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.news_intelligence import NewsAnalysisRequest, analyze_news

NOTICE = "Research decision support only; not investment advice or an order instruction."
DEFAULT_FEEDS = (
    ("macro", "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("crypto", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("major-markets", "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
)
_TRACKING = {"fbclid", "gclid", "mc_cid", "mc_eid"}
_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class Feed:
    name: str
    url: str


@dataclass(frozen=True)
class NewsItem:
    headline: str
    link: str
    published: str | None
    source: str
    content: str
    feed_url: str


@dataclass(frozen=True)
class BriefingResult:
    json_path: Path
    markdown_path: Path


def _text(value: str | None) -> str:
    return _SPACE.sub(" ", html.unescape(_TAG.sub(" ", value or ""))).strip()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child(element: ET.Element, *names: str) -> ET.Element | None:
    wanted = set(names)
    return next((child for child in element if _local_name(child.tag) in wanted), None)


def _child_text(element: ET.Element, *names: str) -> str:
    child = _child(element, *names)
    return "" if child is None else "".join(child.itertext())


def canonicalize_link(link: str) -> str:
    parts = urlsplit(html.unescape(link.strip()))
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = f":{parts.port}" if parts.port and not ((scheme == "https" and parts.port == 443) or (scheme == "http" and parts.port == 80)) else ""
    query = sorted((key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
                   if not key.lower().startswith("utm_") and key.lower() not in _TRACKING)
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, host + port, path, urlencode(query), ""))


def _published(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_feed(payload: bytes, feed: Feed) -> list[NewsItem]:
    """Parse RSS or Atom bytes and remove duplicates within the document."""
    root = ET.fromstring(payload)
    channel = _child(root, "channel") if _local_name(root.tag) == "rss" else root
    if channel is None:
        channel = root
    feed_title = _text(_child_text(channel, "title")) or feed.name
    entries = [node for node in channel if _local_name(node.tag) in {"item", "entry"}]
    results: list[NewsItem] = []
    links: set[str] = set()
    titles: set[str] = set()
    for entry in entries:
        headline = _text(_child_text(entry, "title"))
        link_node = _child(entry, "link")
        raw_link = ""
        if link_node is not None:
            raw_link = link_node.attrib.get("href", "") or "".join(link_node.itertext())
        link = canonicalize_link(raw_link)
        title_key = headline.casefold()
        if not headline or not link or link in links or title_key in titles:
            continue
        links.add(link)
        titles.add(title_key)
        results.append(NewsItem(
            headline=headline,
            link=link,
            published=_published(_child_text(entry, "pubdate", "published", "updated", "date")),
            source=feed_title,
            content=_text(_child_text(entry, "description", "summary", "content")) or headline,
            feed_url=feed.url,
        ))
    return results


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "PilkQuant-News-Briefing/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read(5_000_001)[:5_000_000]


def _read_state(path: Path) -> set[str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return set(value.get("seen", [])) if isinstance(value, dict) else set()
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return set()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def _keys(item: NewsItem) -> set[str]:
    return {f"link:{item.link}", f"title:{item.headline.casefold()}"}


def _markdown(document: dict) -> str:
    lines = ["# Market News Briefing", "", f"Generated: {document['generated_at']}",
             f"Items: {document['item_count']}", "", f"> **Advisory only:** {document['notice']}", ""]
    if not document["items"]:
        lines.extend(["No unseen items were found.", ""])
    for item in document["items"]:
        analysis = item["analysis"]
        lines.extend([f"## [{item['headline']}]({item['link']})", "",
                      f"- Source: {item['source']} ({item['feed_url']})",
                      f"- Published: {item['published'] or 'unknown'}",
                      f"- Analysis: {analysis['direction']} (confidence {analysis['confidence']})",
                      f"- Horizon: {analysis['horizon']}", ""])
    if document["fetch_errors"]:
        lines.extend(["## Fetch errors", ""])
        lines.extend(f"- {error['feed']} ({error['url']}): {error['error']}" for error in document["fetch_errors"])
        lines.append("")
    return "\n".join(lines)


def run_briefing(feeds: Iterable[Feed], output_dir: Path, state_file: Path, *, max_items: int = 20,
                 fetcher: Callable[[str], bytes] = _fetch, generated_at: str | None = None,
                 persist_state: bool = True) -> BriefingResult:
    if max_items < 0:
        raise ValueError("max_items must be non-negative")
    generated_at = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    seen = _read_state(state_file)
    candidates: list[NewsItem] = []
    errors: list[dict[str, str]] = []
    run_keys: set[str] = set()
    for feed in feeds:
        try:
            parsed = parse_feed(fetcher(feed.url), feed)
        except Exception as exc:  # one unavailable or malformed feed must not abort the briefing
            errors.append({"feed": feed.name, "url": feed.url, "error": str(exc)})
            continue
        for item in parsed:
            keys = _keys(item)
            if keys & seen or keys & run_keys:
                continue
            run_keys.update(keys)
            candidates.append(item)
    candidates.sort(key=lambda item: (item.published or "", item.headline), reverse=True)
    selected = candidates[:max_items]
    items = []
    for item in selected:
        request = NewsAnalysisRequest.from_dict({"headline": item.headline, "content": item.content,
                                                 "sources": [item.link, item.feed_url], "assets": [], "horizon": "1-5d"})
        items.append({**asdict(item), "source_urls": [item.link, item.feed_url], "analysis": analyze_news(request)})
    document = {"generated_at": generated_at, "item_count": len(items), "advisory_only": True,
                "notice": NOTICE, "items": items, "fetch_errors": errors}
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = re.sub(r"[^0-9]", "", generated_at)[:14]
    json_path = output_dir / f"briefing-{stamp}.json"
    markdown_path = output_dir / f"briefing-{stamp}.md"
    _atomic_json(json_path, document)
    markdown_path.write_text(_markdown(document), encoding="utf-8")
    if persist_state:
        updated = seen.copy()
        for item in selected:
            updated.update(_keys(item))
        _atomic_json(state_file, {"seen": sorted(updated)})
    return BriefingResult(json_path, markdown_path)


def _feeds(values: list[str] | None) -> list[Feed]:
    raw = values or ([part for part in os.getenv("PILKQUANT_NEWS_FEEDS", "").split(",") if part] or
                     [f"{name}={url}" for name, url in DEFAULT_FEEDS])
    feeds = []
    for value in raw:
        name, separator, url = value.partition("=")
        if not separator or not name.strip() or not url.strip():
            raise ValueError(f"invalid feed {value!r}; expected NAME=URL")
        feeds.append(Feed(name.strip(), url.strip()))
    return feeds


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create an advisory-only low-noise RSS market briefing")
    parser.add_argument("--feed", action="append", help="allowlisted feed as NAME=URL (repeatable)")
    parser.add_argument("--output-dir", default=os.getenv("PILKQUANT_NEWS_OUTPUT_DIR", "var/news-briefings"))
    parser.add_argument("--state-file", default=os.getenv("PILKQUANT_NEWS_STATE_FILE", "var/news-seen.json"))
    parser.add_argument("--max-items", type=int, default=int(os.getenv("PILKQUANT_NEWS_MAX_ITEMS", "20")))
    parser.add_argument("--fixtures", type=Path, help="JSON object mapping feed URLs to local XML fixture paths")
    parser.add_argument("--dry-run", action="store_true", help="write artifacts but do not update seen state")
    args = parser.parse_args(argv)
    fetcher = _fetch
    if args.fixtures:
        mapping = json.loads(args.fixtures.read_text(encoding="utf-8"))
        fetcher = lambda url: Path(mapping[url]).read_bytes()
    result = run_briefing(_feeds(args.feed), Path(args.output_dir), Path(args.state_file), max_items=args.max_items,
                          fetcher=fetcher, persist_state=not args.dry_run)
    print(json.dumps({"json": str(result.json_path), "markdown": str(result.markdown_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
