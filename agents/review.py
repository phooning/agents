from crewai import Agent, Crew, Process, Task

from utils.llm import get_llm


def run_tauri_review_crew(task_description: str, target_file: str):
    llm = get_llm(temperature=0.1)

    analyst = Agent(
        role="Code Context Analyst",
        goal="Understand the target file and its role in the Tauri application",
        backstory="Expert at mapping Rust commands, TypeScript invokes, state flow, and project boundaries.",
        llm=llm,
        verbose=True,
    )

    reviewer = Agent(
        role="Senior Code Reviewer",
        goal="Identify correctness, safety, type, security, and maintainability issues",
        backstory="Strict reviewer focused on concrete defects, regressions, interop mismatches, and missing tests.",
        llm=llm,
        verbose=True,
    )

    fixer = Agent(
        role="Review Fix Strategist",
        goal="Turn review findings into minimal, safe fixes when code changes are needed",
        backstory="Pragmatic engineer who keeps patches small and aligned with the existing code style.",
        llm=llm,
        verbose=True,
    )

    approver = Agent(
        role="Final Review Approver",
        goal="Validate that findings and proposed fixes are complete and actionable",
        backstory="Senior maintainer who confirms compatibility, risk, and whether final code is ready to apply.",
        llm=llm,
        verbose=True,
    )

    t1_context = Task(
        description=f"Analyze '{target_file}' for the review request: {task_description}.",
        agent=analyst,
        expected_output="Concise file context summary, dependencies, and Tauri integration points.",
    )

    t2_review = Task(
        description=(
            "Review the target for bugs, unsafe assumptions, interop mismatches, "
            "type issues, security scope problems, and missing validation or tests."
        ),
        agent=reviewer,
        context=[t1_context],
        expected_output="Prioritized review findings with severity, rationale, and concrete locations when possible.",
    )

    t3_fixes = Task(
        description=(
            "If fixes are needed, propose the smallest compatible code changes. "
            "If no fixes are needed, explain why no code changes are recommended."
        ),
        agent=fixer,
        context=[t1_context, t2_review],
        expected_output="Fix plan and final corrected code blocks only when changes are necessary.",
    )

    t4_approval = Task(
        description="Validate the review and fixes for completeness, compatibility, and residual risk.",
        agent=approver,
        context=[t1_context, t2_review, t3_fixes],
        expected_output="Final review summary, approval status, residual risks, and final approved code blocks if applicable.",
    )

    crew = Crew(
        agents=[analyst, reviewer, fixer, approver],
        tasks=[t1_context, t2_review, t3_fixes, t4_approval],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff(inputs={"task": task_description, "file": target_file})
