# GR00T-Ready Auto-Validation Repo

This repo turns the GR00T-Ready evaluation framework into an automated validation
pipeline. When a new robot platform arrives, a coding agent reads the robot's
docs/SDK, generates test cases for every criteria item, runs what can be run,
scores the platform, and produces a detailed report.

This file is the agent's project instructions. It is agent-neutral: point your
agent at it directly, or copy/symlink it to the filename your agent loads
automatically (for example `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`).

## Layout

- `GR00T_Ready_Evaluation_Framework.md` — the human-readable framework (source document).
- `VERSION` — the evaluation pipeline version. New result checklists record this
  value as `evaluation_version`; boards, dashboards, scores, and reports must
  display the recorded value so evaluation artifacts remain traceable.
- `criteria/criteria.yaml` — machine-readable criteria derived from the markdown.
  **Source of truth for automation.** Every scored item has a stable id (e.g.
  `HW-OC-01`), a 0/1/2 rubric, and an `automation` class (auto/semi/manual).
  Certification **must-have** items (the Must-Have column in
  `GR00T_Ready_Evaluation_Framework.md`) carry
  `must_have: true` + `must_have_level: N` — any must-have scoring below N blocks
  certification. Surfaced in score/board/report and the dashboard (⭐ badge,
  must-have KPI + filter; unmet must-haves flagged red).
- `gr00t_ready/` — Python toolkit (needs `pyyaml` only):
  - `python3 -m gr00t_ready items` — list all criteria items
  - `python3 -m gr00t_ready checklist robots/<name>` — blank results skeleton
  - `python3 -m gr00t_ready validate robots/<name>` — sanity-check recorded results
  - `python3 -m gr00t_ready score robots/<name>` — gate verdicts + overall score
  - `python3 -m gr00t_ready report robots/<name>` — write `reports/<name>/<date>_report.md`
  - `python3 -m gr00t_ready board robots/<name>` — progress kanban: prints a compact
    view and writes `robots/<name>/BOARD.md` (statuses derived from repo state:
    scored = done, test file but no score = in progress, id in `BLOCKERS.md` =
    blocked, else to-do). Refresh it after every recorded result.
  - `python3 -m gr00t_ready serve robots/<name> [--host 127.0.0.1] [--port 8321]`
    — live web dashboard
    (same statuses as the board, auto-refreshes every 2 s by re-reading repo state;
    page lives in `gr00t_ready/web/index.html` and is safe to restyle freely).
    Uploads are password-protected: pass `--upload-password <pw>` to `serve`,
    or one is auto-generated and printed at startup; the page prompts once per
    browser session (wrong password → 401 → re-prompt).
    Each item row has a 📎 upload button for evidence photos/videos, saved to
    `robots/<name>/results/media/<ITEM-ID>/` (gitignored — sync that tree to
    cloud storage) and displayed inline as thumbnails/links.
- `skills/` — versioned skills (one `SKILL.md` per directory, in the common
  Agent Skills format) that encode the rules for onboarding (`gr00t-onboard`)
  and per-item testing (`gr00t-test`). They are the source of truth;
  `skills/install.sh [<dest>]` copies them into the directory your agent loads
  skills from (default `.agents/skills/`; pass e.g. `.claude/skills/` or
  `.cursor/skills/` for other agents — all gitignored) so the agent can invoke
  them as `/gr00t-onboard` and `/gr00t-test`. Run the install script at the
  start of a test session, or after editing a skill.
- `robots/<name>/` — one directory per robot: `robot.yaml` (profile/specs/connection),
  `sources.yaml` (manifest of doc/SDK locations — local paths, websites, git repos),
  `tests/` (generated test cases), `results/results.yaml` (recorded scores).
- `reports/<name>/` — generated evaluation reports.

## Workflow: onboarding a new robot

The detailed, authoritative rules live in the skills: `skills/gr00t-onboard/SKILL.md`
for steps 1–2 and `skills/gr00t-test/SKILL.md` for step 3 (including safety rules
for commanding the robot). Run `skills/install.sh` first so they are invocable as
`/gr00t-onboard` and `/gr00t-test`. Summary of the flow:

1. **Create the profile.** Copy `robots/_template/` to `robots/<robot_name>/`.
   Fill `sources.yaml` with every doc/SDK location the user provides — local file
   paths, doc-site URLs, git repos — tagged with `topics` so later steps know
   what to read for which criteria area.
