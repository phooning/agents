#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

# Configuration via Environment Variables with sensible defaults
BASE_URL = os.getenv("TAURI_AGENT_BASE_URL", "http://localhost:11434/v1")
MODEL = os.getenv("TAURI_AGENT_MODEL", "Qwen3.6-35B-A3B")
API_KEY = os.getenv("TAURI_AGENT_API_KEY", "no-key-required")


def get_llm(temperature=0.2):
    return ChatOpenAI(
        model=MODEL,
        base_url=BASE_URL,
        api_key=SecretStr(API_KEY),
        temperature=temperature,
    )


def run_tauri_refactor_crew(task_description: str, target_file: str):
    llm = get_llm(temperature=0.2)

    # === AGENTS ===
    analyst = Agent(
        role="Tauri Context Analyst",
        goal="Deeply understand the file in the context of a full Tauri app (Rust backend + TS/React frontend)",
        backstory="Expert at analyzing Tauri projects: Rust commands, invokes, TypeScript bridges, and build flow.",
        llm=llm,
        verbose=True,
    )

    architect = Agent(
        role="Tauri Software Architect",
        goal="Design an optimal refactoring strategy that respects Tauri constraints",
        backstory="Senior architect specialized in Tauri: safe Rust-TS interop and performance.",
        llm=llm,
        verbose=True,
    )

    implementer = Agent(
        role="Senior Tauri Developer",
        goal="Implement the refactoring cleanly across Rust or TypeScript/React",
        backstory="Full-stack Tauri developer writing idiomatic Rust and clean React.",
        llm=llm,
        verbose=True,
    )

    reviewer = Agent(
        role="Tauri Code Reviewer",
        goal="Review changes for correctness, safety, and Tauri-specific issues",
        backstory="Strict senior reviewer focused on command safety and type consistency.",
        llm=llm,
        verbose=True,
    )

    # === TASKS ===
    t1_analysis = Task(
        description=f"Analyze '{target_file}'. Describe logic, Tauri invokes/commands, and improvement opportunities.",
        agent=analyst,
        expected_output="Structured analysis summary with Tauri context.",
    )

    t2_strategy = Task(
        description=f"Create a step-by-step refactoring plan for: {task_description}.",
        agent=architect,
        context=[t1_analysis],
        expected_output="Bulleted refactoring strategy with rationale.",
    )

    t3_execution = Task(
        description="Apply the strategy and output the COMPLETE refactored code.",
        agent=implementer,
        context=[t1_analysis, t2_strategy],
        expected_output="Full refactored code inside a single markdown code block.",
    )

    t4_review = Task(
        description="Review for Tauri best practices and type consistency. Approve or suggest fixes.",
        agent=reviewer,
        context=[t1_analysis, t2_strategy, t3_execution],
        expected_output="Detailed review + final approved code block.",
    )

    crew = Crew(
        agents=[analyst, architect, implementer, reviewer],
        tasks=[t1_analysis, t2_strategy, t3_execution, t4_review],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff(inputs={"task": task_description, "file": target_file})


def run_tauri_implement_crew(task_description: str, file: str):
    llm = get_llm(temperature=0.3)

    analyst = Agent(
        role="Tauri Requirements Analyst",
        goal="Map feature requests to the existing Tauri codebase",
        backstory="Expert at breaking down features into Rust commands and frontend components.",
        llm=llm,
        verbose=True,
    )

    architect = Agent(
        role="Tauri Solution Architect",
        goal="Design a consistent implementation plan across Rust and TypeScript",
        backstory="Senior architect ensuring safe interop and minimizing breaking changes.",
        llm=llm,
        verbose=True,
    )

    implementer = Agent(
        role="Senior Tauri Full-Stack Developer",
        goal="Implement the feature across necessary files",
        backstory="Pragmatic developer producing clean Rust and modern React.",
        llm=llm,
        verbose=True,
    )

    reviewer = Agent(
        role="Tauri Implementation Reviewer",
        goal="Validate implementation for safety and Tauri best practices",
        backstory="Checks invoke signatures, type safety, and security scopes.",
        llm=llm,
        verbose=True,
    )

    t1_analysis = Task(
        description=f"Identify files needing changes for feature: '{task_description}'.",
        agent=analyst,
        expected_output="File impact list.",
    )

    t2_strategy = Task(
        description=f"Step-by-step plan for: {task_description}.",
        agent=architect,
        context=[t1_analysis],
        expected_output="Bulleted implementation strategy.",
    )

    t3_execution = Task(
        description="Implement according to plan. Output complete code for each file.",
        agent=implementer,
        context=[t1_analysis, t2_strategy],
        expected_output="Full code for all affected files in labeled markdown blocks.",
    )

    t4_review = Task(
        description="Review for compatibility and completeness.",
        agent=reviewer,
        context=[t1_analysis, t2_strategy, t3_execution],
        expected_output="Review summary + final approved code blocks.",
    )

    crew = Crew(
        agents=[analyst, architect, implementer, reviewer],
        tasks=[t1_analysis, t2_strategy, t3_execution, t4_review],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff(inputs={"task": task_description})


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

    args = parser.parse_args()

    crew_fn = (
        run_tauri_refactor_crew
        if args.command == "refactor"
        else run_tauri_implement_crew
    )

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
