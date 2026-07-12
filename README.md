# PilkQuant News Intelligence

A focused news-event research workbench. Supply reporting, filings, transcripts, or notes; map the entities and narratives; simulate how market participants may react; and produce an evidence-linked structured report.

**Decision support only.** This project does not place orders, connect to brokers or exchanges, provide investment advice, or claim predictive profitability.

## Workflow

1. **Ingest news** — upload PDF, Markdown, or text sources and state a research question.
2. **Extract context** — identify entities, assets, narratives, catalysts, and source disagreement.
3. **Simulate reactions** — use the retained graph and multi-agent simulation machinery to explore participant responses.
4. **Produce research** — report direction, confidence, horizon, reversal risk, and evidence.

## Architecture

This fork deliberately keeps MiroFish's useful Flask/Vue, GraphRAG, participant-profile, simulation, and report machinery while narrowing the primary product to market-news intelligence. `backend/app/news_intelligence.py` adds a deterministic, network-free domain contract. `POST /api/news/analyze` validates a request and returns a stable research scaffold that downstream simulation/report stages can enrich. Its direction and scores come from a small lexical ruleset: they are a baseline for integration and UI development, **not real predictive analysis** and not a substitute for source verification or professional judgment.

## Structured output

```json
{
  "affected_assets": ["US10Y", "USD"],
  "direction": "negative",
  "confidence": 0.6,
  "horizon": "1-5d",
  "source_count": 2,
  "disagreement": 0.2,
  "reversal_risk": 0.35,
  "evidence": ["Central bank signals slower cuts", "Source: wire:policy"],
  "advisory_only": true,
  "safety_notice": "Research decision support only; not investment advice or an order instruction."
}
```

Accepted horizons are `intraday`, `1-5d`, `1-4w`, and `1-3m`. The deterministic endpoint makes no LLM or network calls. Required request fields are `headline`, `content`, `sources` (a non-empty string list), `assets` (a string list, which may be empty), and `horizon`.

## Setup

Prerequisites: Python 3.11–3.12, Node.js 20+, npm, and the external services required by the retained MiroFish graph/simulation pipeline.

```bash
cp .env.example .env
cd backend
pip install -r requirements.txt
python run.py
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Verification:

```bash
(cd backend && python -m pytest tests -q)
npm --prefix frontend run build
```

Environment variables for LLM/Zep-backed simulation remain documented in `.env.example`. Never commit credentials. The deterministic news contract and its tests require no live credentials.

## Scheduled RSS briefing automation

The stdlib-based collector reads an explicit RSS/Atom allowlist, includes only unseen stories, caps each run, and writes timestamped JSON and Markdown artifacts. Defaults cover Federal Reserve macro news, CoinDesk crypto news, and Dow Jones major-markets news; no API key is required. Each story is passed through the same deterministic `NewsAnalysisRequest` / `analyze_news` contract described above. Feed text is treated as untrusted data, not instructions. A failed or malformed feed is recorded in the artifact without preventing other feeds from being processed.

One-shot command from the repository root:

```bash
(cd backend && uv run python -m app.news_briefing --output-dir ../var/news-briefings --state-file ../var/news-seen.json --max-items 12)
```

Override the allowlist with repeatable `--feed NAME=URL` options or the comma-separated `PILKQUANT_NEWS_FEEDS` environment variable. `PILKQUANT_NEWS_OUTPUT_DIR`, `PILKQUANT_NEWS_STATE_FILE`, and `PILKQUANT_NEWS_MAX_ITEMS` provide the other configuration equivalents. For network-free fixture runs, pass `--fixtures mapping.json`, where the JSON object maps each configured feed URL to an RSS/Atom file. `--dry-run` still writes artifacts but does not update seen state.

Run this command every three hours using your operating system's scheduler and arrange for it to start at login/boot if desired. Scheduling and process supervision (for example, macOS `launchd`, cron, or systemd) are deliberately external; this repository neither installs nor starts those services. Briefings are advisory research scaffolds only, place no trades, emit no order instructions, and claim no predictive edge.

## License and attribution

Licensed under the [GNU Affero General Public License v3.0](LICENSE). This project is a focused fork of [MiroFish](https://github.com/666ghj/MiroFish) by the MiroFish contributors; their graph, simulation, and reporting foundations remain central to this codebase. Fork lineage: [wasipo09/MiroFish](https://github.com/wasipo09/MiroFish).
