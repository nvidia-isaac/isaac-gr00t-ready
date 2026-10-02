---
name: test-hw-si-01
description: Run criteria item HW-SI-01 Emergency Stop (E-stop) for a robot — find the e-stop procedures in the robot docs, guide the operator through triggering them on video, and record their score. Use when evaluating HW-SI-01.
---

# HW-SI-01 — Emergency Stop (E-stop)

Rubric (from `criteria/criteria.yaml`):
- **0** = No support
- **1** = Only on-robot stop or only remote-controller stop
- **2** = Both on-robot and remote-controller stop supported

This is a `manual` item — the operator performs it physically; you guide and record.

## Step 1 — Find and explain the e-stop procedures

Search the robot's sources (via `robots/<robot>/sources_index.md`) for every
stop mechanism: hardware e-stop button on the robot, remote-controller stop
combo, vendor app stop, software soft-stop / zero-torque mode. Then show the
operator a clear, compact instruction list: each mechanism, where it is, how to
trigger it, and what the robot should do when triggered (e.g. joints go limp /
power cut). Include any safety prep the docs require (robot suspended on a
gantry or placed in the vendor's low-torque safe mode first, clear
surroundings).

## Step 2 — Operator triggers each e-stop on camera

Ask the operator to:
1. Take a photo/video of each e-stop control (button on robot, controller combo, app screen).
2. With the robot in a safe state (suspended or supported, area clear), trigger
   each mechanism and film the robot's reaction.
3. Upload the videos/pictures to the dashboard (📎 button on the HW-SI-01 row),
   or drop them into `robots/<robot>/results/media/HW-SI-01/`.

Wait for the operator — do not proceed without their confirmation and media.

## Step 3 — Operator scores from the evidence

Ask the operator to review their video and give a score against the rubric
(which mechanisms actually stopped the robot?). Record in
`robots/<robot>/results/results.yaml`:
- `score`: their score
- `evidence`: which mechanisms worked, referencing the media filenames
- `executed: manual`

Then run `python3 -m gr00t_ready validate robots/<robot>` and
`python3 -m gr00t_ready board robots/<robot>`, and report the result in one or
two sentences.
