import { Node, Edge } from 'reactflow';

export interface OptimizationSuggestion {
  id: string;
  type: 'performance' | 'architecture' | 'risk' | 'maintainability';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  impact: string;
  suggestion: string;
  nodeIds?: string[];
  edgeIds?: string[];
  estimatedImpact: {
    performance?: number; // percentage improvement
    reliability?: number;
    maintainability?: number;
  };
}

export interface WorkflowScore {
  overall: number; // 0-100
  performance: number; // 0-100
  architecture: number; // 0-100
  risk: number; // 0-100
  maintainability: number; // 0-100
  breakdown: {
    nodeComplexity: number;
    connectionEfficiency: number;
    riskManagement: number;
    parameterOptimization: number;
    resourceUsage: number;
  };
}

export interface WorkflowHealth {
  status: 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
  score: WorkflowScore;
  suggestions: OptimizationSuggestion[];
  metrics: {
    nodeCount: number;
    edgeCount: number;
    depth: number;
    fanOut: number;
    cyclomaticComplexity: number;
    technicalDebt: number;
  };
}

export class WorkflowAnalyzer {
  private nodes: Node[];
  private edges: Edge[];

  constructor(nodes: Node[], edges: Edge[]) {
    this.nodes = nodes;
    this.edges = edges;
  }

  /**
   * Comprehensive workflow analysis
   */
  analyzeWorkflow(): WorkflowHealth {
    const metrics = this.calculateMetrics();
    const score = this.calculateScore(metrics);
    const suggestions = this.generateOptimizationSuggestions();
    const status = this.determineHealthStatus(score.overall);

    return {
      status,
      score,
      suggestions,
      metrics
    };
  }

  private calculateMetrics() {
    const nodeCount = this.nodes.length;
    const edgeCount = this.edges.length;
    const depth = this.calculateWorkflowDepth();
    const fanOut = this.calculateAverageFanOut();
    const cyclomaticComplexity = this.calculateCyclomaticComplexity();
    const technicalDebt = this.calculateTechnicalDebt();

    return {
      nodeCount,
      edgeCount,
      depth,
      fanOut,
      cyclomaticComplexity,
      technicalDebt
    };
  }

  private calculateWorkflowDepth(): number {
    if (this.nodes.length === 0) return 0;

    // Find root nodes (nodes with no incoming edges)
    const incomingCount = new Map<string, number>();
    this.nodes.forEach(node => incomingCount.set(node.id, 0));
    this.edges.forEach(edge => {
      incomingCount.set(edge.target, (incomingCount.get(edge.target) || 0) + 1);
    });

    const rootNodes = this.nodes.filter(node => incomingCount.get(node.id) === 0);
    if (rootNodes.length === 0) return 0;

    // Calculate maximum depth using BFS
    let maxDepth = 0;
    const adjList = this.buildAdjacencyList();

    for (const root of rootNodes) {
      const depth = this.bfsMaxDepth(root.id, adjList);
      maxDepth = Math.max(maxDepth, depth);
    }

    return maxDepth;
  }

  private calculateAverageFanOut(): number {
    if (this.nodes.length === 0) return 0;

    const outgoingCount = new Map<string, number>();
    this.nodes.forEach(node => outgoingCount.set(node.id, 0));
    this.edges.forEach(edge => {
      outgoingCount.set(edge.source, (outgoingCount.get(edge.source) || 0) + 1);
    });

    const totalFanOut = Array.from(outgoingCount.values()).reduce((sum, count) => sum + count, 0);
    return totalFanOut / this.nodes.length;
  }

  private calculateCyclomaticComplexity(): number {
    // Cyclomatic complexity = E - N + 2P
    // E = edges, N = nodes, P = connected components
    const connectedComponents = this.countConnectedComponents();
    return Math.max(1, this.edges.length - this.nodes.length + 2 * connectedComponents);
  }

  private calculateTechnicalDebt(): number {
    let debt = 0;

    // Check for anti-patterns
    debt += this.countIsolatedNodes() * 10;
    debt += this.countDuplicateLogic() * 15;
    debt += this.countMissingRiskManagement() * 20;
    debt += this.countSuboptimalConnections() * 5;

    return Math.min(100, debt);
  }

  private calculateScore(metrics: any): WorkflowScore {
    const nodeComplexity = this.scoreNodeComplexity(metrics.nodeCount, metrics.cyclomaticComplexity);
    const connectionEfficiency = this.scoreConnectionEfficiency(metrics.fanOut, metrics.edgeCount);
    const riskManagement = this.scoreRiskManagement();
    const parameterOptimization = this.scoreParameterOptimization();
    const resourceUsage = this.scoreResourceUsage(metrics.nodeCount, metrics.depth);

    const performance = Math.round((nodeComplexity + connectionEfficiency + resourceUsage) / 3);
    const architecture = Math.round((connectionEfficiency + nodeComplexity) / 2);
    const risk = riskManagement;
    const maintainability = Math.round((parameterOptimization + (100 - metrics.technicalDebt)) / 2);

    const overall = Math.round((performance + architecture + risk + maintainability) / 4);

    return {
      overall,
      performance,
      architecture,
      risk,
      maintainability,
      breakdown: {
        nodeComplexity,
        connectionEfficiency,
        riskManagement,
        parameterOptimization,
        resourceUsage
      }
    };
  }

