"""Compatibility shim for the renamed script.

If other tools or docs still call `tk_file_organizer.py`, this small shim
imports and runs the canonical entrypoint in `DupeRangerAi.py` with a
fallback to the legacy `AiDupeRanger.py` to preserve compatibility.
"""

from importlib import import_module

try:
    # Prefer the canonical entrypoint; fallback to the historical module name
    try:
        mod = import_module("DupeRangerAi")
    except ModuleNotFoundError:
        mod = import_module("AiDupeRanger")
    main = getattr(mod, "main")
except Exception as exc:  # pragma: no cover - fallback reporting
    raise SystemExit(f"Failed to load AiDupeRanger module: {exc}")


if __name__ == "__main__":
    main()
