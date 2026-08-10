"""Shared helpers for Quality Engine tests.

Building a QualityEngine normally runs real tool discovery and loads
pyproject.toml, which makes tests slow and platform dependent. These helpers
back the engine with stub tools instead, so tests exercise engine logic rather
than whichever linters happen to be installed.
"""

from typing import Any

from codeflow_engine.actions.quality_engine.engine import QualityEngine
from codeflow_engine.actions.quality_engine.tools.registry import ToolRegistry


# The engine's mode->tool mapping is hard-coded to real tool names, so stubs have
# to borrow one for the engine to select them.
STUB_TOOL_NAME = "ruff"


def make_stub_tool_class(name: str) -> type:
    """Build a tool class the registry can instantiate and name."""

    class StubTool:
        def __init__(self) -> None:
            self.name = name
            self.category = "general"
            self.description = f"Stub {name} tool"

    return StubTool


def make_engine(
    tool_names: tuple[str, ...] = (STUB_TOOL_NAME,),
    config: Any | None = None,
) -> QualityEngine:
    """Create a QualityEngine whose registry holds only the named stub tools."""
    registry = ToolRegistry()
    for name in tool_names:
        registry.register(make_stub_tool_class(name))

    return QualityEngine(
        tool_registry=registry,
        config=config if config is not None else {"tools": {}},
        skip_windows_check=True,
    )
