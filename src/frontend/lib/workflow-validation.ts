import { Node, Edge } from 'reactflow';

export interface ValidationError {
  id: string;
  type: 'error' | 'warning' | 'info';
  category: 'structure' | 'connection' | 'parameter' | 'performance' | 'security';
  message: string;
  nodeId?: string;
  edgeId?: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  suggestion?: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  performance: {
    estimatedComplexity: number;
    estimatedExecutionTime: number;
    memoryUsage: number;
  };
}

export class WorkflowValidator {
  private nodes: Node[];
  private edges: Edge[];
  private errors: ValidationError[] = [];

  constructor(nodes: Node[], edges: Edge[]) {
    this.nodes = nodes;
    this.edges = edges;
    this.errors = [];
  }

  /**
   * Main validation method that runs all checks
   */
  validate(): ValidationResult {
    this.errors = [];

    // Core structural validations
    this.validateDAGStructure();
    this.validateMinimumRequirements();
    this.validateNodeConnections();
    this.validateDataTypeCompatibility();
    this.validateParameterRanges();
    this.validateCircularDependencies();
    
    // Performance and security checks
    this.validatePerformanceImpact();
    this.validateSecurityVulnerabilities();

    const errors = this.errors.filter(e => e.type === 'error');
    const warnings = this.errors.filter(e => e.type === 'warning');

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      performance: this.calculatePerformanceMetrics()
    };
  }

  /**
   * Validate that the workflow forms a valid Directed Acyclic Graph
   */
  private validateDAGStructure(): void {
    const nodeMap = new Map(this.nodes.map(node => [node.id, node]));
    const adjList = new Map<string, string[]>();
    
    // Build adjacency list
    this.nodes.forEach(node => adjList.set(node.id, []));
    this.edges.forEach(edge => {
      const sources = adjList.get(edge.source) || [];
      sources.push(edge.target);
      adjList.set(edge.source, sources);
    });

    // Check for cycles using DFS
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    const hasCycle = (nodeId: string): boolean => {
      visited.add(nodeId);
      recursionStack.add(nodeId);

      const neighbors = adjList.get(nodeId) || [];
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          if (hasCycle(neighbor)) return true;
        } else if (recursionStack.has(neighbor)) {
          return true;
        }
      }

      recursionStack.delete(nodeId);
      return false;
    };

    for (const nodeId of this.nodes.map(n => n.id)) {
      if (!visited.has(nodeId)) {
        if (hasCycle(nodeId)) {
          this.addError({
            id: 'circular_dependency',
            type: 'error',
            category: 'structure',
            severity: 'critical',
            message: 'Circular dependency detected in workflow',
            suggestion: 'Remove circular connections to create a valid workflow'
          });
          break;
        }
      }
    }
  }

  /**
   * Validate minimum workflow requirements
   */
  private validateMinimumRequirements(): void {
    const dataSourceNodes = this.nodes.filter(n => 
      n.type === 'dataSource' || n.type === 'customDataset'
    );
    const outputNodes = this.nodes.filter(n => n.type === 'output');

    if (dataSourceNodes.length === 0) {
      this.addError({
        id: 'missing_data_source',
        type: 'error',
        category: 'structure',
        severity: 'critical',
        message: 'Workflow must have at least one data source',
        suggestion: 'Add a Market Data or Custom Dataset node'
      });
    }

    if (outputNodes.length === 0) {
      this.addError({
        id: 'missing_output',
        type: 'warning',
        category: 'structure',
        severity: 'medium',
        message: 'Workflow should have an output node',
        suggestion: 'Add an Output node to display results'
      });
    }

    // Check for isolated nodes
    const connectedNodes = new Set<string>();
    this.edges.forEach(edge => {
      connectedNodes.add(edge.source);
      connectedNodes.add(edge.target);
    });

    this.nodes.forEach(node => {
      if (!connectedNodes.has(node.id) && this.nodes.length > 1) {
        this.addError({
          id: `isolated_node_${node.id}`,
          type: 'warning',
          category: 'connection',
          severity: 'low',
          message: `Node "${node.data.label}" is not connected`,
          nodeId: node.id,
          suggestion: 'Connect this node to the workflow or remove it'
        });
      }
    });
  }

  /**
   * Validate node connections and handle requirements
   */
  private validateNodeConnections(): void {
    this.nodes.forEach(node => {
      const incomingEdges = this.edges.filter(e => e.target === node.id);
      const outgoingEdges = this.edges.filter(e => e.source === node.id);

      // Validate required inputs based on node type
      const requiredInputs = this.getRequiredInputs(node);
      if (incomingEdges.length < requiredInputs) {
        this.addError({
          id: `insufficient_inputs_${node.id}`,
          type: 'error',
          category: 'connection',
          severity: 'high',
          message: `Node "${node.data.label}" requires ${requiredInputs} input(s), has ${incomingEdges.length}`,
          nodeId: node.id,
          suggestion: 'Connect the required inputs to this node'
        });
      }

      // Validate maximum inputs
      const maxInputs = this.getMaxInputs(node);
      if (maxInputs > 0 && incomingEdges.length > maxInputs) {
        this.addError({
          id: `excessive_inputs_${node.id}`,
          type: 'error',
          category: 'connection',
          severity: 'medium',
          message: `Node "${node.data.label}" has too many inputs (${incomingEdges.length}/${maxInputs})`,
          nodeId: node.id,
          suggestion: 'Remove excess connections'
        });
      }

      // Check for action nodes that should be terminal
      if (node.type === 'action' && outgoingEdges.length > 0) {
        this.addError({
          id: `action_with_outputs_${node.id}`,
          type: 'warning',
          category: 'connection',
          severity: 'low',
          message: `Action node "${node.data.label}" should not have outputs`,
          nodeId: node.id,
          suggestion: 'Action nodes are typically terminal nodes'
        });
      }
    });
  }

  /**
   * Validate data type compatibility between connected nodes
   */
  private validateDataTypeCompatibility(): void {
    this.edges.forEach(edge => {
      const sourceNode = this.nodes.find(n => n.id === edge.source);
      const targetNode = this.nodes.find(n => n.id === edge.target);

      if (!sourceNode || !targetNode) return;

      const outputType = this.getOutputType(sourceNode, edge.sourceHandle);
      const inputType = this.getInputType(targetNode, edge.targetHandle);

      if (!this.areTypesCompatible(outputType, inputType)) {
        this.addError({
          id: `type_mismatch_${edge.id}`,
          type: 'error',
          category: 'connection',
          severity: 'high',
          message: `Data type mismatch: ${outputType} cannot connect to ${inputType}`,
          edgeId: edge.id,
          suggestion: 'Connect compatible data types or add a conversion node'
        });
      }
    });
  }

  /**
   * Validate parameter ranges and values
   */
  private validateParameterRanges(): void {
    this.nodes.forEach(node => {
      const parameters = node.data.parameters || {};

      switch (node.type) {
        case 'technicalIndicator':
          this.validateTechnicalIndicatorParams(node, parameters);
          break;
        case 'condition':
          this.validateConditionParams(node, parameters);
          break;
        case 'action':
          this.validateActionParams(node, parameters);
          break;
        case 'risk':
          this.validateRiskParams(node, parameters);
          break;
      }
    });
  }

  /**
   * Validate circular dependencies using topological sort
   */
  private validateCircularDependencies(): void {
    const inDegree = new Map<string, number>();
    const adjList = new Map<string, string[]>();

    // Initialize
    this.nodes.forEach(node => {
      inDegree.set(node.id, 0);
      adjList.set(node.id, []);
    });

    // Build graph and calculate in-degrees
    this.edges.forEach(edge => {
      const sources = adjList.get(edge.source) || [];
      sources.push(edge.target);
      adjList.set(edge.source, sources);
      inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
    });

    // Kahn's algorithm for topological sorting
    const queue: string[] = [];
    this.nodes.forEach(node => {
      if (inDegree.get(node.id) === 0) {
        queue.push(node.id);
      }
    });

    let processedCount = 0;
    while (queue.length > 0) {
      const current = queue.shift()!;
      processedCount++;

      const neighbors = adjList.get(current) || [];
      neighbors.forEach(neighbor => {
        const newInDegree = (inDegree.get(neighbor) || 0) - 1;
        inDegree.set(neighbor, newInDegree);
        if (newInDegree === 0) {
          queue.push(neighbor);
        }
      });
    }

    if (processedCount !== this.nodes.length) {
      this.addError({
        id: 'circular_dependency_detected',
        type: 'error',
        category: 'structure',
        severity: 'critical',
        message: 'Circular dependency detected - workflow cannot be executed',
        suggestion: 'Remove circular connections to create a valid execution order'
      });
    }
  }

  /**
   * Validate performance impact
   */
  private validatePerformanceImpact(): void {
    const complexity = this.calculateComplexity();
    
    if (complexity > 1000) {
      this.addError({
        id: 'high_complexity',
        type: 'warning',
        category: 'performance',
        severity: 'medium',
        message: `High workflow complexity (${complexity}). May impact performance.`,
        suggestion: 'Consider simplifying the workflow or optimizing connections'
      });
    }

    // Check for potentially expensive operations
    this.nodes.forEach(node => {
      if (node.type === 'technicalIndicator') {
        const period = node.data.parameters?.period || 0;
        if (period > 200) {
          this.addError({
            id: `large_period_${node.id}`,
            type: 'warning',
            category: 'performance',
            severity: 'low',
            message: `Large indicator period (${period}) may impact performance`,
            nodeId: node.id,
            suggestion: 'Consider using smaller periods for better performance'
          });
        }
      }
    });
  }

  /**
   * Validate for security vulnerabilities
   */
  private validateSecurityVulnerabilities(): void {
    // Check for potential injection points
    this.nodes.forEach(node => {
      const params = node.data.parameters || {};
      
      // Check for potentially dangerous parameter values
      Object.entries(params).forEach(([key, value]) => {
        if (typeof value === 'string') {
          if (this.containsSuspiciousContent(value)) {
            this.addError({
              id: `suspicious_content_${node.id}`,
              type: 'error',
              category: 'security',
              severity: 'high',
              message: `Suspicious content detected in parameter "${key}"`,
              nodeId: node.id,
              suggestion: 'Remove potentially malicious content'
            });
          }
        }
      });
    });
  }

  // Helper methods
  private getRequiredInputs(node: Node): number {
    switch (node.type) {
      case 'dataSource':
      case 'customDataset':
        return 0;
      case 'technicalIndicator':
        return 1;
      case 'condition':
        return 1;
      case 'action':
        return 1;
      case 'logic':
        return node.data.parameters?.inputs || 2;
      case 'risk':
        return 1;
      case 'output':
        return 1;
      default:
        return 0;
    }
  }

  private getMaxInputs(node: Node): number {
    switch (node.type) {
      case 'logic':
        return node.data.parameters?.inputs || 8;
      case 'condition':
        return 2; // data + value inputs
      case 'risk':
        return 2; // data + signal inputs
      default:
        return this.getRequiredInputs(node);
    }
  }

  private getOutputType(node: Node, handle?: string | null): string {
    switch (node.type) {
      case 'dataSource':
      case 'customDataset':
        return 'ohlcv';
      case 'technicalIndicator':
        if (!handle) return 'value';
        if (handle.includes('signal')) return 'signal';
        if (handle.includes('upper') || handle.includes('lower') || handle.includes('middle')) return 'numeric';
        if (handle.includes('histogram') || handle.includes('macd') || handle.includes('k') || handle.includes('d')) return 'numeric';
        if (handle.includes('width') || handle.includes('adx') || handle.includes('di')) return 'numeric';
        return 'value';
      case 'condition':
        return 'signal';
      case 'logic':
        return 'signal';
      case 'risk':
        return 'risk';
      default:
        return 'unknown';
    }
  }

  private getInputType(node: Node, handle?: string | null): string {
    switch (node.type) {
      case 'technicalIndicator':
        return 'ohlcv';
      case 'condition':
        if (!handle) return 'ohlcv';
        if (handle.includes('value') || handle.includes('threshold')) return 'numeric';
        return 'ohlcv';
      case 'action':
        return 'signal';
      case 'logic':
        return 'signal';
      case 'risk':
        if (!handle) return 'signal';
        if (handle.includes('signal') || handle.includes('trigger')) return 'signal';
        return 'ohlcv';
      case 'output':
        return 'any';
      default:
        return 'unknown';
    }
  }

  private areTypesCompatible(outputType: string, inputType: string): boolean {
    if (inputType === 'any') return true;
    if (outputType === inputType) return true;
    
    // Enhanced type compatibility for multi-output system
    const compatibilityMatrix: Record<string, string[]> = {
      'ohlcv': ['ohlcv', 'numeric', 'value'],
      'numeric': ['numeric', 'value', 'ohlcv'],
      'value': ['value', 'numeric', 'ohlcv'],
      'signal': ['signal'],
      'risk': ['risk'],
      'execution': ['execution']
    };
    
    const compatibleTypes = compatibilityMatrix[outputType] || [];
    return compatibleTypes.includes(inputType);
  }

  private validateTechnicalIndicatorParams(node: Node, params: any): void {
    if (params.period && (params.period < 1 || params.period > 500)) {
      this.addError({
        id: `invalid_period_${node.id}`,
        type: 'error',
        category: 'parameter',
        severity: 'medium',
        message: `Invalid period value: ${params.period}`,
        nodeId: node.id,
        suggestion: 'Period should be between 1 and 500'
      });
    }
  }

  private validateConditionParams(node: Node, params: any): void {
    if (params.condition === 'range' && params.value >= params.value2) {
      this.addError({
        id: `invalid_range_${node.id}`,
        type: 'error',
        category: 'parameter',
        severity: 'medium',
        message: 'Range condition: lower bound must be less than upper bound',
        nodeId: node.id,
        suggestion: 'Adjust range values so lower < upper'
      });
    }
  }

  private validateActionParams(node: Node, params: any): void {
    if (params.quantity && params.quantity < 0) {
      this.addError({
        id: `negative_quantity_${node.id}`,
        type: 'error',
        category: 'parameter',
        severity: 'high',
        message: 'Quantity cannot be negative',
        nodeId: node.id,
        suggestion: 'Set quantity to a positive value'
      });
    }
  }

  private validateRiskParams(node: Node, params: any): void {
    if (params.maxLoss && (params.maxLoss <= 0 || params.maxLoss > 100)) {
      this.addError({
        id: `invalid_max_loss_${node.id}`,
        type: 'error',
        category: 'parameter',
        severity: 'high',
        message: `Invalid max loss: ${params.maxLoss}%`,
        nodeId: node.id,
        suggestion: 'Max loss should be between 0% and 100%'
      });
    }
  }

  private calculateComplexity(): number {
    let complexity = 0;
    
    // Base complexity from node count
    complexity += this.nodes.length * 10;
    
    // Additional complexity from connections
    complexity += this.edges.length * 5;
    
    // Additional complexity from specific node types
    this.nodes.forEach(node => {
      switch (node.type) {
        case 'technicalIndicator':
          complexity += 20;
          if (node.data.parameters?.period > 50) complexity += 10;
          break;
        case 'condition':
          complexity += 15;
          break;
        case 'logic':
          complexity += (node.data.parameters?.inputs || 2) * 5;
          break;
        default:
          complexity += 5;
      }
    });

    return complexity;
  }

  private calculatePerformanceMetrics() {
    const complexity = this.calculateComplexity();
    return {
      estimatedComplexity: complexity,
      estimatedExecutionTime: Math.max(complexity / 100, 10), // ms
      memoryUsage: this.nodes.length * 1024 + this.edges.length * 512 // bytes
    };
  }

  private containsSuspiciousContent(value: string): boolean {
    const suspiciousPatterns = [
      /eval\s*\(/i,
      /exec\s*\(/i,
      /system\s*\(/i,
      /import\s+os/i,
      /subprocess/i,
      /__import__/i,
      /script>/i,
      /javascript:/i
    ];

    return suspiciousPatterns.some(pattern => pattern.test(value));
  }

  private addError(error: Omit<ValidationError, 'id'> & { id: string }): void {
    this.errors.push(error);
  }
}

/**
 * Main validation function to be used by components
 */
export function validateWorkflow(nodes: Node[], edges: Edge[]): ValidationResult {
  const validator = new WorkflowValidator(nodes, edges);
  return validator.validate();
}