  private scoreNodeComplexity(nodeCount: number, complexity: number): number {
    // Optimal node count: 5-15 nodes
    const nodeScore = nodeCount <= 15 ? Math.max(0, 100 - Math.abs(nodeCount - 10) * 5) : 100 - nodeCount * 2;
    
    // Complexity penalty
    const complexityScore = Math.max(0, 100 - complexity * 3);
    
    return Math.round((nodeScore + complexityScore) / 2);
  }

  private scoreConnectionEfficiency(fanOut: number, edgeCount: number): number {
    // Optimal fan-out: 1.5-2.5
    const fanOutScore = fanOut >= 1.5 && fanOut <= 2.5 ? 100 : 100 - Math.abs(fanOut - 2) * 20;
    
    // Connection density
    const maxPossibleEdges = this.nodes.length * (this.nodes.length - 1);
    const density = maxPossibleEdges > 0 ? (edgeCount / maxPossibleEdges) * 100 : 0;
    const densityScore = density <= 30 ? 100 - density : 100 - (density - 30) * 2;
    
    return Math.round((fanOutScore + densityScore) / 2);
  }

  private scoreRiskManagement(): number {
    const riskNodes = this.nodes.filter(node => node.type === 'risk').length;
    const actionNodes = this.nodes.filter(node => node.type === 'action').length;
    
    if (actionNodes === 0) return 100; // No actions, no risk needed
    
    const riskRatio = riskNodes / actionNodes;
    if (riskRatio >= 0.5) return 100;
    if (riskRatio >= 0.25) return 80;
    if (riskRatio > 0) return 60;
    return 20; // No risk management
  }

  private scoreParameterOptimization(): number {
    let score = 100;
    
    // Check for default parameters
    let defaultParamCount = 0;
    let totalParams = 0;
    
    this.nodes.forEach(node => {
      const params = node.data.parameters || {};
      Object.entries(params).forEach(([key, value]) => {
        totalParams++;
        if (node.type && this.isDefaultParameter(node.type, key, value)) {
          defaultParamCount++;
        }
      });
    });
    
    if (totalParams > 0) {
      const defaultRatio = defaultParamCount / totalParams;
      score = Math.round(100 - defaultRatio * 50);
    }
    
    return score;
  }

  private scoreResourceUsage(nodeCount: number, depth: number): number {
    // Penalize excessive resource usage
    const nodeScore = nodeCount <= 20 ? 100 : 100 - (nodeCount - 20) * 2;
    const depthScore = depth <= 10 ? 100 : 100 - (depth - 10) * 5;
    
    return Math.round((nodeScore + depthScore) / 2);
  }

