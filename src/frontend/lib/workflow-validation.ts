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
  suggestions: ValidationSuggestion[];
  performance: {
    estimatedComplexity: number;
    estimatedExecutionTime: number;
    memoryUsage: number;
    logicDepth: number;
    indicatorCount: number;
    signalPathCount: number;
  };
}

export interface ValidationSuggestion {
  id: string;
  type: 'optimization' | 'best_practice' | 'alternative_approach';
  message: string;
  nodeIds: string[];
  priority: 'high' | 'medium' | 'low';
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
    this.validateTimeframeConsistency();
    
    // Enhanced validations for sophisticated workflows
    this.validateSignalPaths();
    this.validateLogicGateIntegrity();
    this.validateMultiOutputIndicators();
    
    // Performance and security checks
    this.validatePerformanceImpact();
    this.validateSecurityVulnerabilities();

    const errors = this.errors.filter(e => e.type === 'error');
    const warnings = this.errors.filter(e => e.type === 'warning');
    const suggestions = this.generateOptimizationSuggestions();

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      suggestions,
      performance: this.calculateEnhancedPerformanceMetrics()
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
      case 'marketRegimeDetection':
        return 1;
      case 'multiTimeframeAnalysis':
        return 1;
      case 'correlationAnalysis':
        return 2;
      case 'sentimentAnalysis':
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
      case 'correlationAnalysis':
        return 2;
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
        
        // Channel-based outputs
        if (handle.includes('upper') || handle.includes('lower') || handle.includes('middle') || handle.includes('width')) return 'numeric';
        
        // MACD and PPO outputs  
        if (handle.includes('histogram') || handle.includes('macd') || handle.includes('ppo')) return 'numeric';
        
        // For MACD, PPO, TSI signal outputs, we need to check the node's indicator type
        if (handle === 'signal-output') {
          // This would need node context to determine indicator type, defaulting to numeric for multi-output indicators
          return 'numeric';
        }
        
        // Stochastic outputs (including KDJ)
        if (handle.includes('k') || handle.includes('d') || handle.includes('j')) return 'numeric';
        
        // Directional indicators
        if (handle.includes('adx') || handle.includes('di_plus') || handle.includes('di_minus') || 
            handle.includes('dmi_plus') || handle.includes('dmi_minus')) return 'numeric';
        
        // Aroon outputs
        if (handle.includes('aroon_up') || handle.includes('aroon_down')) return 'numeric';
        
        // Vortex outputs
        if (handle.includes('vi_plus') || handle.includes('vi_minus')) return 'numeric';
        
        // TSI output
        if (handle.includes('tsi')) return 'numeric';
        
        // Default value output
        if (handle.includes('value')) return 'value';
        
        // Generic signal outputs (for simple indicators that just have signal/value outputs)
        if (handle.includes('signal')) return 'signal';
        
        return 'numeric'; // Default for all other technical indicator outputs
      case 'condition':
        return 'signal';
      case 'logic':
        return 'signal';
      case 'risk':
        return 'risk';
      case 'marketRegimeDetection':
        return 'signal';
      case 'multiTimeframeAnalysis':
        return 'ohlcv';
      case 'correlationAnalysis':
        return 'numeric';
      case 'sentimentAnalysis':
        return 'signal';
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
      case 'marketRegimeDetection':
        return 'ohlcv';
      case 'multiTimeframeAnalysis':
        return 'ohlcv';
      case 'correlationAnalysis':
        return 'ohlcv';
      case 'sentimentAnalysis':
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

  /**
   * Validates timeframe consistency for nodes that process time-series data.
   */
  private validateTimeframeConsistency(): void {
    this.nodes.forEach(node => {
      if (node.type === 'technicalIndicator' || node.type === 'condition') {
        const timeframes = this.getUpstreamTimeframes(node.id, new Set());
        if (timeframes.size > 1) {
          this.addError({
            id: `timeframe_inconsistency_${node.id}`,
            type: 'warning',
            category: 'connection',
            severity: 'medium',
            message: `Node "${node.data.label}" receives data from multiple timeframes: ${Array.from(timeframes).join(', ')}. This can lead to unexpected results.`,
            nodeId: node.id,
            suggestion: 'Ensure that all data sources feeding into this node have the same timeframe, or use specific nodes to handle multi-timeframe logic.'
          });
        }
      }
    });
  }

