"""Lightweight telemetry helpers for compiler instrumentation."""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional


class TelemetryRecorder:
    """Record compiler telemetry to structured logs (or a file sink)."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("telemetry")
        self.logger.setLevel(logging.INFO)
        self._lock = threading.Lock()
        self._file_handler: Optional[logging.Handler] = None
        self.configure(os.getenv("TELEMETRY_FILE"))

    def configure(self, file_path: Optional[str]) -> None:
        with self._lock:
            if self._file_handler:
                self.logger.removeHandler(self._file_handler)
                self._file_handler.close()
                self._file_handler = None
            if file_path:
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                handler = logging.FileHandler(file_path)
                handler.setFormatter(logging.Formatter("%(message)s"))
                self.logger.addHandler(handler)
                self._file_handler = handler

    def record(self, event_type: str, payload: Dict[str, Any]) -> None:
        entry = {"event": event_type, **payload}
        try:
            self.logger.info(json.dumps(entry, default=str))
        except TypeError:
            sanitized = {k: str(v) for k, v in entry.items()}
            self.logger.info(json.dumps(sanitized))

    def record_compilation(self, payload: Dict[str, Any]) -> None:
        self.record("compiler_run", payload)

    def flush(self) -> None:
        with self._lock:
            if self._file_handler and hasattr(self._file_handler, "flush"):
                self._file_handler.flush()


telemetry_recorder = TelemetryRecorder()
if os.getenv("TELEMETRY_FILE"):
    telemetry_recorder.configure(os.getenv("TELEMETRY_FILE"))

__all__ = ["telemetry_recorder", "TelemetryRecorder"]
