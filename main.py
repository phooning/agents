#!/usr/bin/env python3
import argparse
from pathlib import Path

from agents.implement import run_tauri_implement_crew
from agents.refactor import run_tauri_refactor_crew
from agents.review import run_tauri_review_crew
from agents.strategize import run_tauri_strategize_crew
from utils.constants import MODEL

# Configuration via Environment Variables with sensible defaults


def main():
    parser = argparse.ArgumentParser(
        description="Tauri-Agent: Multi-agent pipeline for Tauri apps"
    )
    parser.add_argument("--file", "-f", required=True, help="Target file path")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Overwrite file with reviewed code (creates .bak)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    refactor_p = subparsers.add_parser("refactor", help="Refactor existing code")
    refactor_p.add_argument(
        "task", nargs="?", default="Refactor for readability and safety"
    )

    implement_p = subparsers.add_parser("implement", help="Implement new features")
    implement_p.add_argument(
        "task", nargs="?", default="Implement the feature idiomatically"
    )

    review_p = subparsers.add_parser("review", help="Review existing code")
    review_p.add_argument(
        "task", nargs="?", default="Review for correctness, safety, and maintainability"
    )

    strategize_p = subparsers.add_parser(
        "strategize", help="Create an implementation strategy"
    )
    strategize_p.add_argument(
        "task", nargs="?", default="Create a safe implementation strategy"
    )

    args = parser.parse_args()

    crew_fns = {
        "refactor": run_tauri_refactor_crew,
        "implement": run_tauri_implement_crew,
        "review": run_tauri_review_crew,
        "strategize": run_tauri_strategize_crew,
    }
    crew_fn = crew_fns[args.command]

    print(f"🚀 Running {args.command} using model: {MODEL}")
    result = crew_fn(args.task, args.file)
    print("\n" + "=" * 90 + "\n" + str(result))

    if args.write:
        lines = str(result).splitlines()
        in_block = False
        extracted = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                if not in_block and any(
                    stripped.startswith(f"```{lang}")
                    for lang in ("rust", "tsx", "ts", "json")
                ):
                    in_block = True
                    continue
                elif in_block:
                    break
            if in_block:
                extracted.append(line)

        if extracted:
            target_path = Path(args.file)
            backup = target_path.with_suffix(target_path.suffix + ".bak")
            target_path.rename(backup)
            target_path.write_text("\n".join(extracted).strip())
            print(f"\n✅ Updated {args.file} (Backup: {backup})")
        else:
            print("\n⚠️ Extraction failed. Manual copy required.")


if __name__ == "__main__":
    main()
