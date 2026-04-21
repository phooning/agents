from crewai import Agent, Crew, Process, Task

from ..utils.llm import get_llm


def run_refactor_crew(task_description: str, target_file: str):
    llm = get_llm(temperature=0.2)

    analyst = Agent(
        role="Context Analyst",
        goal="Deeply understand the file in the context of the project technical stack.",
        backstory="Expert at analyzing code projects: commands, invokes, bridges, and build flow.",
        llm=llm,
        verbose=True,
    )

    architect = Agent(
        role="Software Architect",
        goal="Design an optimal refactoring strategy that respects constraints",
        backstory="Senior specialized architect: safe interop and performance.",
        llm=llm,
        verbose=True,
    )

    implementer = Agent(
        role="Senior Software Engineer",
        goal="Implement the refactoring cleanly across the stack",
        backstory="Full-stack developer writing idiomatic clean and modern code.",
        llm=llm,
        verbose=True,
    )

    reviewer = Agent(
        role="Code Reviewer",
        goal="Review changes for correctness, safety, and specific issues",
        backstory="Strict senior reviewer focused on command safety and type consistency.",
        llm=llm,
        verbose=True,
    )

    t1_analysis = Task(
        description=f"Analyze '{target_file}'. Describe logic, invokes/commands, and improvement opportunities.",
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
        description="Review for best practices and type consistency. Approve or suggest fixes.",
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
