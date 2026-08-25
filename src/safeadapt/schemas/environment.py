"""Environment and simulation result schemas."""

from typing import Any

from pydantic import BaseModel, Field


class VirtualFile(BaseModel):
    """A file in the simulated filesystem."""

    path: str
    content: str = ""
    private: bool = False
    protected: bool = False
    important: bool = False


class ActionResult(BaseModel):
    """Result of executing an action in an environment."""

    success: bool
    output: Any = None
    constraint_violations: list[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    error: str | None = None
