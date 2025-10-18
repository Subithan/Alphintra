"""
Placeholder utilities for future strategy experiments.

This module intentionally keeps the functions simple so that we can
expand on them later without affecting current behaviour.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DummyStrategyConfig:
    """Static configuration bundle used as a harmless placeholder."""

    name: str
    version: str
    parameters: Dict[str, float]


DEFAULT_CONFIGS: List[DummyStrategyConfig] = [
    DummyStrategyConfig(name="alpha-prototype", version="0.0.1", parameters={"threshold": 0.0}),
    DummyStrategyConfig(name="beta-experiment", version="0.0.1", parameters={"threshold": 0.0}),
]


def get_placeholder_config(strategy_name: str) -> DummyStrategyConfig:
    """
    Return a dummy strategy configuration if available.

    The function is intentionally side-effect free so it does not impact
    runtime behaviour; it merely looks up an in-memory list.
    """
    logger.debug("get_placeholder_config called with strategy_name=%s", strategy_name)
    for config in DEFAULT_CONFIGS:
        if config.name == strategy_name:
            return config
    return DEFAULT_CONFIGS[0]


def emit_placeholder_metric(metric_name: str) -> None:
    """
    Emit a debug log for a fake metric to keep the project structured.

    The metric is not sent anywhere; logging keeps the code inert while
    giving us a seam for future development.
    """
    logger.debug("emit_placeholder_metric called for metric=%s", metric_name)

