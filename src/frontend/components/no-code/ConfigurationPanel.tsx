'use client';

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useNoCodeStore } from '@/lib/stores/no-code-store';
import { useToast } from '@/components/ui/use-toast';
import { shallow } from 'zustand/shallow';
import { 
  Settings, 
  ArrowRight, 
  ArrowLeft, 
  Code, 
  Info,
  Trash2,
  Copy,
  Play,
  CheckCircle
} from 'lucide-react';
import { ValidationPanel } from './ValidationPanel';
import { useWorkflowValidation } from '@/hooks/useWorkflowValidation';
import { getNodeConfiguration, validateNodeConfiguration, ConfigField } from './configuration';

interface ConfigurationPanelProps {
  selectedNode: string | null;
  onNodeSelect?: (nodeId: string | null) => void;
}

export function ConfigurationPanel({ selectedNode, onNodeSelect }: ConfigurationPanelProps) {
  const { currentWorkflow, updateNodeParameters, removeNode, duplicateNode } = useNoCodeStore(
    (state) => ({
      currentWorkflow: state.currentWorkflow,
      updateNodeParameters: state.updateNodeParameters,
      removeNode: state.removeNode,
      duplicateNode: state.duplicateNode
    }),
    shallow
  );
  const { toast } = useToast();
  const [localParameters, setLocalParameters] = useState<Record<string, any>>({});
  const [isDirty, setIsDirty] = useState(false);
  const updateTimeoutRef = useRef<NodeJS.Timeout>();
  
  // Add workflow validation
  const validation = useWorkflowValidation(
    currentWorkflow?.nodes || [],
    currentWorkflow?.edges || [],
    {
      autoValidate: true,
      debounceMs: 300,
      enableRealTime: true
    }
  );

  // Get the selected node data from the store using useMemo for optimization
  const selectedNodeData = useMemo(() => {
    if (!selectedNode || !currentWorkflow) return null;
    return currentWorkflow.nodes.find(node => node.id === selectedNode);
  }, [selectedNode, currentWorkflow?.nodes]);
  
  console.log('ConfigurationPanel:', { selectedNode, selectedNodeData, localParameters, isDirty }); // Debug log

  // Sync local parameters when selected node changes
  useEffect(() => {
    if (selectedNodeData) {
      const nodeParams = selectedNodeData.data.parameters || {};
      setLocalParameters(nodeParams);
      setIsDirty(false);
    } else {
      setLocalParameters({});
      setIsDirty(false);
    }
  }, [selectedNodeData?.id]); // Only trigger when node ID changes

  // Listen for parameter changes from store (e.g., from other components)
  useEffect(() => {
    if (selectedNodeData) {
      const storeParams = selectedNodeData.data.parameters || {};
      const hasExternalChanges = JSON.stringify(storeParams) !== JSON.stringify(localParameters);
      
      if (hasExternalChanges && !isDirty) {
        setLocalParameters(storeParams);
      }
    }
  }, [selectedNodeData?.data.parameters, isDirty]);

  // Debounced parameter update with immediate save for important changes
  const debouncedUpdate = useCallback((nodeId: string, newParameters: Record<string, any>) => {
    if (updateTimeoutRef.current) {
      clearTimeout(updateTimeoutRef.current);
    }
    
    updateTimeoutRef.current = setTimeout(() => {
      updateNodeParameters(nodeId, newParameters);
      setIsDirty(false);
      updateTimeoutRef.current = undefined;
      
      // Show success feedback for significant changes
      if (Object.keys(newParameters).length > 0) {
        toast({
          title: "Parameters Updated",
          description: "Node configuration has been saved",
        });
      }
    }, 200); // 200ms debounce - faster saving
  }, [updateNodeParameters, toast]);

  const handleParameterChange = useCallback((key: string, value: any) => {
    const newParameters = { ...localParameters, [key]: value };
    setLocalParameters(newParameters);
    setIsDirty(true);
    
    if (selectedNode) {
      debouncedUpdate(selectedNode, newParameters);
    }
  }, [localParameters, selectedNode, debouncedUpdate]);

  // Cleanup timeout on unmount and save pending changes
  useEffect(() => {
    return () => {
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
        // Note: We can't reliably save on unmount due to React's cleanup timing
        // The debounced save should handle most cases
      }
    };
  }, []);

  const handleDeleteNode = () => {
    if (selectedNode) {
      console.log('Deleting node:', selectedNode); // Debug log
      removeNode(selectedNode);
      console.log('Node deletion called'); // Debug log
    }
  };

  const handleDuplicateNode = () => {
    if (selectedNode) {
      duplicateNode(selectedNode);
    }
  };

  if (!selectedNode || !selectedNodeData) {
    return (
      <div className="h-full p-4 flex items-center justify-center text-center">
        <div className="space-y-3">
          <Settings className="h-12 w-12 mx-auto text-muted-foreground" />
          <div>
            <h3 className="font-medium text-foreground">No Node Selected</h3>
            <p className="text-sm text-muted-foreground">
              Select a node to configure its parameters
            </p>
          </div>
        </div>
      </div>
    );
  }

  const renderParameterInput = (key: string, config: ConfigField) => {
    const value = localParameters[key] ?? config.default;

    switch (config.type) {
      case 'number':
        return (
          <div className="space-y-2">
            <Label htmlFor={key}>{config.label}</Label>
            <Input
              id={key}
              type="number"
              value={value || ''}
              onChange={(e) => handleParameterChange(key, parseFloat(e.target.value) || 0)}
              min={config.min}
              max={config.max}
              step={config.step}
            />
            {config.description && (
              <p className="text-xs text-muted-foreground">{config.description}</p>
            )}
          </div>
        );

      case 'select':
        const filteredOptions = getFilteredOptions(config, key);
        return (
          <div className="space-y-2">
            <Label htmlFor={key}>{config.label}</Label>
            <Select value={value} onValueChange={(val) => handleParameterChange(key, val)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {filteredOptions.map((option: any) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {config.description && (
              <p className="text-xs text-muted-foreground">{config.description}</p>
            )}
          </div>
        );

      case 'boolean':
        return (
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor={key}>{config.label}</Label>
              {config.description && (
                <p className="text-xs text-muted-foreground">{config.description}</p>
              )}
            </div>
            <Switch
              id={key}
              checked={value || false}
              onCheckedChange={(checked) => handleParameterChange(key, checked)}
            />
          </div>
        );

      case 'range':
        return (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor={key}>{config.label}</Label>
              <span className="text-sm text-muted-foreground">{value}</span>
            </div>
            <Slider
              value={[value || config.default]}
              onValueChange={(values) => handleParameterChange(key, values[0])}
              min={config.min}
              max={config.max}
              step={config.step}
              className="w-full"
            />
            {config.description && (
              <p className="text-xs text-muted-foreground">{config.description}</p>
            )}
          </div>
        );

      default:
        return (
          <div className="space-y-2">
            <Label htmlFor={key}>{config.label}</Label>
            <Input
              id={key}
              value={value || ''}
              onChange={(e) => handleParameterChange(key, e.target.value)}
              placeholder={config.placeholder}
            />
            {config.description && (
              <p className="text-xs text-muted-foreground">{config.description}</p>
            )}
          </div>
        );
    }
  };

  // Get node configuration using the new modular system
  const nodeConfigResult = getNodeConfiguration(selectedNodeData?.type || 'unknown');
  const nodeConfig = nodeConfigResult.fields;

  // Use the shouldShowField function from the configuration module
  const shouldShowField = nodeConfigResult.shouldShowField || (() => true);

  // Function to filter options based on category selection
  const getFilteredOptions = (config: ConfigField, key: string) => {
    if (config.type !== 'select') return [];
    
    // Get the current category selection based on node type
    let categoryValue: string | null = null;
    const nodeType = selectedNodeData?.type;
    
    if (nodeType === 'technicalIndicator' && key === 'indicator') {
      categoryValue = localParameters.indicatorCategory || 'trend';
    } else if (nodeType === 'condition' && key === 'condition') {
      categoryValue = localParameters.conditionType || 'comparison';
    } else if (nodeType === 'action' && key === 'action') {
      categoryValue = localParameters.actionCategory || 'entry';
    } else if (nodeType === 'risk' && key === 'riskType') {
      categoryValue = localParameters.riskCategory || 'position';
    }
    
    // If no category filtering is needed, return all options
    if (!categoryValue) {
      return config.options;
    }
    
    // Filter options based on category
    return config.options.filter(option => 
      !option.category || option.category === categoryValue
    );
  };

  // Use the validation function from the configuration module
  const getValidationErrors = () => {
    const nodeType = selectedNodeData?.type;
    if (!nodeType) return [];
    return validateNodeConfiguration(nodeType, localParameters);
  };

  // Helper function to get node inputs with connection status
  const getNodeInputs = () => {
    if (!selectedNode || !currentWorkflow) return [];
    
    const nodeType = selectedNodeData?.type;
    const edges = currentWorkflow.edges;
    
    // Find all edges targeting this node
    const incomingEdges = edges.filter(edge => edge.target === selectedNode);
    
    // Define default inputs based on node type
    const defaultInputs = {
      dataSource: [],
      customDataset: [],
      technicalIndicator: [{ id: 'data-input', name: 'Data Input' }],
      condition: [
        { id: 'data-input', name: 'Data Input' },
        { id: 'value-input', name: 'Value Input' }
      ],
      action: [{ id: 'signal-input', name: 'Signal Input' }],
      logic: Array.from({ length: localParameters.inputs || 2 }, (_, i) => ({
        id: `input-${i}`,
        name: `Input ${i + 1}`
      })),
      risk: [
        { id: 'data-input', name: 'Data Input' },
        { id: 'signal-input', name: 'Signal Input' }
      ],
      output: [
        { id: 'data-input', name: 'Data Input' },
        { id: 'signal-input', name: 'Signal Input' }
      ]
    };

    const nodeInputs = defaultInputs[nodeType as keyof typeof defaultInputs] || [];
    
    return nodeInputs.map(input => {
      const connectedEdge = incomingEdges.find(edge => edge.targetHandle === input.id);
      return {
        ...input,
        connected: !!connectedEdge,
        source: connectedEdge ? getNodeLabel(connectedEdge.source) : null
      };
    });
  };

  // Helper function to get node outputs with connection status
  const getNodeOutputs = () => {
    if (!selectedNode || !currentWorkflow) return [];
    
    const nodeType = selectedNodeData?.type;
    const edges = currentWorkflow.edges;
    
    // Find all edges originating from this node
    const outgoingEdges = edges.filter(edge => edge.source === selectedNode);
    
    // Define default outputs based on node type
    const defaultOutputs = {
      dataSource: [{ id: 'data-output', name: 'Data Output', color: 'bg-gray-500' }],
      customDataset: [{ id: 'data-output', name: 'Data Output', color: 'bg-gray-500' }],
      technicalIndicator: [
        { id: 'value-output', name: 'Value Output', color: 'bg-blue-500' },
        { id: 'signal-output', name: 'Signal Output', color: 'bg-green-500' }
      ],
      condition: [{ id: 'signal-output', name: 'Signal Output', color: 'bg-green-500' }],
      action: [],
      logic: [{ id: 'output', name: 'Logic Output', color: 'bg-green-500' }],
      risk: [{ id: 'risk-output', name: 'Risk Output', color: 'bg-orange-500' }],
      output: []
    };

    const nodeOutputs = defaultOutputs[nodeType as keyof typeof defaultOutputs] || [];
    
    return nodeOutputs.map(output => {
      const connections = outgoingEdges.filter(edge => edge.sourceHandle === output.id).length;
      return {
        ...output,
        connected: connections
      };
    });
  };

  // Helper function to get node label by ID
  const getNodeLabel = (nodeId: string) => {
    const node = currentWorkflow?.nodes.find(n => n.id === nodeId);
    return node?.data.label || nodeId;
  };


  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 space-y-4">
        {/* Node Header */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Node Configuration</h2>
            <div className="flex space-x-1">
              <Button size="sm" variant="outline" onClick={handleDuplicateNode}>
                <Copy className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="outline" onClick={handleDeleteNode}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Badge variant="secondary">{selectedNodeData.type}</Badge>
              <span className="text-sm font-medium text-foreground">{selectedNodeData.data.label}</span>
            </div>
            <p className="text-xs text-muted-foreground">
              ID: {selectedNode}
            </p>
          </div>
        </div>

        <Separator />

        {/* Configuration Tabs */}
        <Tabs defaultValue="parameters" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="parameters" data-value="parameters">
              <Settings className="h-4 w-4 mr-1" />
              Parameters
            </TabsTrigger>
            <TabsTrigger value="inputs" data-value="inputs">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Inputs
            </TabsTrigger>
            <TabsTrigger value="outputs" data-value="outputs">
              <ArrowRight className="h-4 w-4 mr-1" />
              Outputs
            </TabsTrigger>
            <TabsTrigger value="validation" data-value="validation">
              <CheckCircle className={`h-4 w-4 mr-1 ${
                validation.validation.isValid 
                  ? 'text-green-500' 
                  : validation.hasErrors 
                    ? 'text-red-500' 
                    : 'text-yellow-500'
              }`} />
              Validation
              {(validation.hasErrors || validation.hasWarnings) && (
                <Badge 
                  variant={validation.hasErrors ? "destructive" : "secondary"} 
                  className="ml-1 text-xs px-1 py-0"
                >
                  {validation.validation.errors.length + validation.validation.warnings.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="parameters" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-semibold text-foreground">Node Parameters</CardTitle>
                  {isDirty && (
                    <div className="flex items-center space-x-2 text-xs text-amber-600">
                      <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
                      <span>Unsaved changes</span>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(nodeConfig).map(([key, config]) => {
                  // Conditional field rendering based on other parameter values
                  const shouldShow = shouldShowField(key, config, localParameters);
                  if (!shouldShow) return null;
                  
                  return (
                    <div key={key}>
                      {renderParameterInput(key, config)}
                    </div>
                  );
                })}
                {Object.keys(nodeConfig).length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No parameters available for this node type
                  </p>
                )}
                
                {/* Validation Messages */}
                {getValidationErrors().length > 0 && (
                  <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
                    <h4 className="text-sm font-medium text-red-800 dark:text-red-400 mb-2">Configuration Errors:</h4>
                    <ul className="text-xs text-red-600 dark:text-red-400 space-y-1">
                      {getValidationErrors().map((error, index) => (
                        <li key={index}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="inputs" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold text-foreground">Input Connections</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {getNodeInputs().map((input, index) => (
                    <div key={index} className="flex items-center justify-between p-2 border rounded">
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${input.connected ? 'bg-green-500' : 'bg-gray-300'}`} />
                        <span className="text-sm">{input.name}</span>
                      </div>
                      <Badge variant={input.connected ? "outline" : "secondary"}>
                        {input.connected ? `Connected to ${input.source}` : 'Not Connected'}
                      </Badge>
                    </div>
                  ))}
                  {getNodeInputs().length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      This node has no input connections
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="outputs" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold text-foreground">Output Connections</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {getNodeOutputs().map((output, index) => (
                    <div key={index} className="flex items-center justify-between p-2 border rounded">
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${output.color}`} />
                        <span className="text-sm">{output.name}</span>
                      </div>
                      <Badge variant="outline">
                        {output.connected} connections
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="validation" className="space-y-4">
            <ValidationPanel 
              validation={validation}
              onNodeSelect={(nodeId) => {
                // Focus on the node when validation error is clicked
                console.log('Validation panel requesting focus on node:', nodeId);
                if (onNodeSelect && nodeId) {
                  onNodeSelect(nodeId);
                }
              }}
              nodes={currentWorkflow?.nodes || []}
              edges={currentWorkflow?.edges || []}
              className="border-0 shadow-none p-0"
            />
          </TabsContent>
        </Tabs>

        {/* Test Node */}
        <Card>
          <CardContent className="pt-4">
            <Button className="w-full" variant="outline">
              <Play className="h-4 w-4 mr-2" />
              Test Node
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}