2. **Index the sources — do NOT read the docs fully.** Build a lightweight index
   so later lookups are targeted: skim tables of contents, section headings, and
   file listings only, and record in `robots/<name>/sources_index.md` which
   source/section/file covers which topic (joint API here, camera specs there,
   security chapter there). Fill the `specs:` block of `robot.yaml` from the
   spec/datasheet tables only. Ask the user about anything ambiguous or missing.
3. **Process criteria items ONE BY ONE.** Iterate `criteria/criteria.yaml` in
   order (or the subset the user asks for). For each item, run a full
   generate → execute → record cycle before moving to the next:
   1. *Targeted lookup:* find only the API/knowledge this item needs, using
      `sources_index.md` and the `topics` tags to pick the source, then search
      within it (grep local files/SDK, fetch only the specific doc page).
      Never read a whole manual for one item; when the source is large,
      delegate the lookup to a read-only subagent (if your agent supports
      them) so the main context stays small.
   2. *Generate the test* under `robots/<name>/tests/` (conventions in
      `tests/README.md`):
      - `auto` → executable script using the robot's SDK / SSH to the Thor,
        ending with one JSON line: `{"id", "score", "evidence", "notes"}`.
      - `semi` → script that prompts the operator for setup, then measures.
      - `manual` → entry in `tests/manual_checklist.md` with concrete steps
        and the scoring rubric.
      - `conditional: true` items → record `invalid` when the robot lacks the
        hardware (check `robot.yaml` specs) and skip test generation.
   3. *Execute* it (auto/semi) or hand the operator the checklist entry
      (manual) and wait for their reported outcome.
   4. *Record the result immediately* in `results/results.yaml` (score,
      evidence, notes) before starting the next item — progress must survive
      an interrupted session, and `python3 -m gr00t_ready score` should show
      partial progress at any time.
4. **Score and report.** `validate` → `score` → `report`. The report includes gate
   verdicts (Pass/Conditional/Fail per the framework's Phase 2), blockers, gaps
   with remediation targets, and untested items. Can be run mid-evaluation;
   untested items show as Incomplete.

## Scoring rules (implemented in `gr00t_ready/scoring.py`)

Per gate (category): **Fail** if any applicable item scored 0; **Pass** if every
applicable item reached its max defined level; **Conditional** otherwise;
**Incomplete** if applicable items are untested. Self-Serve tier relabels these
Compatible / Partial / Not Compatible and skips the non-technical gates
(`tier1_only: true` categories).

**Unsupported items are invalid, not failures** (evaluator policy):
when a platform simply does not have the hardware/feature an item measures
(e.g. F/T sensors, vision-based tactile), the item is marked `invalid` and REMOVED
from the totals — it contributes to neither achieved nor possible points, and
the gate verdict ignores it. Workflow: (1) prove the absence (probe/docs),
(2) mark the item `conditional: true` in `criteria/criteria.yaml` with an
explanatory comment (plus a FRAMEWORK_FEEDBACK.md row if the tracker is open),
(3) score `invalid` with the absence evidence, (4) record the confirmation in
robot.yaml specs. `validate` rejects `invalid` on
non-conditional items, so step 2 is what authorizes step 3.

## Rubric feedback loop

Rubrics sometimes prove unreasonable, ambiguous, or unexecutable against real
hardware (wrong sensor class, ">1 Gbps" on 1 GbE hardware, undefined terms,
single-level rubrics...). Whenever a test fights its rubric: create
`FRAMEWORK_FEEDBACK.md` at the repo root if it does not exist, add a row (item,
rubric, why unsuitable, measured value, provisional score + interpretation, proposed
fix, status=open), score the item conservatively with a note, and move on. At
evaluation end the open rows get revisited: rubric fixed in
`criteria/criteria.yaml` **and** the matching row of
`GR00T_Ready_Evaluation_Framework.md`, result re-scored, status flipped to
`revisited`. Once every row is revisited the tracker is deleted — each fix
carries its own dated rationale comment in `criteria/criteria.yaml`, so the
tracker is a work queue, not the archive (see git history for past rounds).

## Keeping criteria in sync

If `GR00T_Ready_Evaluation_Framework.md` changes, update `criteria/criteria.yaml`
to match (same ids for unchanged items; new ids for new items — never reuse an id
with a different meaning, since results files reference them).
