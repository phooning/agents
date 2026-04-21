from crewai import Agent, Crew, Process, Task

from utils.llm import get_llm


def run_tauri_strategize_crew(task_description: str, target_file: str):
    llm = get_llm(temperature=0.25)

    analyst = Agent(
        role="Requirements Strategist",
        goal="Clarify the requested outcome and map it to the existing project surface",
        backstory="Expert at turning ambiguous feature or refactor requests into concrete engineering constraints.",
        llm=llm,
        verbose=True,
    )

    code_mapper = Agent(
        role="Codebase Mapper",
        goal="Identify likely files, APIs, commands, invokes, and state boundaries affected by the request",
        backstory="Tauri-aware engineer who understands Rust backends, TypeScript frontends, and bridge contracts.",
        llm=llm,
        verbose=True,
    )

    architect = Agent(
        role="Implementation Strategist",
        goal="Design a safe, incremental implementation strategy",
        backstory="Senior architect focused on minimizing breakage while preserving project conventions.",
        llm=llm,
        verbose=True,
    )

    risk_reviewer = Agent(
        role="Strategy Reviewer",
        goal="Stress-test the plan for gaps, risks, tests, and rollout order",
        backstory="Pragmatic reviewer who catches incomplete plans before implementation starts.",
        llm=llm,
        verbose=True,
    )

    t1_requirements = Task(
        description=f"Clarify requirements and constraints for: {task_description}. Target file: '{target_file}'.",
        agent=analyst,
        expected_output="Requirements summary, assumptions, open questions, and acceptance criteria.",
    )

    t2_mapping = Task(
        description="Map the request to likely affected files, commands, invokes, components, and data flow.",
        agent=code_mapper,
        context=[t1_requirements],
        expected_output="Impact map with affected files, interfaces, and dependencies.",
    )

    t3_strategy = Task(
        description="Create an incremental implementation plan with validation steps.",
        agent=architect,
        context=[t1_requirements, t2_mapping],
        expected_output="Step-by-step strategy, sequencing, and expected code changes without full code.",
    )

    t4_review = Task(
        description="Review the strategy for missing steps, risks, testing gaps, and compatibility concerns.",
        agent=risk_reviewer,
        context=[t1_requirements, t2_mapping, t3_strategy],
        expected_output="Final strategy with risks, mitigations, test plan, and go/no-go recommendation.",
    )

    crew = Crew(
        agents=[analyst, code_mapper, architect, risk_reviewer],
        tasks=[t1_requirements, t2_mapping, t3_strategy, t4_review],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff(inputs={"task": task_description, "file": target_file})
