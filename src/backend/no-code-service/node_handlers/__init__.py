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

__all__ = [
    "NodeHandler",
    "HANDLER_REGISTRY",
    "DataSourceHandler",
    "CustomDatasetHandler",
    "TechnicalIndicatorHandler",
    "ConditionHandler",
    "LogicHandler",
    "ActionHandler",
    "RiskHandler",
    "OutputHandler",
]
