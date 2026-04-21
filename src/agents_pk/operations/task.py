import re

from crewai import Agent, Crew, Process, Task

from ..utils.llm import get_llm

SPEC_SCHEMA = """
{
  "feature_id": "stable-kebab-case-id",
  "summary": "one sentence",
  "target_file": "path supplied by CLI",
  "assumptions": ["explicit assumption"],
  "non_goals": ["out-of-scope item"],
  "affected_files": [
    {
      "path": "relative/path",
      "reason": "why this file may change"
    }
  ],
  "acceptance_criteria": [
    {
      "id": "AC-001",
      "description": "observable requirement",
      "priority": "must|should|could",
      "verification": {
        "type": "unit_test|integration_test|lint|typecheck|sandbox_execution|manual_review",
        "command": "exact command when applicable",
        "expected_result": "quantifiable expected result"
      }
    }
  ],
  "edge_cases": [
    {
      "id": "EC-001",
      "description": "edge case",
      "expected_behavior": "observable expected behavior",
      "verification": {
        "type": "unit_test|integration_test|lint|typecheck|sandbox_execution|manual_review",
        "command": "exact command when applicable",
        "expected_result": "quantifiable expected result"
      }
    }
  ]
}
"""


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
        goal="Blueprint the requested feature as a structured JSON spec before implementation starts",
        backstory="Senior product-minded engineer who turns feature requests into precise, testable, diffable specifications.",
        llm=llm,
        verbose=True,
    )

    implementer = Agent(
        role="Task Implementer",
        goal="Implement the feature according to the structured strategy spec",
        backstory="Pragmatic software engineer who produces complete, idiomatic code with minimal unrelated churn.",
        llm=llm,
        verbose=True,
    )

    reviewer_one = Agent(
        role="Reviewer 1",
        goal="Review the implementation against the initial structured strategy spec",
        backstory="Strict reviewer focused on correctness, completeness, regressions, and missed requirements.",
        llm=llm,
        verbose=True,
    )

    delta = Agent(
        role="Delta Analyst",
        goal="Identify a machine-comparable delta and negotiate concrete verification conditions",
        backstory="Test-focused engineer who translates gaps into quantified PASS, PARTIAL, and FAIL validation conditions.",
        llm=llm,
        verbose=True,
    )

    optimizer = Agent(
        role="Optimizer",
        goal="Close the delta and produce evidence-oriented verification instructions",
        backstory="Senior engineer who fixes only the remaining gaps and preserves already-correct behavior with testable proof points.",
        llm=llm,
        verbose=True,
    )

    reviewer_two = Agent(
        role="Reviewer 2",
        goal="Review the optimized implementation against every feature in the structured spec",
        backstory="Final reviewer who verifies each acceptance criterion and decides whether the loop can stop.",
        llm=llm,
        verbose=True,
    )

    return strategist, implementer, reviewer_one, delta, optimizer, reviewer_two