  private getUpstreamTimeframes(nodeId: string, visited: Set<string>): Set<string> {
    if (visited.has(nodeId)) {
      return new Set();
    }
    visited.add(nodeId);

    const node = this.nodes.find(n => n.id === nodeId);
    if (!node) {
      return new Set();
    }

    if (node.type === 'dataSource') {
      return new Set([node.data.parameters?.timeframe].filter(Boolean));
    }

    const incomingEdges = this.edges.filter(e => e.target === nodeId);
    if (incomingEdges.length === 0) {
      return new Set();
    }

    const timeframes = new Set<string>();
    for (const edge of incomingEdges) {
      const upstreamTimeframes = this.getUpstreamTimeframes(edge.source, visited);
      upstreamTimeframes.forEach(tf => timeframes.add(tf));
    }

    return timeframes;
  }

  /**
   * Validate complete signal paths from data sources to actions
   */
  private validateSignalPaths(): void {
    const dataSources = this.nodes.filter(n => n.type === 'dataSource' || n.type === 'customDataset');
    const actions = this.nodes.filter(n => n.type === 'action');
    
    if (dataSources.length === 0 || actions.length === 0) return;

    dataSources.forEach(dataSource => {
      actions.forEach(action => {
        const pathExists = this.hasPathBetweenNodes(dataSource.id, action.id);
        if (!pathExists) {
          this.addError({
            id: `no_signal_path_${dataSource.id}_${action.id}`,
            type: 'warning',
            category: 'structure',
            severity: 'medium',
            message: `No signal path from "${dataSource.data?.label}" to "${action.data?.label}"`,
            nodeId: dataSource.id,
            suggestion: 'Ensure there is a complete path from data source through indicators and conditions to action'
          });
        }
      });
    });
  }

  /**
   * Validate logic gate connections and configurations
   */
  private validateLogicGateIntegrity(): void {
    const logicNodes = this.nodes.filter(n => n.type === 'logic');
    
    logicNodes.forEach(logicNode => {
      const incomingEdges = this.edges.filter(e => e.target === logicNode.id);
      const expectedInputs = logicNode.data?.parameters?.inputs || 2;
      
      if (incomingEdges.length < expectedInputs) {
        this.addError({
          id: `logic_insufficient_inputs_${logicNode.id}`,
          type: 'error',
          category: 'connection',
          severity: 'high',
          message: `Logic gate "${logicNode.data?.label}" needs ${expectedInputs} inputs, has ${incomingEdges.length}`,
          nodeId: logicNode.id,
          suggestion: 'Connect the required number of condition signals to this logic gate'
        });
      }

      // Check for logic depth (nested logic gates)
      const logicDepth = this.calculateLogicDepth(logicNode.id, new Set());
      if (logicDepth > 5) {
        this.addError({
          id: `deep_logic_nesting_${logicNode.id}`,
          type: 'warning',
          category: 'performance',
          severity: 'medium',
          message: `Deep logic nesting detected (depth: ${logicDepth})`,
          nodeId: logicNode.id,
          suggestion: 'Consider simplifying nested logic for better performance and maintainability'
        });
      }
    });
  }

  /**
   * Validate multi-output technical indicators
   */
  private validateMultiOutputIndicators(): void {
    const multiOutputIndicators = this.nodes.filter(n => 
      n.type === 'technicalIndicator' && 
      ['ADX', 'BB', 'MACD', 'STOCH', 'KDJ', 'Ichimoku', 'VolumeProfile', 'MarketStructure'].includes(n.data?.parameters?.indicator)
    );

    multiOutputIndicators.forEach(indicator => {
      const outgoingEdges = this.edges.filter(e => e.source === indicator.id);
      const indicatorType = indicator.data?.parameters?.indicator;
      
      // Check if all outputs are properly utilized
      const expectedOutputs = this.getExpectedOutputCount(indicatorType);
      const usedOutputs = new Set(outgoingEdges.map(e => e.sourceHandle).filter(Boolean));
      
      if (usedOutputs.size < expectedOutputs) {
        this.addError({
          id: `underutilized_outputs_${indicator.id}`,
          type: 'info',
          category: 'structure',
          severity: 'low',
          message: `${indicatorType} indicator has unused outputs (${usedOutputs.size}/${expectedOutputs})`,
          nodeId: indicator.id,
          suggestion: 'Consider using all indicator outputs or switch to a simpler indicator'
        });
      }

      // Validate output handle correctness
      outgoingEdges.forEach(edge => {
        if (edge.sourceHandle && !this.isValidIndicatorHandle(indicatorType, edge.sourceHandle)) {
          this.addError({
            id: `invalid_output_handle_${edge.id}`,
            type: 'error',
            category: 'connection',
            severity: 'high',
            message: `Invalid output handle "${edge.sourceHandle}" for ${indicatorType}`,
            edgeId: edge.id,
            suggestion: 'Use valid output handles for this indicator type'
          });
        }
      });
    });
  }

