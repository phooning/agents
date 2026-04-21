import re

from crewai import Agent, Crew, Process, Task

from utils.llm import get_llm


def _review_passed(result: object) -> bool:
    match = re.search(
        r"OVERALL[_ ]STATUS:\s*(PASS|PARTIAL|FAIL)",
        str(result),
        re.I,
    )
    return bool(match and match.group(1).upper() == "PASS")


def _build_agents(llm):
    strategist = Agent(
        role="Feature Strategist",
        goal="Blueprint the requested feature with acceptance criteria before implementation starts",
        backstory="Senior product-minded engineer who turns feature requests into precise, testable blueprints.",
        llm=llm,
        verbose=True,
    )

    implementer = Agent(
        role="Task Implementer",
        goal="Implement the feature according to the strategy blueprint",
        backstory="Pragmatic software engineer who produces complete, idiomatic code with minimal unrelated churn.",
        llm=llm,
        verbose=True,
    )

    reviewer_one = Agent(
        role="Reviewer 1",
        goal="Review the implementation against the initial strategy blueprint",
        backstory="Strict reviewer focused on correctness, completeness, regressions, and missed requirements.",
        llm=llm,
        verbose=True,
    )

    delta = Agent(
        role="Delta Analyst",
        goal="Identify the delta between the strategy blueprint, implementation, and review findings",
        backstory="Test-focused engineer who translates gaps into PASS, PARTIAL, and FAIL validation conditions.",
        llm=llm,
        verbose=True,
    )

    optimizer = Agent(
        role="Optimizer",
        goal="Close the delta between the implementation and the issue-resolution plan",
        backstory="Senior engineer who fixes only the remaining gaps and preserves already-correct behavior.",
        llm=llm,
        verbose=True,
    )

    reviewer_two = Agent(
        role="Reviewer 2",
        goal="Review the optimized implementation against every feature in the initial blueprint",
        backstory="Final reviewer who verifies each acceptance criterion and decides whether the loop can stop.",
        llm=llm,
        verbose=True,
    )

    return strategist, implementer, reviewer_one, delta, optimizer, reviewer_two


def _run_initial_loop(task_description: str, target_file: str, max_iterations: int):
    llm = get_llm(temperature=0.2)
    strategist, implementer, reviewer_one, delta, optimizer, reviewer_two = _build_agents(
        llm
    )

    t1_strategy = Task(
        description=(
            f"Blueprint the feature request for '{target_file}': {task_description}. "
            "Define feature slices, constraints, acceptance criteria, expected files, and validation approach."
        ),
        agent=strategist,
        expected_output="Feature blueprint with acceptance criteria and validation notes.",
    )

    t2_task = Task(
        description="Implement the feature from the strategy blueprint. Output complete code for affected files.",
        agent=implementer,
        context=[t1_strategy],
        expected_output="Implementation summary and complete code in labeled markdown code blocks.",
    )

    t3_review_one = Task(
        description="Review the implementation against the strategy blueprint.",
        agent=reviewer_one,
        context=[t1_strategy, t2_task],
        expected_output="Prioritized review findings with concrete gaps against the blueprint.",
    )

    t4_delta = Task(
        description=(
            "Retrieve the delta between Reviewer 1 findings and the initial strategy blueprint. "
            "Formulate a test-first plan to fix the delta. For each feature or criterion, delineate "
            "PASS, PARTIAL, and FAIL conditions."
        ),
        agent=delta,
        context=[t1_strategy, t2_task, t3_review_one],
        expected_output="Delta matrix, test plan, and PASS/PARTIAL/FAIL conditions for each feature.",
    )

    t5_optimize = Task(
        description="Close the delta between the implementation and the issue-resolution plan.",
        agent=optimizer,
        context=[t1_strategy, t2_task, t3_review_one, t4_delta],
        expected_output="Optimized implementation summary and complete updated code blocks.",
    )

    t6_review_two = Task(
        description=(
            "Review the optimized implementation against the initial strategy. Mark every feature criterion "
            "as PASS, PARTIAL, or FAIL. If any item is PARTIAL or FAIL, explain what must repeat from Delta. "
            "Always include the latest optimized code blocks and a traceability summary that maps each "
            "initial strategy criterion to its status. "
            "The first line of the response must be exactly one of: OVERALL_STATUS: PASS, "
            "OVERALL_STATUS: PARTIAL, or OVERALL_STATUS: FAIL."
        ),
        agent=reviewer_two,
        context=[t1_strategy, t2_task, t3_review_one, t4_delta, t5_optimize],
        expected_output="OVERALL_STATUS, traceability matrix, remaining delta if any, and latest complete code blocks.",
    )

    crew = Crew(
        agents=[strategist, implementer, reviewer_one, delta, optimizer, reviewer_two],
        tasks=[t1_strategy, t2_task, t3_review_one, t4_delta, t5_optimize, t6_review_two],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff(
        inputs={
            "task": task_description,
            "file": target_file,
            "max_iterations": max_iterations,
        }
    )


def _run_delta_repeat(
    task_description: str,
    target_file: str,
    previous_result: object,
    iteration: int,
):
    llm = get_llm(temperature=0.15)
    _, _, _, delta, optimizer, reviewer_two = _build_agents(llm)
    previous = str(previous_result)

    t1_delta = Task(
        description=(
            f"Repeat Delta iteration {iteration} for '{target_file}' and task '{task_description}'. "
            "Use the previous Reviewer 2 result below as the current source of truth. Rebuild the delta "
            "matrix and test-first plan only for criteria that are PARTIAL or FAIL.\n\n"
            f"Previous result:\n{previous}"
        ),
        agent=delta,
        expected_output="Updated delta matrix and PASS/PARTIAL/FAIL test plan for remaining gaps.",
    )

    t2_optimize = Task(
        description="Optimize the implementation to close only the remaining delta from this iteration.",
        agent=optimizer,
        context=[t1_delta],
        expected_output="Updated implementation summary and complete corrected code blocks.",
    )

    t3_review_two = Task(
        description=(
            "Review the optimized implementation against the initial strategy and remaining delta. "
            "Always include the latest optimized code blocks and a traceability summary that maps each "
            "initial strategy criterion to PASS, PARTIAL, or FAIL. "
            "The first line of the response must be exactly one of: OVERALL_STATUS: PASS, "
            "OVERALL_STATUS: PARTIAL, or OVERALL_STATUS: FAIL."
        ),
        agent=reviewer_two,
        context=[t1_delta, t2_optimize],
        expected_output="OVERALL_STATUS, traceability matrix, remaining delta if any, and latest complete code blocks.",
    )

    crew = Crew(
        agents=[delta, optimizer, reviewer_two],
        tasks=[t1_delta, t2_optimize, t3_review_two],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff(
        inputs={"task": task_description, "file": target_file, "iteration": iteration}
    )


def run_tauri_task_crew(task_description: str, target_file: str, max_iterations: int = 2):
    max_iterations = max(1, max_iterations)
    result = _run_initial_loop(task_description, target_file, max_iterations)

    for iteration in range(2, max_iterations + 1):
        if _review_passed(result):
            break
        result = _run_delta_repeat(task_description, target_file, result, iteration)

    return result
