---
name: gr00t-test
description: Run one GR00T-Ready criteria test item for a robot — targeted doc lookup, test generation, execution, and result recording. Use when the user wants to run/continue the evaluation of a robot against criteria items (e.g. "/gr00t-test my_robot HW-OC-01" or "test the next item").
---

# Run one GR00T-Ready criteria test

The evaluation's `results/results.yaml` must retain the `evaluation_version`
written by `python3 -m gr00t_ready checklist`. Do not remove or rewrite it while
recording individual results.

Arguments: `<robot_name> [item_id ...]`. If no item id is given, pick the next
untested applicable item in `criteria/criteria.yaml` order (check
`robots/<robot_name>/results/results.yaml` for what's already scored).

Process exactly ONE item at a time, completing the full cycle below before the
next. Never batch-generate tests for items you haven't reached yet.

## Per-item skills

Each criteria item gets its own skill at `skills/test-<item-id-lowercase>/SKILL.md`
(e.g. `skills/test-hw-si-01/`) encoding that item's exact procedure. Before the
generic cycle below:
- If a per-item skill EXISTS for this item, follow it (it takes precedence).
- If it does NOT exist, create it first — write the SKILL.md capturing the
  concrete procedure for this item (doc findings, operator steps, scoring), run
  `skills/install.sh`, then follow it. This way every test run leaves a
  reusable, refinable procedure behind.

## Cycle for one item

1. **Load the item.** Read its entry in `criteria/criteria.yaml`: method, the
   0/1/2 rubric (`levels`), `automation` class, `conditional` flag. The rubric
   is the ONLY basis for scoring — do not invent thresholds.
2. **Check applicability.** If `conditional: true` and `robot.yaml` specs show
   the hardware is absent, record `score: invalid` with a note and stop here.
   If the item is already scored in `results.yaml`, ask before re-running.
   If testing reveals the platform does NOT have the feature at all (and the
   item isn't yet conditional): unsupported = INVALID, not a 0 — prove the
   absence, mark the item `conditional: true` in criteria.yaml with an explanatory
   comment (plus a FRAMEWORK_FEEDBACK.md row if the tracker is open), score `invalid` with the evidence, and update
   robot.yaml. Invalid items are excluded from the score totals entirely.
3. **Targeted knowledge lookup — never read a whole manual.**
   - Consult `robots/<robot_name>/sources_index.md` and the `topics` tags in
     `sources.yaml` to pick the ONE source likely to answer this item.
   - Search within it: grep local files/SDK code, fetch only the specific doc
     page. For large sources, delegate to a read-only subagent (if your agent
     supports them) with a narrow question ("what API reads joint states and
     at what rate?") so the main context stays small.
   - If the index lacks the topic, extend `sources_index.md` with what you find.
4. **Generate the test** in `robots/<robot_name>/tests/`:
   - Filename: `test_<ITEM_ID with dashes as underscores>.py` (e.g.
     `test_HW_OC_01.py`).
   - `auto`: runs unattended (SSH to the Thor uses `connection:` from
     `robot.yaml`). `semi`: prompts the operator for physical setup first.
   - Last line of output must be one JSON object:
     `{"id": "<ITEM-ID>", "score": <int>, "evidence": "<measured values>", "notes": ""}`
   - The script must measure and print evidence (actual numbers), not just
     pass/fail — evidence goes into the report.
   - Never run remote `sudo` inside a pipeline — its password prompt is
     swallowed by the pipe and the run looks hung (sudo tickets are per-tty,
     so a prior `sudo -v` in another ssh session does NOT carry over). Instead:
     start the privileged command in the background on the remote host from a
     visible `ssh -t` session (prompt appears normally), log to a remote file,
     then stream that file back with a plain sudo-free ssh + `tail -F`.
   - Long runs (> ~10 minutes) must (a) start with a ~1-minute SANITY PHASE
     that validates the data stream / preconditions and aborts early on
     failure — never bet an hour on unverified assumptions — and (b) run a
     mid-run WATCHDOG that aborts loudly if the stream dies or preconditions
     break (e.g. robot moved during an at-rest capture).
   - Any phase longer than ~15 seconds must show LIVE progress: a progress
     bar with percent and elapsed/total plus the current measurement per
     line. Beware buffering: use `python3 -u` / `flush=True` / line-buffered
     awk, and never end a live pipeline in `tail`/`sort` — operator-facing
     runs must not go silent.
   - `manual` items: no script. Append a section to `tests/manual_checklist.md`
     with concrete numbered steps, the rubric, and blanks for score/evidence;
     then ask the operator to perform it and report back.
5. **Safety rules for execution (hard requirements):**
   - Never command robot motion (joints, locomotion, WBC, teleop) without the
     operator explicitly confirming the robot is in a safe state with E-stop
     within reach. Print a confirmation prompt in the test itself.
   - Motion-test rules (evaluator-mandated): (1) the agent never triggers motion —
     the EVALUATOR runs the script and each movement fires on their Enter;
     (2) load the joint limits from the vendor model BEFORE any command and
     refuse targets outside them; (3) announce every movement (joint,
     direction, degrees) before sending, then require the evaluator's visual
     confirmation AND a state read-back that the target was reached;
     (4) movements small but visible (several degrees, hard-capped);
     (5) targets reached via a 1-second interpolated trajectory (delta/rate
     increments), never an instantaneous setpoint jump.
   - Respect joint limits from `robot.yaml` specs; command conservative
     amplitudes and speeds by default.
   - Read-only checks (versions, topics, bandwidth, sensor streams) may run
     without confirmation.
   - Long-duration tests (endurance, stability hours) should log progress to
     `tests/output/` and be resumable/interruptible.
6. **Score strictly against the rubric.** Map the measured evidence to the
   highest level whose criteria text is fully satisfied. When measurement is
   ambiguous, score the LOWER level and explain in notes. Never round up.
   If the RUBRIC ITSELF proves unreasonable for the platform class (wrong
   sensor grade, impossible threshold on fitted hardware, undefined term),
   additionally add a row to `FRAMEWORK_FEEDBACK.md` (the revisit tracker,
   created at the repo root if it does not exist — it is deleted once every
   row has been revisited) — score conservatively now, revisit at
   evaluation end.
7. **Record immediately** in `robots/<robot_name>/results/results.yaml`: score,
   evidence (measured values), notes, and `executed: auto|semi|manual`. Then run
   `python3 -m gr00t_ready validate robots/<robot_name>` to confirm the entry is
   valid. Progress must survive an interrupted session. Then refresh the
   progress board: `python3 -m gr00t_ready board robots/<robot_name>` (updates
   `BOARD.md` — the user's kanban view of all items, statuses, and scores).
8. **Report progress** to the user in one or two sentences (item, score,
   evidence), then continue with the next item if they asked for more than one.

## When something blocks a test

- SDK/API missing for the measurement → tell the user what's missing and leave
  the item untested (blank score). Track blockers in
  `robots/<robot_name>/BLOCKERS.md`.
- Never fabricate evidence or scores. An unrun test stays untested.
