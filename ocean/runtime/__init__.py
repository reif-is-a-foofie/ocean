"""Autonomous runtime: product state, user inbox, and single-cycle execution."""

from .cycle import CycleResult, run_cycle
from .inbox import ingest as ingest_message
from .state import ProductState
from .status import format_status_text

__all__ = [
    "CycleResult",
    "ProductState",
    "format_status_text",
    "ingest_message",
    "run_cycle",
]