  /**
   * Generate optimization suggestions based on workflow analysis
   */
  private generateOptimizationSuggestions(): ValidationSuggestion[] {
    const suggestions: ValidationSuggestion[] = [];
    
    // Suggest indicator consolidation
    const indicatorGroups = this.findSimilarIndicators();
    if (indicatorGroups.length > 0) {
      suggestions.push({
        id: 'consolidate_similar_indicators',
        type: 'optimization',
        message: `Found ${indicatorGroups.length} groups of similar indicators that could be consolidated`,
        nodeIds: indicatorGroups.flat(),
        priority: 'medium'
      });
    }

    // Suggest logic simplification
    const complexLogicNodes = this.findComplexLogicNodes();
    if (complexLogicNodes.length > 0) {
      suggestions.push({
        id: 'simplify_complex_logic',
        type: 'optimization',
        message: 'Consider simplifying complex logic gates for better performance',
        nodeIds: complexLogicNodes,
        priority: 'medium'
      });
    }

    // Suggest performance optimizations
    const performanceSuggestions = this.generatePerformanceSuggestions();
    suggestions.push(...performanceSuggestions);

    // Suggest best practices
    const bestPracticeSuggestions = this.generateBestPracticeSuggestions();
    suggestions.push(...bestPracticeSuggestions);

    return suggestions;
  }

  /**
   * Calculate enhanced performance metrics
   */
  private calculateEnhancedPerformanceMetrics() {
    const complexity = this.calculateComplexity();
    const logicDepth = this.calculateMaxLogicDepth();
    const indicatorCount = this.nodes.filter(n => n.type === 'technicalIndicator').length;
    const signalPathCount = this.calculateSignalPathCount();
    
    return {
      estimatedComplexity: complexity,
      estimatedExecutionTime: this.estimateExecutionTime(complexity, logicDepth, indicatorCount),
      memoryUsage: this.estimateMemoryUsage(),
      logicDepth,
      indicatorCount,
      signalPathCount
    };
  }

  // Enhanced helper methods
  private hasPathBetweenNodes(sourceId: string, targetId: string): boolean {
    const visited = new Set<string>();
    const queue = [sourceId];
    
    while (queue.length > 0) {
      const currentId = queue.shift()!;
      if (currentId === targetId) return true;
      if (visited.has(currentId)) continue;
      
      visited.add(currentId);
      const neighbors = this.edges
        .filter(e => e.source === currentId)
        .map(e => e.target);
      queue.push(...neighbors);
    }
    
    return false;
  }

  private calculateLogicDepth(nodeId: string, visited: Set<string>): number {
    if (visited.has(nodeId)) return 0;
    visited.add(nodeId);
    
    const children = this.edges
      .filter(e => e.source === nodeId)
      .map(e => e.target)
      .filter(targetId => {
        const targetNode = this.nodes.find(n => n.id === targetId);
        return targetNode?.type === 'logic';
      });
    
    if (children.length === 0) return 1;
    
    return 1 + Math.max(...children.map(childId => 
      this.calculateLogicDepth(childId, new Set(visited))
    ));
  }

  private calculateMaxLogicDepth(): number {
    const logicNodes = this.nodes.filter(n => n.type === 'logic');
    return Math.max(0, ...logicNodes.map(node => 
      this.calculateLogicDepth(node.id, new Set())
    ));
  }

  private getExpectedOutputCount(indicatorType: string): number {
    const outputCounts: Record<string, number> = {
      'ADX': 3, // ADX, DI+, DI-
      'BB': 4,  // Upper, Middle, Lower, Width
      'MACD': 3, // MACD, Signal, Histogram
      'STOCH': 2, // %K, %D
      'KDJ': 3,   // %K, %D, %J
      'Ichimoku': 5,
      'VolumeProfile': 3,
      'MarketStructure': 4,
    };
    return outputCounts[indicatorType] || 2;
  }

