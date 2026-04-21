#!/usr/bin/env python3
import argparse
from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib
from typing import cast

from .operations.implement import run_implement_crew
from .operations.refactor import run_refactor_crew
from .operations.review import run_review_crew
from .operations.strategize import run_strategize_crew
from .operations.task import run_task_crew
from .utils.constants import MODEL

# Configuration via Environment Variables with sensible defaults


class CliArgs(argparse.Namespace):
    command: str
    file: str
    max_iterations: int
    task: str
    write: bool

    def __init__(self) -> None:
        super().__init__()
        self.command = ""
        self.file = ""
        self.max_iterations = 2
        self.task = ""
        self.write = False


def get_package_version() -> str:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if pyproject_path.exists():
        with pyproject_path.open("rb") as pyproject_file:
            pyproject = cast(Mapping[str, object], tomllib.load(pyproject_file))
        project = pyproject.get("project")
        if not isinstance(project, dict):
            return "unknown"

        project_version = cast(dict[str, object], project).get("version")
        if isinstance(project_version, str):
            return project_version

    try:
        return version("agents")
    except PackageNotFoundError:
        return "unknown"


def extract_first_code_block(text: str) -> str | None:
    in_block = False
    found_block = False
    extracted: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_block:
                break
            in_block = True
            found_block = True
            continue

        if in_block:
            extracted.append(line)

    if not found_block:
        return None

    return "\n".join(extracted).strip()


def main():
    parser = argparse.ArgumentParser(
        description="Tauri-Agent: Multi-agent pipeline for Tauri apps"
    )
    _ = parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_package_version()}",
    )
    _ = parser.add_argument("--file", "-f", required=True, help="Target file path")
    _ = parser.add_argument(
        "--write",
        action="store_true",
        help="Overwrite file with reviewed code (creates .bak)",
    )
    _ = parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
        help="Maximum Delta/Optimizer/Reviewer 2 loop iterations for task command",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    refactor_p = subparsers.add_parser("refactor", help="Refactor existing code")
    _ = refactor_p.add_argument(
        "task", nargs="?", default="Refactor for readability and safety"
    )

    implement_p = subparsers.add_parser("implement", help="Implement new features")
    _ = implement_p.add_argument(
        "task", nargs="?", default="Implement the feature idiomatically"
    )

    review_p = subparsers.add_parser("review", help="Review existing code")
    _ = review_p.add_argument(
        "task", nargs="?", default="Review for correctness, safety, and maintainability"
    )

    strategize_p = subparsers.add_parser(
        "strategize", help="Create an implementation strategy"
    )
    _ = strategize_p.add_argument(
        "task", nargs="?", default="Create a safe implementation strategy"
    )

    task_p = subparsers.add_parser(
        "task",
        help="Run strategy, implementation, review, delta, and optimization loop",
    )
    _ = task_p.add_argument(
        "task", nargs="?", default="Implement the feature through review"
    )

    args = CliArgs()
    _ = parser.parse_args(namespace=args)

    print(f"🚀 Running {args.command} using model: {MODEL}")
    match args.command:
        case "refactor":
            result = run_refactor_crew(args.task, args.file)
        case "implement":
            result = run_implement_crew(args.task, args.file)
        case "review":
            result = run_review_crew(args.task, args.file)
        case "strategize":
            result = run_strategize_crew(args.task, args.file)
        case "task":
            result = run_task_crew(args.task, args.file, args.max_iterations)
        case _:
            parser.error(f"Unknown command: {args.command}")
    print("\n" + "=" * 90 + "\n" + str(result))

    if args.write:
        extracted = extract_first_code_block(str(result))
        if extracted is not None:
            target_path = Path(args.file)
            backup = target_path.with_suffix(target_path.suffix + ".bak")
            _ = target_path.rename(backup)
            _ = target_path.write_text(extracted)
            print(f"\n✅ Updated {args.file} (Backup: {backup})")
        else:
            print("\n⚠️ Extraction failed. Manual copy required.")


if __name__ == "__main__":
    main()
