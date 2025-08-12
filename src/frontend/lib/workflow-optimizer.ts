import { Node, Edge } from 'reactflow';

export interface OptimizationSuggestion {
  id:string;
  type:'performance' | 'best_practice' | 'simplification';
  message:string;
  nodeIds:string[];
  priority:'high' | 'medium' | 'low';
  action?:{
    type:'CONSOLIDATE_NODES';
    payload:{
      nodesToRemove:string[];
      nodeToKeep:string;
    }
  };
}

export class WorkflowOptimizer {
  private nodes: Node[];
  private edges: Edge[];

  constructor(nodes: Node[], edges: Edge[]) {
    this.nodes = nodes;
    this.edges = edges;
  }

  public generateOptimizations(): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];

    suggestions.push(...this.suggestIndicatorConsolidation());
    suggestions.push(...this.suggestNodeReordering());
    suggestions.push(...this.suggestCaching());
    suggestions.push(...this.suggestParallelExecution());
    suggestions.push(...this.suggestAlternativeIndicators());

    return suggestions;
  }

  private suggestIndicatorConsolidation(): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];
    const indicatorNodes = this.nodes.filter(n => n.type === 'technicalIndicator');
    const indicatorMap = new Map<string, Node[]>();

    // Group indicators by type and parameters
    for (const node of indicatorNodes) {
      const key = `${node.data.parameters.indicator}-${node.data.parameters.period}`;
      if (!indicatorMap.has(key)) {
        indicatorMap.set(key, []);
      }
      indicatorMap.get(key)!.push(node);
    }

    // Find groups with more than one indicator
    for (const [key, nodes] of indicatorMap.entries()) {
      if (nodes.length > 1) {
        const nodeToKeep = nodes[0];
        const nodesToRemove = nodes.slice(1);
        suggestions.push({
          id: `consolidate-${key}`,
          type: 'simplification',
          message: `Consolidate ${nodes.length} identical ${key} indicators into one.`,
          nodeIds: nodes.map(n => n.id),
          priority: 'medium',
          action: {
            type: 'CONSOLIDATE_NODES',
            payload: {
              nodesToRemove: nodesToRemove.map(n => n.id),
              nodeToKeep: nodeToKeep.id,
            }
          }
        });
      }
    }

    return suggestions;
  }

  private suggestNodeReordering(): OptimizationSuggestion[] {
    // This is a complex UI/visual task, returning empty for now.
    return [];
  }

  private suggestCaching(): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];
    const expensiveNodes = this.nodes.filter(node => {
      if (node.type === 'technicalIndicator') {
        const period = node.data.parameters?.period || 0;
        return period > 200;
      }
      return false;
    });

    for (const node of expensiveNodes) {
      suggestions.push({
        id: `cache-${node.id}`,
        type: 'performance',
        message: `Consider caching the result of ${node.data.label} (period: ${node.data.parameters.period}) as it is computationally expensive.`,
        nodeIds: [node.id],
        priority: 'low',
      });
    }

    return suggestions;
  }

  private suggestParallelExecution(): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];
    const sources = this.nodes.filter(n => this.edges.every(e => e.target !== n.id));

    if (sources.length > 1) {
        const sourceLabels = sources.map(n => n.data.label);
        suggestions.push({
            id: 'parallel-execution',
            type: 'performance',
            message: `Multiple independent execution paths detected, starting from: ${sourceLabels.join(', ')}. These paths can be executed in parallel.`,
            nodeIds: sources.map(n => n.id),
            priority: 'medium'
        });
    }

    return suggestions;
  }

  private suggestAlternativeIndicators(): OptimizationSuggestion[] {
    // This requires pattern detection, which is complex. Returning empty for now.
    return [];
  }
}

export function getWorkflowOptimizations(nodes: Node[], edges: Edge[]): OptimizationSuggestion[] {
  const optimizer = new WorkflowOptimizer(nodes, edges);
  return optimizer.generateOptimizations();
}