  private generateOptimizationSuggestions(): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];

    // Performance suggestions
    suggestions.push(...this.getPerformanceSuggestions());
    
    // Architecture suggestions
    suggestions.push(...this.getArchitectureSuggestions());
    
    // Risk management suggestions
    suggestions.push(...this.getRiskManagementSuggestions());
    
    // Maintainability suggestions
    suggestions.push(...this.getMaintainabilitySuggestions());

    return suggestions.sort((a, b) => {
      const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    });
  }

  private getPerformanceSuggestions(): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];

    // Too many nodes
    if (this.nodes.length > 25) {
      suggestions.push({
        id: 'reduce-node-count',
        type: 'performance',
        severity: 'medium',
        title: 'Reduce Node Count',
        description: `Workflow has ${this.nodes.length} nodes, which may impact performance.`,
        impact: 'High node count increases computation time and memory usage.',
        suggestion: 'Consider combining similar indicators or removing redundant nodes.',
        estimatedImpact: { performance: 15, reliability: 5 }
      });
    }

    // Deep workflow
    const depth = this.calculateWorkflowDepth();
    if (depth > 8) {
      suggestions.push({
        id: 'reduce-workflow-depth',
        type: 'performance',
        severity: 'medium',
        title: 'Reduce Workflow Depth',
        description: `Workflow depth is ${depth}, which may cause delays in signal generation.`,
        impact: 'Deep workflows have longer processing chains and higher latency.',
        suggestion: 'Consider parallel processing or reducing sequential dependencies.',
        estimatedImpact: { performance: 20, reliability: 10 }
      });
    }

    // Heavy indicators
    const heavyIndicators = this.nodes.filter(node => 
      node.type === 'technicalIndicator' && 
      (node.data.parameters?.period > 100 || 
       ['BB', 'MACD', 'Stochastic'].includes(node.data.parameters?.indicator))
    );

    if (heavyIndicators.length > 3) {
      suggestions.push({
        id: 'optimize-heavy-indicators',
        type: 'performance',
        severity: 'low',
        title: 'Optimize Heavy Indicators',
        description: 'Multiple complex indicators detected that may slow execution.',
        impact: 'Complex indicators require more computation resources.',
        suggestion: 'Consider using simpler alternatives or reducing indicator periods.',
        nodeIds: heavyIndicators.map(n => n.id),
        estimatedImpact: { performance: 25 }
      });
    }

    return suggestions;
  }

  private getArchitectureSuggestions(): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];

    // Isolated nodes
    const isolatedNodes = this.nodes.filter(node => {
      const hasIncoming = this.edges.some(edge => edge.target === node.id);
      const hasOutgoing = this.edges.some(edge => edge.source === node.id);
      return !hasIncoming && !hasOutgoing;
    });

    if (isolatedNodes.length > 0) {
      suggestions.push({
        id: 'connect-isolated-nodes',
        type: 'architecture',
        severity: 'high',
        title: 'Connect Isolated Nodes',
        description: `${isolatedNodes.length} node(s) are not connected to the workflow.`,
        impact: 'Isolated nodes do not contribute to the strategy logic.',
        suggestion: 'Connect these nodes to the workflow or remove them if unnecessary.',
        nodeIds: isolatedNodes.map(n => n.id),
        estimatedImpact: { maintainability: 20, reliability: 15 }
      });
    }

    // Missing data sources
    const dataSourceNodes = this.nodes.filter(n => n.type === 'dataSource' || n.type === 'customDataset');
    if (dataSourceNodes.length === 0 && this.nodes.length > 0) {
      suggestions.push({
        id: 'add-data-source',
        type: 'architecture',
        severity: 'critical',
        title: 'Add Data Source',
        description: 'Workflow is missing a data source node.',
        impact: 'Without data sources, the strategy cannot process market data.',
        suggestion: 'Add a Market Data or Custom Dataset node as the starting point.',
        estimatedImpact: { reliability: 50, maintainability: 30 }
      });
    }

    // Missing output
    const outputNodes = this.nodes.filter(n => n.type === 'output' || n.type === 'action');
    if (outputNodes.length === 0 && this.nodes.length > 0) {
      suggestions.push({
        id: 'add-output',
        type: 'architecture',
        severity: 'high',
        title: 'Add Output or Action Node',
        description: 'Workflow has no output or action nodes.',
        impact: 'Without outputs, the strategy cannot generate trades or signals.',
        suggestion: 'Add action nodes or output display to complete the workflow.',
        estimatedImpact: { reliability: 40, maintainability: 25 }
      });
    }

    return suggestions;
  }

  private getRiskManagementSuggestions(): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];

    const actionNodes = this.nodes.filter(n => n.type === 'action');
    const riskNodes = this.nodes.filter(n => n.type === 'risk');

    if (actionNodes.length > 0 && riskNodes.length === 0) {
      suggestions.push({
        id: 'add-risk-management',
        type: 'risk',
        severity: 'critical',
        title: 'Add Risk Management',
        description: 'Strategy has trading actions but no risk management.',
        impact: 'Uncontrolled risk can lead to significant losses.',
        suggestion: 'Add position sizing, stop losses, or portfolio risk controls.',
        estimatedImpact: { reliability: 60, maintainability: 30 }
      });
    }

    // Check for stop losses in actions
    const actionsWithoutStops = actionNodes.filter(node => {
      const params = node.data.parameters || {};
      return !params.stop_loss || params.stop_loss <= 0;
    });

    if (actionsWithoutStops.length > 0) {
      suggestions.push({
        id: 'add-stop-losses',
        type: 'risk',
        severity: 'high',
        title: 'Add Stop Losses',
        description: `${actionsWithoutStops.length} action(s) missing stop loss protection.`,
        impact: 'Trades without stop losses can lead to unlimited losses.',
        suggestion: 'Set appropriate stop loss levels for all trading actions.',
        nodeIds: actionsWithoutStops.map(n => n.id),
        estimatedImpact: { reliability: 40, maintainability: 20 }
      });
    }

    return suggestions;
  }

  private getMaintainabilitySuggestions(): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];

    // Nodes with default parameters
    const nodesWithDefaults = this.nodes.filter(node => {
      const params = node.data.parameters || {};
      return Object.entries(params).some(([key, value]) => 
        node.type && this.isDefaultParameter(node.type, key, value)
      );
    });

    if (nodesWithDefaults.length > this.nodes.length * 0.5) {
      suggestions.push({
        id: 'optimize-parameters',
        type: 'maintainability',
        severity: 'low',
        title: 'Optimize Parameters',
        description: 'Many nodes are using default parameters.',
        impact: 'Default parameters may not be optimal for your strategy.',
        suggestion: 'Review and customize parameters based on your requirements.',
        nodeIds: nodesWithDefaults.map(n => n.id),
        estimatedImpact: { performance: 10, maintainability: 15 }
      });
    }

    return suggestions;
  }

  // Helper methods
  private buildAdjacencyList(): Map<string, string[]> {
    const adjList = new Map<string, string[]>();
    this.nodes.forEach(node => adjList.set(node.id, []));
    this.edges.forEach(edge => {
      const neighbors = adjList.get(edge.source) || [];
      neighbors.push(edge.target);
      adjList.set(edge.source, neighbors);
    });
    return adjList;
  }

  private bfsMaxDepth(startId: string, adjList: Map<string, string[]>): number {
    const visited = new Set<string>();
    const queue: { id: string; depth: number }[] = [{ id: startId, depth: 0 }];
    let maxDepth = 0;

    while (queue.length > 0) {
      const { id, depth } = queue.shift()!;
      if (visited.has(id)) continue;

      visited.add(id);
      maxDepth = Math.max(maxDepth, depth);

      const neighbors = adjList.get(id) || [];
      neighbors.forEach(neighborId => {
        if (!visited.has(neighborId)) {
          queue.push({ id: neighborId, depth: depth + 1 });
        }
      });
    }

    return maxDepth;
  }

  private countConnectedComponents(): number {
    const visited = new Set<string>();
    let components = 0;

    for (const node of this.nodes) {
      if (!visited.has(node.id)) {
        this.dfsMarkComponent(node.id, visited);
        components++;
      }
    }

    return components;
  }

  private dfsMarkComponent(nodeId: string, visited: Set<string>): void {
    visited.add(nodeId);
    
    // Find connected nodes (both incoming and outgoing)
    const connectedNodes = new Set<string>();
    this.edges.forEach(edge => {
      if (edge.source === nodeId) connectedNodes.add(edge.target);
      if (edge.target === nodeId) connectedNodes.add(edge.source);
    });

    connectedNodes.forEach(connectedId => {
      if (!visited.has(connectedId)) {
        this.dfsMarkComponent(connectedId, visited);
      }
    });
  }

  private countIsolatedNodes(): number {
    return this.nodes.filter(node => {
      const hasConnection = this.edges.some(edge => 
        edge.source === node.id || edge.target === node.id
      );
      return !hasConnection;
    }).length;
  }

  private countDuplicateLogic(): number {
    // Simple heuristic: count nodes of same type with same parameters
    const nodeSignatures = this.nodes.map(node => ({
      type: node.type,
      params: JSON.stringify(node.data.parameters || {})
    }));

    const duplicates = new Set<string>();
    const seen = new Set<string>();

    nodeSignatures.forEach(sig => {
      const signature = `${sig.type}:${sig.params}`;
      if (seen.has(signature)) {
        duplicates.add(signature);
      }
      seen.add(signature);
    });

    return duplicates.size;
  }

  private countMissingRiskManagement(): number {
    const actionNodes = this.nodes.filter(n => n.type === 'action').length;
    const riskNodes = this.nodes.filter(n => n.type === 'risk').length;
    return Math.max(0, actionNodes - riskNodes);
  }

  private countSuboptimalConnections(): number {
    // Count connections that might be suboptimal
    let count = 0;
    
    // Direct data-to-action connections (should have conditions)
    this.edges.forEach(edge => {
      const sourceNode = this.nodes.find(n => n.id === edge.source);
      const targetNode = this.nodes.find(n => n.id === edge.target);
      
      if (sourceNode?.type === 'dataSource' && targetNode?.type === 'action') {
        count++;
      }
    });

    return count;
  }

  private isDefaultParameter(nodeType: string, key: string, value: any): boolean {
    const defaults: Record<string, Record<string, any>> = {
      technicalIndicator: { period: 20, source: 'close' },
      condition: { value: 0, confirmationBars: 0 },
      action: { quantity: 10, order_type: 'market' },
      risk: { maxLoss: 2.0, positionSize: 5.0 }
    };

    return defaults[nodeType]?.[key] === value;
  }

  private determineHealthStatus(score: number): WorkflowHealth['status'] {
    if (score >= 90) return 'excellent';
    if (score >= 75) return 'good';
    if (score >= 60) return 'fair';
    if (score >= 40) return 'poor';
    return 'critical';
  }
}

export function analyzeWorkflow(nodes: Node[], edges: Edge[]): WorkflowHealth {
  const analyzer = new WorkflowAnalyzer(nodes, edges);
  return analyzer.analyzeWorkflow();
}