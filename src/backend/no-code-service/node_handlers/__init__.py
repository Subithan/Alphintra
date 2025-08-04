"""Node handler implementations and registry."""

from .base import NodeHandler
from .data_source import DataSourceHandler
from .custom_dataset import CustomDatasetHandler
from .technical_indicator import TechnicalIndicatorHandler
from .condition import ConditionHandler
from .logic import LogicHandler
from .action import ActionHandler
from .risk import RiskHandler
from .output import OutputHandler
from .fallback import FallbackHandler

# Instantiate handlers and expose a simple dictionary based registry.  The
# :class:`Generator` uses this to look up the correct handler for each node.
HANDLER_REGISTRY = {
    handler.node_type: handler
    for handler in [
        DataSourceHandler(),
        CustomDatasetHandler(),
        TechnicalIndicatorHandler(),
        ConditionHandler(),
        LogicHandler(),
        ActionHandler(),
        RiskHandler(),
        OutputHandler(),
    ]
}

# Single instance used when no specific handler is registered for a node type.
FALLBACK_HANDLER = FallbackHandler()

__all__ = [
    "NodeHandler",
    "HANDLER_REGISTRY",
    "FALLBACK_HANDLER",
    "DataSourceHandler",
    "CustomDatasetHandler",
    "TechnicalIndicatorHandler",
    "ConditionHandler",
    "LogicHandler",
    "ActionHandler",
    "RiskHandler",
    "OutputHandler",
    "FallbackHandler",
]
