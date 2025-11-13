"""Execution planning for workflow graphs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from collections import defaultdict, deque


@dataclass
class ExecutionPlanStage:
    """Represents a single execution stage."""

    index: int
    nodes: List[str]
    parallelizable: bool = False


@dataclass
class ExecutionPlanResult:
    """Execution planner output."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    ordered_nodes: List[str] = field(default_factory=list)
    stages: List[ExecutionPlanStage] = field(default_factory=list)
    critical_path_length: int = 0


class ExecutionPlanner:
    """Compute deterministic execution plans for workflows."""

    def plan(
        self,
        nodes: List[Dict[str, str]],
        edges: List[Dict[str, str]],
    ) -> ExecutionPlanResult:
        errors: List[str] = []
        warnings: List[str] = []

        node_ids = [node["id"] for node in nodes]
        if len(node_ids) != len(set(node_ids)):
            warnings.append("Duplicate node identifiers detected during planning.")

        adjacency: Dict[str, List[str]] = {node_id: [] for node_id in node_ids}
        indegree: Dict[str, int] = {node_id: 0 for node_id in node_ids}

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source not in adjacency or target not in indegree:
                errors.append(
                    f"Execution planner encountered edge with unknown nodes: {source}->{target}"
                )
                continue
            adjacency[source].append(target)
            indegree[target] += 1

        ordered: List[str] = []
        stages: List[ExecutionPlanStage] = []
        ready = deque(sorted([node_id for node_id, degree in indegree.items() if degree == 0]))
        stage_index = 0

        while ready:
            current_stage = list(ready)
            ready.clear()
            current_stage.sort()
            stages.append(
                ExecutionPlanStage(
                    index=stage_index,
                    nodes=current_stage.copy(),
                    parallelizable=len(current_stage) > 1,
                )
            )
            stage_index += 1

            for node_id in current_stage:
                ordered.append(node_id)
                for neighbour in adjacency[node_id]:
                    indegree[neighbour] -= 1
                    if indegree[neighbour] == 0:
                        ready.append(neighbour)
            ready = deque(sorted(ready))

        if len(ordered) != len(node_ids):
            errors.append("Workflow contains circular dependencies.")

        critical_path = self._critical_path_length(adjacency, nodes, edges, errors)

        return ExecutionPlanResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            ordered_nodes=ordered,
            stages=stages,
            critical_path_length=critical_path,
        )

    def _critical_path_length(
        self,
        adjacency: Dict[str, List[str]],
        nodes: List[Dict[str, str]],
        edges: List[Dict[str, str]],
        errors: List[str],
    ) -> int:
        """Approximate the critical path length for the DAG."""
        if errors:
            return 0
        indegree = {node["id"]: 0 for node in nodes}
        for edge in edges:
            if edge.get("source") in indegree and edge.get("target") in indegree:
                indegree[edge["target"]] += 1
        ready = deque([node_id for node_id, deg in indegree.items() if deg == 0])
        distance = {node_id: 1 for node_id in indegree}
        while ready:
            node_id = ready.popleft()
            for neighbour in adjacency[node_id]:
                distance[neighbour] = max(distance[neighbour], distance[node_id] + 1)
                indegree[neighbour] -= 1
                if indegree[neighbour] == 0:
                    ready.append(neighbour)
        return max(distance.values() or [0])


__all__ = ["ExecutionPlanner", "ExecutionPlanResult", "ExecutionPlanStage"]
