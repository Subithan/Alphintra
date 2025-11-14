"""No-code service tests package utilities."""

from __future__ import annotations

from pathlib import Path


def _locate_service_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "cloudbuild.yaml").exists():
            return parent
    raise RuntimeError("Unable to locate service root with cloudbuild.yaml marker")


SERVICE_ROOT = _locate_service_root()
PROJECT_ROOT = SERVICE_ROOT  # Retained for backward compatibility

__all__ = ["SERVICE_ROOT", "PROJECT_ROOT"]
