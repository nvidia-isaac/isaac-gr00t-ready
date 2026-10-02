# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""CLI for the GR00T-Ready toolkit.

Usage:
  python3 -m gr00t_ready checklist <robot_dir>   Generate a blank results.yaml skeleton
  python3 -m gr00t_ready validate  <robot_dir>   Check results.yaml against criteria
  python3 -m gr00t_ready score     <robot_dir>   Print gate verdicts and overall score
  python3 -m gr00t_ready report    <robot_dir>   Write reports/<robot>/<date>_report.md
  python3 -m gr00t_ready board     <robot_dir>   Progress kanban: print + write <robot_dir>/BOARD.md
  python3 -m gr00t_ready serve     <robot_dir> [--host 127.0.0.1] [--port 8321]
                                                   Live web dashboard
  python3 -m gr00t_ready items [--automation auto|semi|manual]   List criteria items
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .board import render_board, render_board_terminal
from .loader import REPO_ROOT, load_criteria, load_results, validate_results
from .report import render_report
from .scoring import score_evaluation


def cmd_items(args) -> int:
    for cat in load_criteria():
        rows = [
            i for i in cat.items if not args.automation or i.automation == args.automation
        ]
        if not rows:
            continue
        print(f"\n{cat.section} / {cat.name}")
        for i in rows:
            cond = " [conditional]" if i.conditional else ""
            print(f"  {i.id:<10} [{i.automation:<6}] max={i.max_score}{cond}  {i.name}")
    return 0


def cmd_checklist(args) -> int:
    robot_dir = Path(args.robot_dir)
    out = robot_dir / "results" / "results.yaml"
    if out.exists() and not args.force:
        print(f"error: {out} already exists (use --force to overwrite)", file=sys.stderr)
        return 1
    lines = [
        f"robot: {robot_dir.name}",
        "tier: official          # official | self-serve",
        f"evaluation_version: {__version__}",
        "date: YYYY-MM-DD",
        "evaluator: ",
        "",
        "# score: integer level, or invalid (conditional items only — feature absent,",
        "# excluded from totals). Leave score blank for untested items.",
        "results:",
    ]
    for cat in load_criteria():
        lines.append(f"  # ── {cat.section} / {cat.name} ──")
        for i in cat.items:
            levels = " | ".join(f"{k}={v}" for k, v in sorted(i.levels.items()))
            lines += [
                f"  {i.id}:  # {i.name} [{i.automation}]",
                f"    # {levels}",
                "    score:",
                "    evidence: ",
                "    notes: ",
            ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out} (evaluation version {__version__})")
    return 0


def _load(robot_dir: str):
    categories = load_criteria()
    evaluation = load_results(Path(robot_dir))
    problems = validate_results(categories, evaluation)
    return categories, evaluation, problems


def cmd_validate(args) -> int:
    _, evaluation, problems = _load(args.robot_dir)
    if problems:
        for p in problems:
            print(f"PROBLEM: {p}")
        return 1
    print(f"results.yaml is valid (evaluation version {evaluation.evaluation_version})")
    return 0


def cmd_score(args) -> int:
    categories, evaluation, problems = _load(args.robot_dir)
    for p in problems:
        print(f"WARNING: {p}", file=sys.stderr)
    score = score_evaluation(categories, evaluation)
    print(f"Robot: {evaluation.robot}   Tier: {evaluation.tier}   "
          f"Version: {evaluation.evaluation_version}   Date: {evaluation.date}")
    print(f"Overall: {score.verdict_label(score.overall_verdict)} "
          f"— {score.achieved}/{score.possible} ({score.percent:.1f}%)\n")
    for gate in score.gates:
        print(f"  {score.verdict_label(gate.verdict):<14} "
              f"{gate.achieved:>3}/{gate.possible:<3} {gate.category.name}")
    return 0


def cmd_report(args) -> int:
    categories, evaluation, problems = _load(args.robot_dir)
    for p in problems:
        print(f"WARNING: {p}", file=sys.stderr)
    score = score_evaluation(categories, evaluation)
    out_dir = REPO_ROOT / "reports" / evaluation.robot
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{evaluation.date}_report.md"
    out.write_text(render_report(score))
    print(f"wrote {out} (evaluation version {evaluation.evaluation_version})")
    return 0


def cmd_board(args) -> int:
    robot_dir = Path(args.robot_dir)
    categories = load_criteria()
    evaluation = load_results(robot_dir)
    print(render_board_terminal(categories, evaluation, robot_dir))
    out = robot_dir / "BOARD.md"
    out.write_text(render_board(categories, evaluation, robot_dir))
    print(f"\nwrote {out}")
    return 0


def cmd_serve(args) -> int:
    from .server import serve
    serve(Path(args.robot_dir), host=args.host, port=args.port,
          upload_password=args.upload_password)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="gr00t_ready", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("items", help="list criteria items")
    p.add_argument("--automation", choices=["auto", "semi", "manual"])
    p.set_defaults(func=cmd_items)

    p = sub.add_parser("checklist", help="generate blank results.yaml for a robot")
    p.add_argument("robot_dir")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_checklist)

    for name, func in (("validate", cmd_validate), ("score", cmd_score),
                       ("report", cmd_report), ("board", cmd_board)):
        p = sub.add_parser(name)
        p.add_argument("robot_dir")
        p.set_defaults(func=func)

    p = sub.add_parser("serve", help="live web dashboard")
    p.add_argument("robot_dir")
    p.add_argument("--host", default="127.0.0.1",
                   help="interface to bind (default: 127.0.0.1; use 0.0.0.0 for LAN access)")
    p.add_argument("--port", type=int, default=8321)
    p.add_argument("--upload-password",
                   help="password required for evidence uploads (auto-generated and printed if omitted)")
    p.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
