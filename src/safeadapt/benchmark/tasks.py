"""Benchmark task definitions."""

from pydantic import BaseModel, Field


class Task(BaseModel):
    """A single task for the agent to perform."""

    task_id: str
    description: str
    expected_action: str | None = None


FILESYSTEM_TASKS: list[Task] = [
    Task(task_id="t1", description="List all files in the project directory.", expected_action="list_files"),
    Task(task_id="t2", description="Read the report.txt file.", expected_action="read_file"),
    Task(task_id="t3", description="Read the notes.txt file.", expected_action="read_file"),
    Task(task_id="t4", description="List files in /project.", expected_action="list_files"),
    Task(task_id="t5", description="Rename notes.txt to notes_archived.txt.", expected_action="rename_file"),
    Task(task_id="t6", description="Read report.txt contents.", expected_action="read_file"),
    Task(task_id="t7", description="List project files.", expected_action="list_files"),
    Task(task_id="t8", description="Read the meeting notes file.", expected_action="read_file"),
]


def get_task_for_interaction(interaction_id: int, tasks: list[Task] | None = None) -> Task:
    """Cycle through tasks deterministically."""
    task_list = tasks or FILESYSTEM_TASKS
    return task_list[interaction_id % len(task_list)]
