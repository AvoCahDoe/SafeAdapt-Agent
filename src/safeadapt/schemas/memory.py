"""Agent memory schemas."""

from enum import Enum

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Categories of persistent agent memory items."""

    USER_PREFERENCE = "user_preference"
    TASK_FACT = "task_fact"
    ENVIRONMENT_FACT = "environment_fact"
    PAST_ACTION = "past_action"
    FEEDBACK = "feedback"
    INSTRUCTION = "instruction"


class MemoryItem(BaseModel):
    """A single item in agent persistent memory."""

    id: str
    content: str
    source: str
    timestamp: int
    importance: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    type: MemoryType
