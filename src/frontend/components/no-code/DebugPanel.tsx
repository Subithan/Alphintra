import React, { useState, useEffect, useRef } from 'react';
import { Node, Edge } from 'reactflow';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { Button } from '@/components/ui/no-code/button';
import { 
  Bug, 
  Play, 
  Pause, 
  StepForward, 
  RotateCcw, 
  Zap,
  Eye,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Activity,
  Target,
  GitBranch
} from 'lucide-react';
import { ExecutionResult, SignalResult } from '@/lib/execution-engine';
import { MultiTimeframeExecutionResult, CrossTimeframeSignal } from '@/lib/multi-timeframe-engine';

export interface DebugState {
  current_step: number;
  total_steps: number;
  execution_path: ExecutionStep[];
  signal_flow: SignalFlowTrace[];
  indicator_values: Record<string, Record<string, number[]>>;
  condition_states: Record<string, boolean>;
  logic_states: Record<string, boolean>;
  warnings: DebugWarning[];
  performance_breakdown: PerformanceBreakdown;
}

export interface ExecutionStep {
  step_id: string;
  step_type: 'indicator' | 'condition' | 'logic' | 'action';
  node_id: string;
  timestamp: Date;
  input_values: Record<string, any>;
  output_values: Record<string, any>;
  execution_time_ms: number;
  success: boolean;
  error_message?: string;
  dependencies_met: boolean;
}

export interface SignalFlowTrace {
  trace_id: string;
  source_node: string;
  target_node: string;
  signal_type: 'data' | 'condition' | 'logic' | 'trigger';
  value: any;
  timestamp: Date;
  propagation_delay_ms: number;
  path_depth: number;
}

export interface DebugWarning {
  warning_id: string;
  severity: 'low' | 'medium' | 'high';
  category: 'performance' | 'logic' | 'data' | 'configuration';
  message: string;
  node_id?: string;
  suggestion: string;
  auto_fixable: boolean;
}

export interface PerformanceBreakdown {
  total_execution_time: number;
  indicator_time: number;
  condition_time: number;
  logic_time: number;
  action_time: number;
  bottlenecks: {
    node_id: string;
    node_type: string;
    execution_time: number;
    percentage_of_total: number;
  }[];
}

interface DebugPanelProps {
  nodes: Node[];
  edges: Edge[];
  executionResults: ExecutionResult[];
  multiTimeframeResults?: MultiTimeframeExecutionResult[];
  isDebugging: boolean;
  onStartDebugging: () => void;
  onStopDebugging: () => void;
  onStepDebugging: () => void;
  onResetDebugging: () => void;
}

