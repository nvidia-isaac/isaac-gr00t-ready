#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Sync repo skills into the directory your coding agent loads skills from, so
# it picks them up as /gr00t-onboard and /gr00t-test. Run before starting an
# evaluation session (safe to re-run; it mirrors this directory).
#
# Usage: skills/install.sh [<dest>]
#   <dest>  skills directory, relative to the repo root or absolute.
#           Defaults to $SKILLS_DIR, else .agents/skills.
#           Common agent locations: .agents/skills, .claude/skills,
#           .cursor/skills, .codex/skills (all gitignored).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src="$repo_root/skills"
dest="${1:-${SKILLS_DIR:-.agents/skills}}"
case "$dest" in
  /*) dst="$dest" ;;
  *)  dst="$repo_root/$dest" ;;
esac

mkdir -p "$dst"
for skill_dir in "$src"/*/; do
  name="$(basename "$skill_dir")"
  rm -rf "${dst:?}/$name"
  cp -r "$skill_dir" "$dst/$name"
  echo "installed $name -> $dest/$name"
done
