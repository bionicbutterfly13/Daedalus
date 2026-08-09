"""Process-runtime state for EvoScientist.

Small, module-level runtime values that live for the lifetime of the process
and are read/written across the agent, its middleware, and the CLI command
layer — analogous to the stream cancel-scope in ``stream/display.py``. For
example, the interaction-mode (``initiative``) level.
"""

# Async bridge runtime (upstream 8b1451c shipped this as a sibling module
# ``EvoScientist/runtime.py``; this fork already owns the ``runtime`` package
# for initiative/steer state, and a package shadows a same-named module, so
# the module lives here instead and its public API is re-exported).
from .async_runtime import (
    AsyncFactory,
    AsyncRuntime,
    AsyncRuntimeClosedError,
    AsyncRuntimeError,
    RuntimeHandle,
)

__all__ = [
    "AsyncFactory",
    "AsyncRuntime",
    "AsyncRuntimeClosedError",
    "AsyncRuntimeError",
    "RuntimeHandle",
]
