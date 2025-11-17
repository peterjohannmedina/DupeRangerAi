"""Compatibility shim for the renamed script.

This file imports and runs the canonical entrypoint in `DupeRangerAi.py`.
Legacy variants were removed from the public repo to avoid confusion.
"""

from importlib import import_module

try:
    # Prefer the canonical entrypoint; fallback to the historical module name
    try:
        mod = import_module("DupeRangerAi")
    except ModuleNotFoundError:
        # Canonical script not found; don't fall back to legacy names to avoid
        # silent imports of removed variants. Explicitly inform the caller.
        raise
    main = getattr(mod, "main")
except Exception as exc:  # pragma: no cover - fallback reporting
    raise SystemExit(f"Failed to load DupeRangerAi module: {exc}")


if __name__ == "__main__":
    main()
