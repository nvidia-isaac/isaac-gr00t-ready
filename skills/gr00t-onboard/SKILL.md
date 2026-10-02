---
name: gr00t-onboard
description: Onboard a new robot platform into the GR00T-Ready evaluation — create the robot profile, register doc/SDK sources, build the source index, and fill the spec sheet. Use when the user says a new robot is coming or provides robot docs/SDK for evaluation.
---

# Onboard a new robot

Arguments: `<robot_name>` plus whatever doc/SDK locations the user provides.

1. **Create the profile.** Copy `robots/_template/` to `robots/<robot_name>/`.
2. **Ask the user to fill in sources.** The user fills
   `robots/<robot_name>/sources.yaml` with the doc/SDK locations — local file
   paths (`type: local`), doc-site URLs (`type: web`), git repos (`type: git`),
   each tagged with `topics`. Do NOT search the web for sources yourself; wait
   for the user to provide them. Point the user at the file, remind them of the
   three source types, and pause until they say it's ready. After they fill it,
   review it and ask about key areas with no source (SDK API, datasheet,
   security/OTA docs).
3. **Index the sources — do NOT read the docs fully.** Skim only tables of
   contents, section headings, and file/directory listings. Write
   `robots/<robot_name>/sources_index.md` mapping topics to exact locations
   (source + chapter/page/path). For large sources, delegate the skim to a
   read-only subagent if your agent supports them.
4. **Fill the spec sheet.** Read ONLY the spec/datasheet tables and fill the
   `specs:` block in `robot.yaml` — generated tests compare measurements against
   these values. Also fill `connection:` (SSH to the onboard Thor) and `sdk:`
   details from the user.
5. **Confirm readiness.** Summarize for the user: sources registered, index
   built, specs filled, anything missing or ambiguous. Then suggest starting the
   evaluation with `/gr00t-test <robot_name>` (one criteria item at a time).

Do not generate any test cases during onboarding — tests are created one by one
during `/gr00t-test`, each with its own targeted doc lookup.