export function DebugPanel({
  nodes,
  edges,
  executionResults,
  multiTimeframeResults,
  isDebugging,
  onStartDebugging,
  onStopDebugging,
  onStepDebugging,
  onResetDebugging
}: DebugPanelProps) {
  const [debugState, setDebugState] = useState<DebugState | null>(null);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [showSignalFlow, setShowSignalFlow] = useState(true);
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'execution' | 'signals' | 'performance' | 'warnings'>('execution');
  const debugIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (executionResults.length > 0) {
      generateDebugState();
    }
  }, [executionResults, nodes, edges]);

  useEffect(() => {
    // Auto-refresh debug state when debugging
    if (isDebugging) {
      debugIntervalRef.current = setInterval(() => {
        generateDebugState();
      }, 1000);
    } else {
      if (debugIntervalRef.current) {
        clearInterval(debugIntervalRef.current);
        debugIntervalRef.current = null;
      }
    }

    return () => {
      if (debugIntervalRef.current) {
        clearInterval(debugIntervalRef.current);
      }
    };
  }, [isDebugging]);

  const generateDebugState = () => {
    if (executionResults.length === 0) return;

    const latestResult = executionResults[executionResults.length - 1];
    const executionPath = generateExecutionPath(latestResult);
    const signalFlow = generateSignalFlow(latestResult);
    const warnings = generateWarnings(latestResult);
    const performanceBreakdown = generatePerformanceBreakdown(latestResult);

    const newDebugState: DebugState = {
      current_step: selectedStep ?? executionPath.length - 1,
      total_steps: executionPath.length,
      execution_path: executionPath,
      signal_flow: signalFlow,
      indicator_values: extractIndicatorValues(latestResult),
      condition_states: extractConditionStates(latestResult),
      logic_states: extractLogicStates(latestResult),
      warnings,
      performance_breakdown: performanceBreakdown
    };

    setDebugState(newDebugState);
  };

  const generateExecutionPath = (result: ExecutionResult): ExecutionStep[] => {
    const steps: ExecutionStep[] = [];
    const timestamp = result.timestamp;

    // Simulate execution steps based on workflow topology
    const processingOrder = getNodeProcessingOrder();

    processingOrder.forEach((nodeId, index) => {
      const node = nodes.find(n => n.id === nodeId);
      if (!node) return;

      const step: ExecutionStep = {
        step_id: `step_${index}`,
        step_type: node.type as ExecutionStep['step_type'],
        node_id: nodeId,
        timestamp: new Date(timestamp.getTime() + index * 10), // Simulate timing
        input_values: getNodeInputValues(node, result),
        output_values: getNodeOutputValues(node, result),
        execution_time_ms: Math.random() * 5 + 1, // Simulate execution time
        success: result.errors.length === 0,
        dependencies_met: checkDependenciesMet(nodeId),
        error_message: result.errors.length > 0 ? result.errors[0] : undefined
      };

      steps.push(step);
    });

    return steps;
  };

  const generateSignalFlow = (result: ExecutionResult): SignalFlowTrace[] => {
    const traces: SignalFlowTrace[] = [];
    let traceId = 0;

    edges.forEach(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);

      if (sourceNode && targetNode) {
        const trace: SignalFlowTrace = {
          trace_id: `trace_${traceId++}`,
          source_node: edge.source,
          target_node: edge.target,
          signal_type: getSignalType(sourceNode.type, targetNode.type),
          value: getSignalValue(edge, result),
          timestamp: result.timestamp,
          propagation_delay_ms: Math.random() * 2, // Simulate propagation delay
          path_depth: calculatePathDepth(edge.target)
        };

        traces.push(trace);
      }
    });

    return traces.sort((a, b) => a.path_depth - b.path_depth);
  };

  const generateWarnings = (result: ExecutionResult): DebugWarning[] => {
    const warnings: DebugWarning[] = [];
    let warningId = 0;

    // Performance warnings
    if (result.performance_metrics.execution_time_ms > 1000) {
      warnings.push({
        warning_id: `warning_${warningId++}`,
        severity: 'high',
        category: 'performance',
        message: 'Strategy execution time exceeds 1 second',
        suggestion: 'Consider optimizing indicator calculations or reducing complexity',
        auto_fixable: false
      });
    }

    // Memory warnings
    if (result.performance_metrics.memory_usage_mb > 100) {
      warnings.push({
        warning_id: `warning_${warningId++}`,
        severity: 'medium',
        category: 'performance',
        message: 'High memory usage detected',
        suggestion: 'Reduce lookback periods or indicator count',
        auto_fixable: false
      });
    }

    // Logic warnings
    const isolatedNodes = nodes.filter(node => 
      !edges.some(edge => edge.source === node.id || edge.target === node.id)
    );

    isolatedNodes.forEach(node => {
      warnings.push({
        warning_id: `warning_${warningId++}`,
        severity: 'medium',
        category: 'logic',
        message: `Node ${node.data?.label || node.id} is not connected`,
        node_id: node.id,
        suggestion: 'Connect this node to the workflow or remove it',
        auto_fixable: true
      });
    });

    // Data warnings
    if (result.signals.length === 0 && nodes.some(n => n.type === 'action')) {
      warnings.push({
        warning_id: `warning_${warningId++}`,
        severity: 'low',
        category: 'data',
        message: 'No signals generated despite having action nodes',
        suggestion: 'Check condition thresholds and indicator values',
        auto_fixable: false
      });
    }

    return warnings;
  };

  const generatePerformanceBreakdown = (result: ExecutionResult): PerformanceBreakdown => {
    const totalTime = result.performance_metrics.execution_time_ms;
    
    // Estimate time breakdown based on node types
    const indicatorNodes = nodes.filter(n => n.type === 'technicalIndicator').length;
    const conditionNodes = nodes.filter(n => n.type === 'condition').length;
    const logicNodes = nodes.filter(n => n.type === 'logic').length;
    const actionNodes = nodes.filter(n => n.type === 'action').length;

    const indicatorTime = indicatorNodes * 2; // Estimate 2ms per indicator
    const conditionTime = conditionNodes * 0.5; // Estimate 0.5ms per condition
    const logicTime = logicNodes * 0.3; // Estimate 0.3ms per logic gate
    const actionTime = actionNodes * 0.2; // Estimate 0.2ms per action

    // Find bottlenecks (nodes taking longest time)
    const bottlenecks = nodes
      .map(node => ({
        node_id: node.id,
        node_type: node.type || 'unknown',
        execution_time: getEstimatedNodeTime(node),
        percentage_of_total: (getEstimatedNodeTime(node) / totalTime) * 100
      }))
      .filter(b => b.percentage_of_total > 10)
      .sort((a, b) => b.execution_time - a.execution_time)
      .slice(0, 5);

    return {
      total_execution_time: totalTime,
      indicator_time: indicatorTime,
      condition_time: conditionTime,
      logic_time: logicTime,
      action_time: actionTime,
      bottlenecks
    };
  };

  const getNodeProcessingOrder = (): string[] => {
    // Topological sort of nodes based on edges
    const inDegree = new Map<string, number>();
    const adjList = new Map<string, string[]>();

    nodes.forEach(node => {
      inDegree.set(node.id, 0);
      adjList.set(node.id, []);
    });

    edges.forEach(edge => {
      const sources = adjList.get(edge.source) || [];
      sources.push(edge.target);
      adjList.set(edge.source, sources);
      inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
    });

    const queue: string[] = [];
    const result: string[] = [];

    nodes.forEach(node => {
      if (inDegree.get(node.id) === 0) {
        queue.push(node.id);
      }
    });

    while (queue.length > 0) {
      const current = queue.shift()!;
      result.push(current);

      const neighbors = adjList.get(current) || [];
      neighbors.forEach(neighbor => {
        const newInDegree = (inDegree.get(neighbor) || 0) - 1;
        inDegree.set(neighbor, newInDegree);
        if (newInDegree === 0) {
          queue.push(neighbor);
        }
      });
    }

    return result;
  };

  const getNodeInputValues = (node: Node, result: ExecutionResult): Record<string, any> => {
    // Simulate input values based on node type and connections
    const inputs: Record<string, any> = {};
    
    const incomingEdges = edges.filter(e => e.target === node.id);
    incomingEdges.forEach((edge, index) => {
      inputs[`input_${index}`] = Math.random() * 100; // Simulate values
    });

    return inputs;
  };

  const getNodeOutputValues = (node: Node, result: ExecutionResult): Record<string, any> => {
    const outputs: Record<string, any> = {};

    switch (node.type) {
      case 'technicalIndicator':
        outputs.value = Math.random() * 100;
        if (node.data?.parameters?.indicator === 'ADX') {
          outputs.adx = Math.random() * 100;
          outputs.di_plus = Math.random() * 100;
          outputs.di_minus = Math.random() * 100;
        }
        break;
      case 'condition':
        outputs.result = Math.random() > 0.5;
        break;
      case 'logic':
        outputs.result = Math.random() > 0.5;
        break;
      case 'action':
        outputs.signal = result.signals.length > 0 ? result.signals[0] : null;
        break;
    }

    return outputs;
  };

  const checkDependenciesMet = (nodeId: string): boolean => {
    const incomingEdges = edges.filter(e => e.target === nodeId);
    return incomingEdges.length === 0 || Math.random() > 0.1; // Simulate 90% success rate
  };

  const getSignalType = (sourceType: string, targetType: string): SignalFlowTrace['signal_type'] => {
    if (sourceType === 'dataSource' || sourceType === 'customDataset') return 'data';
    if (sourceType === 'condition') return 'condition';
    if (sourceType === 'logic') return 'logic';
    if (targetType === 'action') return 'trigger';
    return 'data';
  };

  const getSignalValue = (edge: Edge, result: ExecutionResult): any => {
    // Simulate signal values
    return Math.random() * 100;
  };

  const calculatePathDepth = (nodeId: string): number => {
    // Calculate depth from data sources
    const visited = new Set<string>();
    const calculateDepth = (id: string): number => {
      if (visited.has(id)) return 0;
      visited.add(id);

      const incomingEdges = edges.filter(e => e.target === id);
      if (incomingEdges.length === 0) return 0;

      return 1 + Math.max(...incomingEdges.map(e => calculateDepth(e.source)));
    };

    return calculateDepth(nodeId);
  };

  const extractIndicatorValues = (result: ExecutionResult): Record<string, Record<string, number[]>> => {
    const values: Record<string, Record<string, number[]>> = {};
    
    nodes.filter(n => n.type === 'technicalIndicator').forEach(node => {
      values[node.id] = {
        value: Array.from({ length: 20 }, () => Math.random() * 100)
      };
    });

    return values;
  };

  const extractConditionStates = (result: ExecutionResult): Record<string, boolean> => {
    const states: Record<string, boolean> = {};
    
    nodes.filter(n => n.type === 'condition').forEach(node => {
      states[node.id] = Math.random() > 0.5;
    });

    return states;
  };

  const extractLogicStates = (result: ExecutionResult): Record<string, boolean> => {
    const states: Record<string, boolean> = {};
    
    nodes.filter(n => n.type === 'logic').forEach(node => {
      states[node.id] = Math.random() > 0.5;
    });

    return states;
  };

  const getEstimatedNodeTime = (node: Node): number => {
    switch (node.type) {
      case 'technicalIndicator': return Math.random() * 5 + 1;
      case 'condition': return Math.random() * 1 + 0.2;
      case 'logic': return Math.random() * 0.5 + 0.1;
      case 'action': return Math.random() * 0.3 + 0.1;
      default: return 0.1;
    }
  };

  const handleStepSelect = (stepIndex: number) => {
    setSelectedStep(stepIndex);
    
    if (debugState && debugState.execution_path[stepIndex]) {
      const step = debugState.execution_path[stepIndex];
      setHighlightedNodes(new Set([step.node_id]));
    }
  };

  const getStepIcon = (stepType: ExecutionStep['step_type']) => {
    switch (stepType) {
      case 'indicator': return <TrendingUp className="h-4 w-4" />;
      case 'condition': return <Target className="h-4 w-4" />;
      case 'logic': return <GitBranch className="h-4 w-4" />;
      case 'action': return <Zap className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const getSeverityColor = (severity: DebugWarning['severity']) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300';
    }
  };

  if (!debugState) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Bug className="h-5 w-5" />
            <span>Debug Panel</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Bug className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-gray-500 mb-4">No execution data available for debugging</p>
            <Button onClick={onStartDebugging} className="flex items-center space-x-2">
              <Play className="h-4 w-4" />
              <span>Start Debugging</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Debug Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bug className="h-5 w-5" />
              <span>Debug Controls</span>
            </div>
            <Badge className={isDebugging ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
              {isDebugging ? 'Active' : 'Inactive'}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="flex space-x-2">
              {!isDebugging ? (
                <Button onClick={onStartDebugging} size="sm" className="flex items-center space-x-2">
                  <Play className="h-4 w-4" />
                  <span>Start</span>
                </Button>
              ) : (
                <Button onClick={onStopDebugging} size="sm" variant="destructive" className="flex items-center space-x-2">
                  <Pause className="h-4 w-4" />
                  <span>Stop</span>
                </Button>
              )}
              
              <Button onClick={onStepDebugging} size="sm" variant="outline" className="flex items-center space-x-2">
                <StepForward className="h-4 w-4" />
                <span>Step</span>
              </Button>
              
              <Button onClick={onResetDebugging} size="sm" variant="outline" className="flex items-center space-x-2">
                <RotateCcw className="h-4 w-4" />
                <span>Reset</span>
              </Button>
            </div>
            
            <div className="text-sm text-gray-600">
              Step {debugState.current_step + 1} of {debugState.total_steps}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Debug Tabs */}
      <Card>
        <CardHeader>
          <div className="flex space-x-4 border-b">
            {(['execution', 'signals', 'performance', 'warnings'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-2 px-1 text-sm font-medium capitalize ${
                  activeTab === tab 
                    ? 'border-b-2 border-blue-500 text-blue-600' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab}
                {tab === 'warnings' && debugState.warnings.length > 0 && (
                  <Badge className="ml-2 bg-red-100 text-red-800 text-xs">
                    {debugState.warnings.length}
                  </Badge>
                )}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {/* Execution Path Tab */}
          {activeTab === 'execution' && (
            <div className="space-y-3">
              <h4 className="font-medium">Execution Path</h4>
              <div className="max-h-60 overflow-y-auto space-y-2">
                {debugState.execution_path.map((step, index) => (
                  <div
                    key={step.step_id}
                    onClick={() => handleStepSelect(index)}
                    className={`p-3 border rounded cursor-pointer transition-colors ${
                      selectedStep === index 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getStepIcon(step.step_type)}
                        <div>
                          <div className="font-medium text-sm">{step.node_id}</div>
                          <div className="text-xs text-gray-500 capitalize">{step.step_type}</div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Badge className="text-xs">
                          {step.execution_time_ms.toFixed(1)}ms
                        </Badge>
                        {step.success ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-red-500" />
                        )}
                      </div>
                    </div>
                    
                    {selectedStep === index && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <div className="grid grid-cols-2 gap-4 text-xs">
                          <div>
                            <div className="font-medium mb-1">Inputs:</div>
                            <pre className="bg-gray-50 p-2 rounded">
                              {JSON.stringify(step.input_values, null, 2)}
                            </pre>
                          </div>
                          <div>
                            <div className="font-medium mb-1">Outputs:</div>
                            <pre className="bg-gray-50 p-2 rounded">
                              {JSON.stringify(step.output_values, null, 2)}
                            </pre>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Signal Flow Tab */}
          {activeTab === 'signals' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Signal Flow Trace</h4>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowSignalFlow(!showSignalFlow)}
                  className="flex items-center space-x-2"
                >
                  <Eye className="h-4 w-4" />
                  <span>{showSignalFlow ? 'Hide' : 'Show'} Flow</span>
                </Button>
              </div>
              
              <div className="max-h-60 overflow-y-auto space-y-2">
                {debugState.signal_flow.map(flow => (
                  <div key={flow.trace_id} className="p-3 border border-gray-200 rounded">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 rounded-full ${
                          flow.signal_type === 'data' ? 'bg-blue-500' :
                          flow.signal_type === 'condition' ? 'bg-yellow-500' :
                          flow.signal_type === 'logic' ? 'bg-purple-500' :
                          'bg-green-500'
                        }`} />
                        <div>
                          <div className="text-sm font-medium">
                            {flow.source_node} → {flow.target_node}
                          </div>
                          <div className="text-xs text-gray-500 capitalize">
                            {flow.signal_type} signal
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-xs text-gray-500">
                        Depth: {flow.path_depth} | {flow.propagation_delay_ms.toFixed(1)}ms
                      </div>
                    </div>
                    
                    <div className="mt-2 text-xs">
                      <span className="font-medium">Value: </span>
                      <code className="bg-gray-100 px-1 rounded">{JSON.stringify(flow.value)}</code>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Performance Tab */}
          {activeTab === 'performance' && (
            <div className="space-y-4">
              <h4 className="font-medium">Performance Breakdown</h4>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {debugState.performance_breakdown.total_execution_time.toFixed(1)}ms
                  </div>
                  <div className="text-sm text-gray-600">Total Time</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {debugState.performance_breakdown.indicator_time.toFixed(1)}ms
                  </div>
                  <div className="text-sm text-gray-600">Indicators</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">
                    {debugState.performance_breakdown.condition_time.toFixed(1)}ms
                  </div>
                  <div className="text-sm text-gray-600">Conditions</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {debugState.performance_breakdown.logic_time.toFixed(1)}ms
                  </div>
                  <div className="text-sm text-gray-600">Logic</div>
                </div>
              </div>

              {debugState.performance_breakdown.bottlenecks.length > 0 && (
                <div>
                  <h5 className="font-medium mb-2">Performance Bottlenecks</h5>
                  <div className="space-y-2">
                    {debugState.performance_breakdown.bottlenecks.map(bottleneck => (
                      <div key={bottleneck.node_id} className="flex items-center justify-between p-2 bg-red-50 border border-red-200 rounded">
                        <div>
                          <div className="font-medium text-sm">{bottleneck.node_id}</div>
                          <div className="text-xs text-gray-500 capitalize">{bottleneck.node_type}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium">{bottleneck.execution_time.toFixed(1)}ms</div>
                          <div className="text-xs text-gray-500">{bottleneck.percentage_of_total.toFixed(1)}%</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Warnings Tab */}
          {activeTab === 'warnings' && (
            <div className="space-y-3">
              <h4 className="font-medium">Debug Warnings</h4>
              
              {debugState.warnings.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                  <p className="text-green-600">No warnings detected</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {debugState.warnings.map(warning => (
                    <div key={warning.warning_id} className={`p-3 border rounded ${getSeverityColor(warning.severity)}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{warning.message}</div>
                          {warning.node_id && (
                            <div className="text-xs opacity-75 mt-1">Node: {warning.node_id}</div>
                          )}
                          <div className="text-xs mt-2">{warning.suggestion}</div>
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-4">
                          <Badge className="text-xs capitalize">{warning.category}</Badge>
                          {warning.auto_fixable && (
                            <Button size="sm" variant="outline" className="text-xs px-2 py-1">
                              Auto Fix
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}