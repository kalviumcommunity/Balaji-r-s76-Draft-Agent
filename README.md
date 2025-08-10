# LinkedIn Agent — Planner, Drafter, Scheduler, and Analyst

A practical, CLI-first LinkedIn agent that uses prompting, RAG, structured output, and function calling to plan weekly content, draft posts grounded in past performance, schedule into evidence-based engagement windows, and learn from analytics while respecting LinkedIn API policies and rate limits.[1][2][3]

## Why this exists
- Streamlines ideation-to-publish with reproducible workflows and machine-readable outputs.[3][1]
- Grounds drafts in prior top-performing content via retrieval to avoid repetition and improve relevance.
- Uses structured JSON artifacts to integrate with dashboards and automations.
- Encodes safe scheduling and rate-limit-aware operations for compliant usage with LinkedIn’s ecosystem.[2][1]

## Key concepts encoded
- Prompting: role/tone-specific templates for hooks, value, and CTAs.
- RAG: local retrieval over exports of past posts, comments, and notes to generate grounded drafts.
- Structured output: JSON schemas for posts, schedules, and metrics for predictable pipelines.[4][1]
- Function calling: modular actions (fetch, draft, schedule, metrics) wired to either approved APIs or manual import/export flows with throttling and backoff guidance.[1][2]

## Features
- Content planner: propose a 7‑day plan with Now–Next–Later framing and timing experiments that converge to audience-specific windows.[5][6][7]
- Drafting assistant: generate grounded posts with hooks, tags, CTA, and source snippets from prior wins.
- Scheduler: queue drafts into mid‑morning weekday windows as a starting heuristic, then adapt via weekly experiments.[6][7][5]
- Analytics tracker: import or fetch metrics; update recommendations and reorder plan based on outcomes.
- Compliance-first mode: operate via approved endpoints or manual flows; avoid scraping and prohibited automation; respect rate limits and resets.[2][1]

## Getting started

### Prerequisites
- Python 3.9+.
- Optional: CSV exports of past post performance for local RAG and analytics.

### Installation
- Clone the repo, then:
- pip install -r requirements.txt

### Quick start
1) Initialize workspace
- li init

2) Plan next week with recommended windows
- li plan --accept

3) Draft a grounded post
- li draft "3 lessons from building our MVP" --format story > draft.json

4) Queue the draft
- li queue draft.json

5) Metrics ingestion (manual import or API when approved)
- li metrics --since 7d --import metrics.csv

6) Update plan based on last week’s performance
- li plan --suggest --accept

## CLI commands

- li init — set up workspace, config, and folders.
- li plan [--accept|--suggest] — propose Now–Next–Later weekly plan and recommended time slots based on best-practice windows, then adapt from metrics[5][6][7].
- li draft "topic" --format short|story|carousel — generate a post grounded in past posts via local retrieval.
- li queue  — schedule into the next available slot; outputs a schedule JSON.
- li post --now  — immediate publish (only if compliant with approved APIs); otherwise outputs ready-to-paste content.
- li metrics --since 7d [--import metrics.csv] — ingest metrics and update the learning store.
- li replies  — suggest thoughtful, value-adding comment replies to top responses.

All commands emit JSON artifacts for portability and automation.[4][1]

## JSON schemas

- Post
{
  "id": "P1",
  "title": "Hooked story: MVP lessons",
  "body": "...",
  "tags": ["product", "startups"],
  "assets": [],
  "cta": "What would you try next?",
  "target_window": {"day": "Tue", "hour": 10},
  "source_snippets": [{"post_id": "old123", "reason": "similar topic"}]
}

- Schedule
{
  "week_of": "2025-08-11",
  "slots": [{"post_id": "P1", "day": "Tue", "hour": 10}, {"post_id": "P2", "day": "Thu", "hour": 11}]
}

- Metrics
{
  "post_id": "P1",
  "impressions": 1234,
  "reactions": 87,
  "comments": 23,
  "shares": 5,
  "clicks": 41,
  "published_at": "2025-08-12T10:05:00Z"
}

Schemas keep outputs predictable and easy to validate or visualize.[1][4]

## Planning and posting windows

- Start with weekday work hours, especially mid‑morning and lunch, with a slight bias to Tuesday and Thursday; then personalize via experiments because audiences differ.[7][5][6]
- Maintain a rolling timing experiment: vary posting hour by ±1–2h for 2 weeks; select winners and prune underperformers.[5][6][7]

## Rate limits, compliance, and safe operation

- Respect LinkedIn’s Terms and program-specific API rules; use only permitted scopes, store only allowed data, and avoid prohibited automation.[2][1]
- Expect dual app/member rate limits, 429 responses on exceedance, and midnight UTC resets; use throttling, exponential backoff, jitter, and queued jobs to stay within quotas.[1][2]
- If not in an approved program, run in manual mode: import metrics via CSV, export drafts/schedules as JSON, and publish manually from the CLI output.[2][1]

## Repository structure
- cli/: command handlers (plan, draft, queue, metrics, replies).
- core/: prompting, retrieval, scheduling heuristics, analytics.
- data/: posts/, metrics/, schedules/ (JSON artifacts).
- docs/: API notes, compliance guide, examples.
- tests/: unit tests for planners, retrievers, and validators.

## Configuration
- config.json
{
  "topics": ["product", "engineering", "founder"],
  "tone": "practical, concise, conversational",
  "windows": [{"day": "Tue", "hour": 10}, {"day": "Thu", "hour": 11}],
  "experiment_spread_hours": 2,
  "manual_mode": true
}

- Set manual_mode to true unless approved API access is configured.[1][2]

## Roadmap
- Post variants A/B with automatic selection.
- Comment quality scoring and reply suggestions using simple heuristics.
- Lightweight dashboard for trends from JSON artifacts.
- Optional semantic-release style versioning and badges once stabilized.[8][9][10]

## Contributing
- Open an issue describing the change.
- Follow semantic versioning for any public API changes; use X.Y.Z and bump versions meaningfully.[10][8]
- Keep README and docs updated; remove empty sections and avoid broken links for good project hygiene.[11][2][1]

## License
- See LICENSE in the repository.
