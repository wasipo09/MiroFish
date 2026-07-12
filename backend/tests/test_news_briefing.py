import json
from pathlib import Path

from app.news_briefing import Feed, canonicalize_link, parse_feed, run_briefing


RSS = b"""<?xml version='1.0'?><rss version='2.0'><channel><title>Macro Wire</title>
<item><title> Fed  raises   outlook </title><link>https://example.com/story?utm_source=rss&amp;b=2&amp;a=1</link><pubDate>Tue, 07 Jul 2026 10:00:00 GMT</pubDate><description>Growth is stronger.</description></item>
<item><title>Fed raises outlook</title><link>https://example.com/duplicate</link><description>Duplicate title.</description></item>
</channel></rss>"""
ATOM = b"""<?xml version='1.0'?><feed xmlns='http://www.w3.org/2005/Atom'><title>Crypto Desk</title>
<entry><title>Bitcoin upgrade ships</title><link rel='alternate' href='https://crypto.example/btc#comments'/><updated>2026-07-07T11:00:00Z</updated><summary>Network upgrade completed.</summary></entry>
</feed>"""


def test_parse_rss_and_atom_normalizes_fields_and_deduplicates_titles():
    rss = parse_feed(RSS, Feed("macro", "https://feeds.example/macro"))
    atom = parse_feed(ATOM, Feed("crypto", "https://feeds.example/crypto"))

    assert len(rss) == 1
    assert rss[0].headline == "Fed raises outlook"
    assert rss[0].link == "https://example.com/story?a=1&b=2"
    assert rss[0].published == "2026-07-07T10:00:00Z"
    assert rss[0].source == "Macro Wire"
    assert atom[0].headline == "Bitcoin upgrade ships"
    assert atom[0].link == "https://crypto.example/btc"
    assert atom[0].published == "2026-07-07T11:00:00Z"


def test_canonicalize_link_removes_tracking_fragment_and_sorts_query():
    assert canonicalize_link("HTTPS://Example.COM/x/?z=2&utm_campaign=n&a=1#top") == "https://example.com/x?a=1&z=2"


def test_run_writes_json_markdown_uses_analysis_contract_and_seen_state(tmp_path):
    output = tmp_path / "briefings"
    state = tmp_path / "seen.json"
    feeds = [Feed("macro", "fixture:macro"), Feed("crypto", "fixture:crypto")]
    payloads = {"fixture:macro": RSS, "fixture:crypto": ATOM}

    first = run_briefing(feeds, output, state, max_items=1, fetcher=payloads.__getitem__, generated_at="2026-07-07T12:00:00Z")
    document = json.loads(first.json_path.read_text())

    assert document["generated_at"] == "2026-07-07T12:00:00Z"
    assert document["item_count"] == 1
    assert document["advisory_only"] is True
    assert "not investment advice" in document["notice"].lower()
    assert document["items"][0]["analysis"]["advisory_only"] is True
    assert document["items"][0]["source_urls"]
    assert first.markdown_path.exists()
    assert "# Market News Briefing" in first.markdown_path.read_text()
    assert json.loads(state.read_text())["seen"]

    second = run_briefing(feeds, output, state, max_items=10, fetcher=payloads.__getitem__, generated_at="2026-07-07T15:00:00Z")
    assert json.loads(second.json_path.read_text())["item_count"] == 1  # capped item was not marked seen
    third = run_briefing(feeds, output, state, max_items=10, fetcher=payloads.__getitem__, generated_at="2026-07-07T18:00:00Z")
    assert json.loads(third.json_path.read_text())["item_count"] == 0


def test_fetch_error_is_recorded_without_failing_other_feeds(tmp_path):
    def fetch(url):
        if url == "broken":
            raise OSError("offline")
        return ATOM

    result = run_briefing(
        [Feed("bad", "broken"), Feed("markets", "working")], tmp_path / "out", tmp_path / "state.json",
        max_items=5, fetcher=fetch, generated_at="2026-07-07T12:00:00Z",
    )
    document = json.loads(result.json_path.read_text())
    assert document["item_count"] == 1
    assert document["fetch_errors"] == [{"feed": "bad", "url": "broken", "error": "offline"}]