def _run_initial_loop(task_description: str, target_file: str, max_iterations: int):
    llm = get_llm(temperature=0.2)
    strategist, implementer, reviewer_one, delta, optimizer, reviewer_two = (
        _build_agents(llm)
    )

    t1_strategy = Task(
        description=(
            f"Blueprint the feature request for '{target_file}': {task_description}. "
            "Output a structured JSON spec first, followed by any concise notes. The JSON must be valid, "
            "must use stable IDs, and must include acceptance criteria, edge cases, non-goals, affected files, "
            "and verification commands or procedures that later agents can literally diff against. "
            f"Use this exact top-level shape:\n{SPEC_SCHEMA}"
        ),
        agent=strategist,
        expected_output="A valid JSON spec matching the requested schema, followed by concise implementation notes.",
    )

    t2_task = Task(
        description=(
            "Implement the feature from the structured strategy spec. Preserve the acceptance criteria IDs "
            "in the implementation summary so reviewers can trace each code change back to the spec. "
            "Output complete code for affected files."
        ),
        agent=implementer,
        context=[t1_strategy],
        expected_output="Implementation summary mapped to spec IDs and complete code in labeled markdown code blocks.",
    )

    t3_review_one = Task(
        description=(
            "Review the implementation against the structured strategy spec. Diff against acceptance criteria, "
            "edge cases, non-goals, and affected-file expectations by ID."
        ),
        agent=reviewer_one,
        context=[t1_strategy, t2_task],
        expected_output="Prioritized review findings mapped to spec IDs, including any missing tests or verification gaps.",
    )

    t4_delta = Task(
        description=(
            "Retrieve the delta between Reviewer 1 findings, the implementation, and the initial JSON strategy spec. "
            "Formulate a verification-first plan to fix the delta. For each acceptance criterion and edge case, "
            "delineate PASS, PARTIAL, and FAIL conditions with real quantifiables. Include at least one concrete "
            "verification method when applicable: unit tests, integration tests, linter run, typecheck, build, "
            "or sandbox execution. For each verification item, specify command, fixture/input, expected output, "
            "exit code, assertion count, coverage target, or other measurable threshold. If a real executable "
            "verification is impossible from context, state why and provide the closest manual-review evidence."
        ),
        agent=delta,
        context=[t1_strategy, t2_task, t3_review_one],
        expected_output="Delta matrix mapped to spec IDs plus a quantified verification plan with PASS/PARTIAL/FAIL conditions.",
    )

    t5_optimize = Task(
        description=(
            "Close the delta between the implementation and the issue-resolution plan. Negotiate the verification "
            "plan by either adding or updating concrete tests/checks, or explaining exactly which existing checks "
            "prove the fix. Include runnable commands, expected exit codes, expected assertions/results, and any "
            "sandbox execution assumptions alongside the optimized code."
        ),
        agent=optimizer,
        context=[t1_strategy, t2_task, t3_review_one, t4_delta],
        expected_output="Optimized implementation, complete updated code blocks, and verification evidence/commands mapped to spec IDs.",
    )

    t6_review_two = Task(
        description=(
            "Review the optimized implementation against the initial JSON strategy spec. Mark every feature criterion "
            "as PASS, PARTIAL, or FAIL. If any item is PARTIAL or FAIL, explain what must repeat from Delta. "
            "Always include the latest optimized code blocks and a traceability summary that maps each "
            "initial strategy criterion to its status. Verify that the Delta and Optimizer supplied real, "
            "quantified verification items such as unit tests, lint/typecheck/build commands, or sandbox runs. "
            "The first line of the response must be exactly one of: OVERALL_STATUS: PASS, "
            "OVERALL_STATUS: PARTIAL, or OVERALL_STATUS: FAIL."
        ),
        agent=reviewer_two,
        context=[t1_strategy, t2_task, t3_review_one, t4_delta, t5_optimize],
        expected_output="OVERALL_STATUS, traceability matrix, verification evidence review, remaining delta if any, and latest complete code blocks.",
    )

    crew = Crew(
        agents=[strategist, implementer, reviewer_one, delta, optimizer, reviewer_two],
        tasks=[
            t1_strategy,
            t2_task,
            t3_review_one,
            t4_delta,
            t5_optimize,
            t6_review_two,
        ],
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
            "matrix and verification-first plan only for criteria that are PARTIAL or FAIL. Preserve the original "
            "spec IDs. Negotiate real quantifiables for each remaining gap: tests, lint/typecheck/build commands, "
            "sandbox execution, expected exit codes, assertion counts, fixtures, expected output, or measurable "
            "manual evidence when executable checks are impossible.\n\n"
            f"Previous result:\n{previous}"
        ),
        agent=delta,
        expected_output="Updated delta matrix and quantified PASS/PARTIAL/FAIL verification plan for remaining gaps.",
    )

    t2_optimize = Task(
        description=(
            "Optimize the implementation to close only the remaining delta from this iteration. Include concrete "
            "verification artifacts: new/updated test code where appropriate, exact commands to run, expected "
            "exit codes/results, and any sandbox constraints."
        ),
        agent=optimizer,
        context=[t1_delta],
        expected_output="Updated implementation summary, complete corrected code blocks, and verification evidence mapped to spec IDs.",
    )

    t3_review_two = Task(
        description=(
            "Review the optimized implementation against the initial strategy and remaining delta. "
            "Always include the latest optimized code blocks and a traceability summary that maps each "
            "initial strategy criterion to PASS, PARTIAL, or FAIL. Verify the quantifiable evidence from Delta "
            "and Optimizer, including tests/check commands and expected results. "
            "The first line of the response must be exactly one of: OVERALL_STATUS: PASS, "
            "OVERALL_STATUS: PARTIAL, or OVERALL_STATUS: FAIL."
        ),
        agent=reviewer_two,
        context=[t1_delta, t2_optimize],
        expected_output="OVERALL_STATUS, traceability matrix, verification evidence review, remaining delta if any, and latest complete code blocks.",
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


def run_tauri_task_crew(
    task_description: str, target_file: str, max_iterations: int = 2
):
    max_iterations = max(1, max_iterations)
    result = _run_initial_loop(task_description, target_file, max_iterations)

    for iteration in range(2, max_iterations + 1):
        if _review_passed(result):
            break
        result = _run_delta_repeat(task_description, target_file, result, iteration)

    return result