  private isValidIndicatorHandle(indicatorType: string, handle: string): boolean {
    const validHandles: Record<string, string[]> = {
      'ADX': ['adx', 'di_plus', 'di_minus'],
      'BB': ['upper', 'middle', 'lower', 'width'],
      'MACD': ['macd', 'signal', 'histogram'],
      'STOCH': ['k', 'd'],
      'KDJ': ['k', 'd', 'j'],
      'Ichimoku': ['tenkan', 'kijun', 'senkou_a', 'senkou_b', 'chikou'],
      'VolumeProfile': ['poc', 'vah', 'val'],
      'MarketStructure': ['higher_high', 'lower_low', 'support', 'resistance'],
    };
    // Also allow generic output handles
    const genericHandles = ['output-1', 'output-2', 'output-3', 'output-4', 'output-5'];
    const specificHandles = validHandles[indicatorType] || [];
    return specificHandles.includes(handle) || genericHandles.includes(handle);
  }

  private findSimilarIndicators(): string[][] {
    const groups: string[][] = [];
    const indicatorMap = new Map<string, string[]>();
    
    this.nodes
      .filter(n => n.type === 'technicalIndicator')
      .forEach(node => {
        const key = `${node.data?.parameters?.indicator}-${node.data?.parameters?.period}`;
        const existing = indicatorMap.get(key) || [];
        existing.push(node.id);
        indicatorMap.set(key, existing);
      });
    
    indicatorMap.forEach(group => {
      if (group.length > 1) groups.push(group);
    });
    
    return groups;
  }

  private findComplexLogicNodes(): string[] {
    return this.nodes
      .filter(n => n.type === 'logic')
      .filter(node => {
        const inputCount = this.edges.filter(e => e.target === node.id).length;
        const outputCount = this.edges.filter(e => e.source === node.id).length;
        return inputCount > 3 || outputCount > 2;
      })
      .map(n => n.id);
  }

  private generatePerformanceSuggestions(): ValidationSuggestion[] {
    const suggestions: ValidationSuggestion[] = [];
    
    const indicatorCount = this.nodes.filter(n => n.type === 'technicalIndicator').length;
    if (indicatorCount > 8) {
      suggestions.push({
        id: 'too_many_indicators',
        type: 'optimization',
        message: `High number of indicators (${indicatorCount}) may impact performance`,
        nodeIds: this.nodes.filter(n => n.type === 'technicalIndicator').map(n => n.id),
        priority: 'high'
      });
    }
    
    return suggestions;
  }

  private generateBestPracticeSuggestions(): ValidationSuggestion[] {
    const suggestions: ValidationSuggestion[] = [];
    
    // Check for missing risk management
    const riskNodes = this.nodes.filter(n => n.type === 'risk');
    const actionNodes = this.nodes.filter(n => n.type === 'action');
    
    if (actionNodes.length > 0 && riskNodes.length === 0) {
      suggestions.push({
        id: 'add_risk_management',
        type: 'best_practice',
        message: 'Consider adding risk management nodes to protect your strategy',
        nodeIds: actionNodes.map(n => n.id),
        priority: 'high'
      });
    }
    
    return suggestions;
  }

  private calculateSignalPathCount(): number {
    const dataSources = this.nodes.filter(n => n.type === 'dataSource' || n.type === 'customDataset');
    const actions = this.nodes.filter(n => n.type === 'action');
    
    let pathCount = 0;
    dataSources.forEach(source => {
      actions.forEach(action => {
        if (this.hasPathBetweenNodes(source.id, action.id)) {
          pathCount++;
        }
      });
    });
    
    return pathCount;
  }

  private estimateExecutionTime(complexity: number, logicDepth: number, indicatorCount: number): number {
    // Base execution time
    let execTime = Math.max(complexity / 100, 10);
    
    // Add time for indicator calculations
    execTime += indicatorCount * 2;
    
    // Add time for logic depth
    execTime += logicDepth * 5;
    
    return Math.round(execTime);
  }

  private estimateMemoryUsage(): number {
    const baseMemory = this.nodes.length * 1024 + this.edges.length * 512;
    const indicatorMemory = this.nodes.filter(n => n.type === 'technicalIndicator').length * 2048;
    const logicMemory = this.nodes.filter(n => n.type === 'logic').length * 512;
    
    return baseMemory + indicatorMemory + logicMemory;
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