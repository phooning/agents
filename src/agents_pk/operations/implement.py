from crewai import Agent, Crew, Process, Task

from ..utils.llm import get_llm


def run_implement_crew(task_description: str, file: str):
    llm = get_llm(temperature=0.3)

    analyst = Agent(
        role="Requirements Analyst",
        goal="Map feature requests to the existing codebase",
        backstory="Expert at breaking down features into commands and components.",
        llm=llm,
        verbose=True,
    )

    architect = Agent(
        role="Solution Architect",
        goal="Design a consistent implementation plan across Rust and TypeScript",
        backstory="Senior architect ensuring safe interop and minimizing breaking changes.",
        llm=llm,
        verbose=True,
    )

    implementer = Agent(
        role="Senior Software Engineer",
        goal="Implement the feature across necessary files",
        backstory="Pragmatic developer producing clean and modern code.",
        llm=llm,
        verbose=True,
    )

    reviewer = Agent(
        role="Implementation Reviewer",
        goal="Validate implementation for safety and best practices",
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
