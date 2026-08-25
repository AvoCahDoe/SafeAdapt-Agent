"""Tool registry for environment actions."""

from typing import Callable

from safeadapt.schemas.action import AgentAction


class ToolRegistry:
    """Registry mapping tool names to handler callables."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable[[AgentAction], object]] = {}

    def register(self, name: str, handler: Callable[[AgentAction], object]) -> None:
        """Register a tool handler."""
        self._tools[name] = handler

    def has(self, name: str) -> bool:
        """Return True if the tool is registered."""
        return name in self._tools

    def execute(self, action: AgentAction) -> object:
        """Execute a registered tool."""
        if action.action not in self._tools:
            raise KeyError(f"Unknown tool: {action.action}")
        return self._tools[action.action](action)

    def list_tools(self) -> list[str]:
        """Return registered tool names."""
        return sorted(self._tools.keys())
