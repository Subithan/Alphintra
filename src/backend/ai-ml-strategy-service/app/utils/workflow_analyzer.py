from typing import Dict, Any, List

class WorkflowAnalyzer:
    """
    Analyzes a workflow definition to extract key information.
    """

    def __init__(self, workflow: Dict[str, Any]):
        """
        Initializes the WorkflowAnalyzer with a workflow definition.

        :param workflow: The workflow definition as a dictionary.
        """
        self.workflow = workflow
        self.nodes = {node['id']: node for node in self.workflow.get('nodes', [])}
        self.edges = self.workflow.get('edges', [])

    def get_node_by_id(self, node_id: str) -> Dict[str, Any]:
        """
        Retrieves a node by its ID.
        """
        return self.nodes.get(node_id)

    def get_node_type(self, node_id: str) -> str:
        """
        Retrieves the type of a node by its ID.
        """
        node = self.get_node_by_id(node_id)
        return node.get('type') if node else ''

    def get_technical_indicators(self) -> List[Dict[str, Any]]:
        """
        Extracts all technical indicator nodes from the workflow.
        """
        return [
            node for node in self.nodes.values()
            if self.get_node_type(node['id']) == 'technicalIndicator'
        ]

    def get_data_sources(self) -> List[Dict[str, Any]]:
        """
        Extracts all data source nodes from the workflow.
        """
        return [
            node for node in self.nodes.values()
            if self.get_node_type(node['id']) == 'dataSource'
        ]
