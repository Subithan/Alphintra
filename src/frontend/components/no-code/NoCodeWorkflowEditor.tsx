"use client";

import React, { useCallback, useEffect, useState, useRef, useMemo } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  ReactFlowProvider,
  BackgroundVariant,
  useReactFlow,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";

import { TechnicalIndicatorNode } from "./nodes/TechnicalIndicatorNode";
import { ConditionNode } from "./nodes/ConditionNode";
import { ActionNode } from "./nodes/ActionNode";
import { DataSourceNode } from "./nodes/DataSourceNode";
import { CustomDatasetNode } from "./nodes/CustomDatasetNode";
import { OutputNode } from "./nodes/OutputNode";
import { LogicNode } from "./nodes/LogicNode";
import { RiskManagementNode } from "./nodes/RiskManagementNode";
import { SmartEdge } from "./edges/SmartEdge";
import { useNoCodeStore } from "@/lib/stores/no-code-store";
import { useExecutionStore } from "@/lib/stores/execution-store";
import { connectionManager } from "@/lib/connection-manager";
import { validateWorkflow, ValidationResult } from "@/lib/workflow-validation";
import {
  getWorkflowOptimizations,
  OptimizationSuggestion,
} from "@/lib/workflow-optimizer";
import { noCodeApiClient } from "@/lib/api/no-code-api";
import { ConfigurationPanel } from "./ConfigurationPanel";
import {
  ExecutionModeSelector,
  type ExecutionMode,
  type ExecutionModeConfig,
  type ExecutionModeSelectorProps,
} from "./ExecutionModeSelector";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { X, AlertTriangle, CheckCircle, Info, Play, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";

// Define nodeTypes and edgeTypes components that will be memoized inside the component

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

type EstimatedDuration = NonNullable<
  ExecutionModeSelectorProps["estimatedDuration"]
>;

const DURATION_PRESETS: Record<
  "simple" | "medium" | "complex",
  EstimatedDuration
> = {
  simple: {
    strategy: "< 30 seconds",
    model: "1-2 hours",
    hybrid: "15-45 minutes",
    backtesting: "10-20 minutes",
    paper_trading: "Live (setup < 5 minutes)",
    research: "Instant",
  },
  medium: {
    strategy: "< 1 minute",
    model: "2-6 hours",
    hybrid: "30-90 minutes",
    backtesting: "20-45 minutes",
    paper_trading: "Live (setup < 10 minutes)",
    research: "Instant",
  },
  complex: {
    strategy: "< 2 minutes",
    model: "6-12 hours",
    hybrid: "1-3 hours",
    backtesting: "45-120 minutes",
    paper_trading: "Live (setup < 15 minutes)",
    research: "Instant",
  },
};

const getComplexityLevel = (score?: number): "simple" | "medium" | "complex" => {
  if (typeof score !== "number") {
    return "simple";
  }

  if (score >= 70) {
    return "complex";
  }

  if (score >= 35) {
    return "medium";
  }

  return "simple";
};

interface NoCodeWorkflowEditorProps {
  selectedNode: string | null;
  onNodeSelect: (nodeId: string | null) => void;
}

function NoCodeWorkflowEditorInner({
  selectedNode,
  onNodeSelect,
}: NoCodeWorkflowEditorProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [isClosingModal, setIsClosingModal] = useState(false);
  const [modalSelectedNode, setModalSelectedNode] = useState<string | null>(
    null,
  );
  const [validationResult, setValidationResult] =
    useState<ValidationResult | null>(null);
  const [optimizationSuggestions, setOptimizationSuggestions] = useState<
    OptimizationSuggestion[]
  >([]);
  const [showValidationPanel, setShowValidationPanel] = useState(false);
  const [showExecutionModal, setShowExecutionModal] = useState(false);
  const [isWorkflowSaved, setIsWorkflowSaved] = useState(false);
  const { toast } = useToast();
  const { currentWorkflow, updateWorkflow, addNode, removeNode } =
    useNoCodeStore();
  const {
    openExecutionModal,
    closeExecutionModal,
    isExecutionModalOpen,
    currentExecutionMode,
    currentExecutionStatus,
    setExecutionStatus,
  } = useExecutionStore();
  const { screenToFlowPosition } = useReactFlow();

  // Memoize nodeTypes and edgeTypes to prevent re-renders
  const nodeTypes = useMemo(() => ({
    technicalIndicator: TechnicalIndicatorNode,
    condition: ConditionNode,
    action: ActionNode,
    dataSource: DataSourceNode,
    customDataset: CustomDatasetNode,
    output: OutputNode,
    logic: LogicNode,
    risk: RiskManagementNode,
  }), []);

  const edgeTypes = useMemo(() => ({
    smart: SmartEdge,
  }), []);

  // Use ReactFlow state as primary, sync to store when needed
  // Ensure we have valid arrays even if the workflow data is malformed
  const initialNodes = Array.isArray(currentWorkflow?.nodes) ? currentWorkflow.nodes : [];
  const initialEdges = Array.isArray(currentWorkflow?.edges) ? currentWorkflow.edges : [];

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync store changes to ReactFlow when store is updated externally
  useEffect(() => {
    console.log('🔍 [DEBUG] Sync useEffect triggered:', {
      currentWorkflowId: currentWorkflow?.id,
      currentWorkflowName: currentWorkflow?.name,
      currentNodesCount: nodes.length,
      currentEdgesCount: edges.length,
      workflowNodesCount: currentWorkflow?.nodes?.length || 0,
      workflowEdgesCount: currentWorkflow?.edges?.length || 0,
      workflowUpdatedAt: currentWorkflow?.updatedAt
    });

    // Only sync when workflow is loaded from backend (has updatedAt) AND it's different from ReactFlow state
    if (currentWorkflow && currentWorkflow.updatedAt) {
      const currentNodesCount = nodes.length;
      const currentEdgesCount = edges.length;
      const newNodesCount = currentWorkflow.nodes.length;
      const newEdgesCount = currentWorkflow.edges.length;

      // Only sync if the workflow in store has more nodes than ReactFlow (indicating fresh load from backend)
      // OR if ReactFlow is empty but store has data
      if ((newNodesCount > currentNodesCount) || (currentNodesCount === 0 && newNodesCount > 0)) {
        console.log('🔍 [DEBUG] Syncing saved workflow to ReactFlow:', {
          workflowId: currentWorkflow.id,
          workflowName: currentWorkflow.name,
          nodesCount: newNodesCount,
          edgesCount: newEdgesCount,
          hasNodes: newNodesCount > 0,
          hasEdges: newEdgesCount > 0,
          reason: 'Fresh load from backend'
        });

        setNodes(currentWorkflow.nodes);
        setEdges(currentWorkflow.edges);
      } else {
        console.log('🔍 [DEBUG] No sync needed - ReactFlow has more recent changes');
      }
    } else {
      console.log('🔍 [DEBUG] Not syncing - default workflow or no updatedAt timestamp');
    }
  }, [
    currentWorkflow?.id, // Watch for workflow ID changes (most reliable)
    currentWorkflow?.updatedAt, // Watch for workflow updates (critical for fresh loads)
    setNodes,
    setEdges,
    // Only include nodes/edges length to prevent infinite loops, not to trigger syncs
  ]);

  // Track ReactFlow state changes and update store for all workflows
  useEffect(() => {
    console.log('🔍 [DEBUG] ReactFlow nodes/edges changed:', {
      nodesCount: nodes.length,
      edgesCount: edges.length,
      nodes: nodes.slice(0, 2),
      edges: edges.slice(0, 2),
      workflowId: currentWorkflow?.id
    });

    // Update store with ReactFlow changes for all workflows
    if (currentWorkflow) {
      console.log('🔍 [DEBUG] Updating store with ReactFlow changes for workflow:', currentWorkflow.id);
      const { updateWorkflow } = useNoCodeStore.getState();

      // Update the current workflow in the store with ReactFlow state
      const { loadWorkflow } = useNoCodeStore.getState();
      const updatedWorkflow = {
        ...currentWorkflow,
        nodes: nodes,
        edges: edges,
        updatedAt: new Date(),
        hasUnsavedChanges: true
      };
      loadWorkflow(updatedWorkflow);
    }
  }, [nodes, edges, currentWorkflow?.id]);

  // Run validation when workflow changes
  useEffect(() => {
    if (nodes.length > 0 || edges.length > 0) {
      const result = validateWorkflow(nodes, edges);
      setValidationResult(result);
      const optimizations = getWorkflowOptimizations(nodes, edges);
      setOptimizationSuggestions(optimizations);
    } else {
      setValidationResult(null);
      setOptimizationSuggestions([]);
    }
  }, [nodes, edges]);

  // Validate connection before ReactFlow attempts to create it
  const isValidConnection = useCallback(
    (connection: Connection) => {
      // Find source and target nodes for validation
      const sourceNode = nodes.find((n) => n.id === connection.source);
      const targetNode = nodes.find((n) => n.id === connection.target);

      if (!sourceNode || !targetNode) {
        console.warn("Source or target node not found for validation");
        return false;
      }

      // For technical indicators, check if the handle should exist based on the indicator type
      if (sourceNode.type === "technicalIndicator" && connection.sourceHandle) {
        const indicator = sourceNode.data?.parameters?.indicator;
        console.log(
          `🔍 Checking handle ${connection.sourceHandle} for indicator ${indicator}`,
        );

        // List of valid handles for each indicator (full handle IDs)
        const validHandles: Record<string, string[]> = {
          ADX: ["adx-output", "di_plus-output", "di_minus-output"],
          BB: ["upper-output", "middle-output", "lower-output", "width-output"],
          MACD: ["macd-output", "signal-output", "histogram-output"],
          STOCH: ["k-output", "d-output"],
          Stochastic: ["k-output", "d-output"],
        };

        const expectedHandles = validHandles[indicator] || [
          "value-output",
          "signal-output",
        ];
        if (!expectedHandles.includes(connection.sourceHandle)) {
          console.warn(
            `Handle ${connection.sourceHandle} not valid for indicator ${indicator}`,
          );
          return false;
        }
      }

      // Validate connection using connection manager
      const validation = connectionManager.validateConnection(
        sourceNode,
        connection.sourceHandle || "default",
        targetNode,
        connection.targetHandle || "default",
      );

      if (!validation.valid) {
        console.warn("Invalid connection attempt:", validation.reason);
        return false;
      }

      return true;
    },
    [nodes],
  );

  const onConnect = useCallback(
    (params: Connection) => {
      console.log("🔗 Creating connection:", params);

      // Find source and target nodes for validation
      const sourceNode = nodes.find((n) => n.id === params.source);
      const targetNode = nodes.find((n) => n.id === params.target);

      if (!sourceNode || !targetNode) {
        console.warn("Source or target node not found");
        return;
      }

      // Validate connection using connection manager
      const validation = connectionManager.validateConnection(
        sourceNode,
        params.sourceHandle || "default",
        targetNode,
        params.targetHandle || "default",
      );

      if (!validation.valid) {
        console.warn("Invalid connection:", validation.reason);
        return;
      }

      // Create the edge with enhanced styling
      const newEdge: Edge = {
        id: `${params.source}-${params.target}-${Date.now()}`,
        source: params.source!,
        target: params.target!,
        sourceHandle: params.sourceHandle,
        targetHandle: params.targetHandle,
        type: "smart",
        markerEnd: { type: MarkerType.ArrowClosed },
        ...connectionManager.getConnectionStyle(validation.rule),
        animated: validation.rule?.dataType === "signal",
        data: {
          rule: validation.rule,
          sourceNode,
          targetNode,
        },
      };

      // Create connection config and add to manager
      connectionManager.createConnection(newEdge, validation.rule);

      // Add edge to ReactFlow state
      setEdges((eds) => [...eds, newEdge]);
    },
    [setEdges, nodes],
  );

  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      onNodeSelect(node.id);
    },
    [onNodeSelect],
  );

  const onNodeDoubleClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      console.log("Double click on node:", node.id); // Debug log
      setModalSelectedNode(node.id);
      setShowConfigModal(true);
      onNodeSelect(node.id);
    },
    [onNodeSelect],
  );

  const handleCloseModal = useCallback(() => {
    setIsClosingModal(true);
    // Wait for exit animation to complete before hiding modal
    setTimeout(() => {
      setShowConfigModal(false);
      setModalSelectedNode(null);
      setIsClosingModal(false);
    }, 200); // Match animation duration
  }, []);

  const onPaneClick = useCallback(() => {
    onNodeSelect(null);
  }, [onNodeSelect]);

  const onEdgeClick = useCallback((event: React.MouseEvent, edge: Edge) => {
    console.log("🔗 Edge clicked:", edge.id);
    event.stopPropagation();
  }, []);

  // Handle node changes - let ReactFlow manage dragging, sync to store on end
  const handleNodesChange = useCallback(
    (changes: any) => {
      console.log("🔄 ReactFlow node changes:", changes);

      // Let ReactFlow handle its own state changes
      onNodesChange(changes);

      // Sync to store only when drag ends or nodes are removed/added
      const needsSync = changes.some(
        (change: any) =>
          (change.type === "position" && change.dragging === false) ||
          change.type === "remove" ||
          change.type === "add",
      );

      if (needsSync) {
        setTimeout(() => {
          console.log("📍 Syncing node changes to store");
          updateWorkflow({ nodes, edges });
        }, 100);
      }
    },
    [onNodesChange, updateWorkflow, nodes, edges],
  );

  const handleEdgesChange = useCallback(
    (changes: any) => {
      console.log("🔄 ReactFlow edge changes:", changes);

      // Let ReactFlow handle its own state changes
      onEdgesChange(changes);

      // Sync to store after edge changes (but not for every selection change)
      const needsSync = changes.some(
        (change: any) => change.type === "remove" || change.type === "add",
      );

      if (needsSync) {
        setTimeout(() => {
          console.log("📍 Syncing edge changes to store");
          updateWorkflow({ nodes, edges });
        }, 100);
      }
    },
    [onEdgesChange, updateWorkflow, nodes, edges],
  );

  // Handle dropping nodes from the component library
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      event.stopPropagation();
      console.log("📦 Drop event triggered"); // Debug log

      const type =
        event.dataTransfer.getData("application/reactflow") ||
        event.dataTransfer.getData("text/plain");
      const label = event.dataTransfer.getData("application/reactflow-label");

      console.log("📦 Drop data:", { type, label }); // Debug log

      if (!type) {
        console.log(
          "No type found in dataTransfer, available types:",
          event.dataTransfer.types,
        );
        return;
      }

      try {
        // Use ReactFlow's screenToFlowPosition for accurate positioning
        const position = screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });

        const nodeId = `${type}-${Date.now()}`;
        const newNode: Node = {
          id: nodeId,
          type,
          position,
          data: {
            label: label || `${type} Node`,
            parameters: getDefaultParameters(type),
          },
        };

        console.log("Creating new node:", newNode); // Debug log

        // Add node to ReactFlow state
        setNodes((nds) => nds.concat(newNode));

        setIsDragOver(false);

        // Auto-select the new node
        onNodeSelect(nodeId);
        console.log("Node creation completed successfully"); // Debug log
      } catch (error) {
        console.error("Error creating node:", error); // Debug log
      }
    },
    [screenToFlowPosition, setNodes, onNodeSelect],
  );

  const getDefaultParameters = (nodeType: string) => {
    switch (nodeType) {
      case "technicalIndicator":
        return {
          indicatorCategory: "trend",
          indicator: "SMA",
          period: 20,
          source: "close",
          smoothing: 0.2,
          multiplier: 2.0,
          outputType: "main",
        };
      case "condition":
        return {
          conditionType: "comparison",
          condition: "greater_than",
          value: 0,
          lookback: 1,
          sensitivity: 1.0,
          confirmationBars: 0,
        };
      case "action":
        return {
          actionCategory: "entry",
          action: "buy",
          quantity: 10,
          order_type: "market",
          positionSizing: "percentage",
          stop_loss: 2.0,
          take_profit: 4.0,
          conditional_execution: false,
        };
      case "dataSource":
        return {
          symbol: "AAPL",
          timeframe: "1h",
          bars: 1000,
          dataSource: "system",
          assetClass: "stocks",
        };
      case "customDataset":
        return {
          fileName: "No file uploaded",
          dateColumn: "Date",
          openColumn: "Open",
          highColumn: "High",
          lowColumn: "Low",
          closeColumn: "Close",
          volumeColumn: "Volume",
          normalization: "none",
          missingValues: "forward_fill",
          validateData: true,
        };
      case "logic":
        return { operation: "AND", inputs: 2 };
      case "risk":
        return {
          riskCategory: "position",
          riskType: "position_size",
          riskLevel: 2,
          maxLoss: 2.0,
          positionSize: 5.0,
          portfolioHeat: 20,
          emergencyAction: "alert_only",
        };
      default:
        return {};
    }
  };

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = "move";
    setIsDragOver(true);
  }, []);

  const onDragEnter = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragOver(true);
  }, []);

  const onDragLeave = useCallback((event: React.DragEvent) => {
    // Only set to false if we're leaving the main container
    if (!event.currentTarget.contains(event.relatedTarget as Element)) {
      console.log("Drag leave canvas"); // Debug log
      setIsDragOver(false);
    }
  }, []);

  const getValidationIcon = () => {
    if (!validationResult) return null;

    if (validationResult.errors.length > 0) {
      return <AlertTriangle className="h-4 w-4 text-red-500" />;
    } else if (validationResult.warnings.length > 0) {
      return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    } else {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
  };

  const getValidationStatus = () => {
    if (!validationResult) return "No validation";

    if (validationResult.errors.length > 0) {
      return `${validationResult.errors.length} error${validationResult.errors.length > 1 ? "s" : ""}`;
    } else if (validationResult.warnings.length > 0) {
      return `${validationResult.warnings.length} warning${validationResult.warnings.length > 1 ? "s" : ""}`;
    } else {
      return "Valid workflow";
    }
  };

  const handleSaveWorkflow = useCallback(async () => {
    try {
      if (!currentWorkflow) {
        toast({
          title: "Error",
          description: "No workflow to save",
          variant: "destructive",
        });
        return;
      }

      console.log("🔍 [DEBUG] Saving workflow to backend:", {
        workflowId: currentWorkflow.id,
        workflowName: currentWorkflow.name,
        nodesCount: nodes.length,
        edgesCount: edges.length
      });

      // Prepare workflow data for backend
      const workflowDataForAPI = {
        name: currentWorkflow.name,
        description: currentWorkflow.description || "",
        workflow_data: {
          nodes: nodes,
          edges: edges
        },
        category: "custom",
        execution_mode: "backtest",
      };

      let savedWorkflow;

      if (currentWorkflow.id === 'default') {
        // Create new workflow
        console.log("🔍 [DEBUG] Creating new workflow...");
        savedWorkflow = await noCodeApiClient.createWorkflow(workflowDataForAPI);
        console.log("🔍 [DEBUG] Workflow created:", savedWorkflow);
      } else {
        // Update existing workflow
        console.log("🔍 [DEBUG] Updating existing workflow:", currentWorkflow.id);
        savedWorkflow = await noCodeApiClient.updateWorkflow(currentWorkflow.id, workflowDataForAPI);
        console.log("🔍 [DEBUG] Workflow updated:", savedWorkflow);
      }

      // Update the store with the saved workflow from backend
      const noCodeWorkflow = {
        id: savedWorkflow.uuid,
        name: savedWorkflow.name,
        description: savedWorkflow.description,
        nodes: savedWorkflow.workflow_data.nodes,
        edges: savedWorkflow.workflow_data.edges,
        parameters: {},
        createdAt: savedWorkflow.created_at,
        lastModified: savedWorkflow.updated_at,
        updatedAt: new Date(savedWorkflow.updated_at),
        hasUnsavedChanges: false
      };

      const { loadWorkflow } = useNoCodeStore.getState();
      loadWorkflow(noCodeWorkflow);

      setIsWorkflowSaved(true);

      // Reset save status after delay
      setTimeout(() => setIsWorkflowSaved(false), 3000);

      toast({
        title: "Workflow Saved",
        description: `Successfully saved "${savedWorkflow.name}" with ${nodes.length} nodes and ${edges.length} connections`,
      });

      console.log("🔍 [DEBUG] Workflow saved successfully to backend");
      return savedWorkflow;
    } catch (error) {
      console.error("🔍 [DEBUG] Failed to save workflow:", error);
      toast({
        title: "Error",
        description: "Failed to save workflow. Please try again.",
        variant: "destructive",
      });
      throw error;
    }
  }, [nodes, edges, currentWorkflow]);

  const handleExecuteWorkflow = useCallback(() => {
    // First validate the workflow
    if (!validationResult || validationResult.errors.length > 0) {
      alert("Please fix all validation errors before executing the workflow.");
      return;
    }

    // Save the workflow before execution
    handleSaveWorkflow();

    // Show execution mode selector
    setShowExecutionModal(true);
  }, [validationResult, handleSaveWorkflow]);

  const handleModeSelect = useCallback(
    async (mode: ExecutionMode, config: ExecutionModeConfig) => {
      if (mode !== "strategy" && mode !== "model") {
        console.warn(
          `Execution mode "${mode}" is not yet supported from the editor.`,
        );
        setExecutionStatus("idle");
        setShowExecutionModal(false);
        return;
      }

      try {
        setExecutionStatus("executing");

        const workflowId = currentWorkflow?.id ?? Date.now().toString();

        const result = await noCodeApiClient.setExecutionMode(workflowId, {
          mode,
          config,
        });

        if (mode === "strategy") {
          setExecutionStatus("completed");
          setShowExecutionModal(false);
          console.log("Strategy execution result:", result);
          window.location.href = `/workflows/${workflowId}/results/strategy?executionId=${Date.now()}`;
        } else {
          setExecutionStatus("monitoring");
          setShowExecutionModal(false);
          const trainingJobId = result.training_job_id;
          console.log("Training job created:", result);
          window.location.href = `/workflows/${workflowId}/training/${trainingJobId}?from=execute`;
        }
      } catch (error) {
        console.error("Execution failed:", error);
        setExecutionStatus("failed");
        alert("Failed to execute workflow. Please try again.");
      }
    },
    [currentWorkflow?.id, setExecutionStatus],
  );

  const isWorkflowExecutable = () => {
    return (
      nodes.length > 0 &&
      validationResult &&
      validationResult.errors.length === 0
    );
  };

  const complexityLevel = getComplexityLevel(
    validationResult?.performance?.estimatedComplexity,
  );
  const estimatedDuration = DURATION_PRESETS[complexityLevel];

  const handleApplyOptimization = (action: any) => {
    if (action.type === "CONSOLIDATE_NODES") {
      const { nodesToRemove, nodeToKeep } = action.payload;

      // Re-wire the edges from the removed nodes to the node to keep
      const updatedEdges = edges
        .map((edge) => {
          if (nodesToRemove.includes(edge.source)) {
            return { ...edge, source: nodeToKeep };
          }
          return edge;
        })
        .filter((edge) => !nodesToRemove.includes(edge.target)); // also remove edges going to the removed nodes

      // Filter out duplicate edges
      const uniqueEdges = updatedEdges.filter(
        (edge, index, self) =>
          index ===
          self.findIndex(
            (e) =>
              e.source === edge.source &&
              e.target === edge.target &&
              e.sourceHandle === edge.sourceHandle &&
              e.targetHandle === edge.targetHandle,
          ),
      );

      setEdges(uniqueEdges);

      // Remove the redundant nodes
      setNodes((currentNodes) =>
        currentNodes.filter((n) => !nodesToRemove.includes(n.id)),
      );
    }
  };

  const getExecutionStatusBadge = () => {
    switch (currentExecutionStatus) {
      case "executing":
        return (
          <Badge variant="secondary" className="bg-blue-100 text-blue-800">
            Executing...
          </Badge>
        );
      case "monitoring":
        return (
          <Badge variant="secondary" className="bg-purple-100 text-purple-800">
            Training in Progress
          </Badge>
        );
      case "completed":
        return (
          <Badge variant="secondary" className="bg-green-100 text-green-800">
            Completed
          </Badge>
        );
      case "failed":
        return <Badge variant="destructive">Execution Failed</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="w-full h-full relative" suppressHydrationWarning>
      {/* Breadcrumb Navigation */}
      <div className="absolute top-4 left-4 z-40">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/strategy-hub">Strategy Hub</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink>
                {currentWorkflow?.name || "Workflow Designer"}
              </BreadcrumbLink>
            </BreadcrumbItem>
            {currentExecutionMode && (
              <>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbLink className="capitalize">
                    {currentExecutionMode} Mode
                  </BreadcrumbLink>
                </BreadcrumbItem>
              </>
            )}
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      {/* Execution Status Indicator */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-40">
        {getExecutionStatusBadge()}
      </div>
      {/* Toolbar */}
      <div className="absolute top-4 right-4 z-40 flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleSaveWorkflow}
          disabled={nodes.length === 0}
          className="flex items-center space-x-1"
        >
          <Save className="h-4 w-4" />
          <span>{isWorkflowSaved ? "Saved!" : "Save"}</span>
        </Button>

        <Button
          variant="default"
          size="sm"
          onClick={handleExecuteWorkflow}
          disabled={!isWorkflowExecutable()}
          className="flex items-center space-x-1 bg-blue-600 hover:bg-blue-700"
        >
          <Play className="h-4 w-4" />
          <span>Execute Workflow</span>
        </Button>
      </div>

      {/* Validation Status Bar */}
      {validationResult && (
        <div className="absolute top-4 left-4 z-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 shadow-lg">
          <div className="flex items-center space-x-2">
            {getValidationIcon()}
            <span className="text-sm font-medium">{getValidationStatus()}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowValidationPanel(!showValidationPanel)}
              className="h-6 px-2 text-xs"
            >
              {showValidationPanel ? "Hide" : "Details"}
            </Button>
          </div>

          {/* Performance Metrics */}
          {validationResult.performance && (
            <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
              Complexity: {validationResult.performance.estimatedComplexity} |
              Logic Depth: {validationResult.performance.logicDepth} |
              Indicators: {validationResult.performance.indicatorCount}
            </div>
          )}
        </div>
      )}

      {/* Validation Panel */}
      {showValidationPanel && validationResult && (
        <div className="absolute top-20 left-4 z-40 w-96 max-h-96 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden">
          <div className="p-3 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-sm">Workflow Validation</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowValidationPanel(false)}
                className="h-6 w-6 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="overflow-y-auto max-h-80">
            {/* Errors */}
            {validationResult.errors.length > 0 && (
              <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-red-600 dark:text-red-400 mb-2">
                  Errors ({validationResult.errors.length})
                </h4>
                {validationResult.errors.map((error, index) => (
                  <div
                    key={index}
                    className="mb-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs"
                  >
                    <div className="font-medium text-red-800 dark:text-red-300">
                      {error.message}
                    </div>
                    {error.suggestion && (
                      <div className="text-red-600 dark:text-red-400 mt-1">
                        {error.suggestion}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Warnings */}
            {validationResult.warnings.length > 0 && (
              <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-yellow-600 dark:text-yellow-400 mb-2">
                  Warnings ({validationResult.warnings.length})
                </h4>
                {validationResult.warnings.map((warning, index) => (
                  <div
                    key={index}
                    className="mb-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded text-xs"
                  >
                    <div className="font-medium text-yellow-800 dark:text-yellow-300">
                      {warning.message}
                    </div>
                    {warning.suggestion && (
                      <div className="text-yellow-600 dark:text-yellow-400 mt-1">
                        {warning.suggestion}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Suggestions */}
            {validationResult.suggestions &&
              validationResult.suggestions.length > 0 && (
                <div className="p-3">
                  <h4 className="text-sm font-medium text-blue-600 dark:text-blue-400 mb-2">
                    Suggestions ({validationResult.suggestions.length})
                  </h4>
                  {validationResult.suggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      className="mb-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-xs"
                    >
                      <div className="font-medium text-blue-800 dark:text-blue-300">
                        {suggestion.message}
                      </div>
                      <div className="text-blue-600 dark:text-blue-400 mt-1 capitalize">
                        {suggestion.type} • Priority: {suggestion.priority}
                      </div>
                    </div>
                  ))}
                </div>
              )}

            {/* Optimizations */}
            {optimizationSuggestions.length > 0 && (
              <div className="p-3 border-t border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-green-600 dark:text-green-400 mb-2">
                  Optimizations ({optimizationSuggestions.length})
                </h4>
                {optimizationSuggestions.map((suggestion, index) => (
                  <div
                    key={index}
                    className="mb-2 p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs"
                  >
                    <div className="font-medium text-green-800 dark:text-green-300">
                      {suggestion.message}
                    </div>
                    <div className="text-green-600 dark:text-green-400 mt-1 capitalize">
                      {suggestion.type} • Priority: {suggestion.priority}
                    </div>
                    {suggestion.action && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-2 text-xs h-6 px-2"
                        onClick={() =>
                          handleApplyOptimization(suggestion.action)
                        }
                      >
                        Apply
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {isDragOver && (
        <div className="absolute inset-0 bg-blue-100/20 dark:bg-blue-900/20 border-2 border-dashed border-blue-400 dark:border-blue-600 z-50 flex items-center justify-center pointer-events-none">
          <div className="bg-blue-50 dark:bg-blue-900/50 px-4 py-2 rounded-lg border border-blue-200 dark:border-blue-700">
            <span className="text-blue-600 dark:text-blue-400 font-medium">
              Drop component here
            </span>
          </div>
        </div>
      )}

      {/* Empty state with instructions */}
      {nodes.length === 0 && !isDragOver && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center space-y-3 max-w-md">
            <h3 className="text-lg font-medium text-muted-foreground">
              Start Building Your Strategy
            </h3>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>• Drag components from the left panel to create nodes</p>
              <p>
                • Connect nodes by dragging from output handles to input handles
              </p>
              <p>
                • Select connections and press Delete/Backspace to remove them
              </p>
              <p>• Double-click nodes to configure their settings</p>
            </div>
          </div>
        </div>
      )}

      <div
        className="w-full h-full"
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragEnter={onDragEnter}
        onDragLeave={onDragLeave}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onNodeDoubleClick={onNodeDoubleClick}
          onPaneClick={onPaneClick}
          onEdgeClick={onEdgeClick}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          className="bg-background dark:bg-background"
          minZoom={0.1}
          maxZoom={2}
          defaultViewport={{ x: 0, y: 0, zoom: 1 }}
          suppressHydrationWarning
          deleteKeyCode={["Delete", "Backspace"]}
          multiSelectionKeyCode={["Meta", "Shift"]}
          selectionKeyCode={null}
          defaultEdgeOptions={{
            type: "default",
            markerEnd: { type: MarkerType.ArrowClosed },
            style: { strokeWidth: 2, stroke: "#6B7280" },
          }}
        >
          <Controls className="dark:bg-background dark:border-border" />
          <MiniMap
            className="dark:bg-background dark:border-border"
            nodeColor={(node) => {
              switch (node.type) {
                case "dataSource":
                  return "#8B5CF6";
                case "technicalIndicator":
                  return "#3B82F6";
                case "condition":
                  return "#F59E0B";
                case "action":
                  return "#10B981";
                default:
                  return "#6B7280";
              }
            }}
          />
          <Background
            variant={BackgroundVariant.Dots}
            gap={12}
            size={1}
            className="dark:bg-background"
          />
        </ReactFlow>
      </div>

      {/* Configuration Modal */}
      {showConfigModal && modalSelectedNode && (
        <div
          className={`fixed inset-0 z-50 flex items-center justify-center ${
            isClosingModal
              ? "animate-out fade-out-0 duration-200"
              : "animate-in fade-in-0 duration-200"
          }`}
        >
          {/* Blur Background Overlay */}
          <div
            className={`absolute inset-0 bg-black/30 backdrop-blur-sm ${
              isClosingModal
                ? "animate-out fade-out-0 duration-200"
                : "animate-in fade-in-0 duration-200"
            }`}
            onClick={handleCloseModal}
          />

          {/* Modal Content */}
          <div
            className={`relative bg-white dark:bg-gray-900 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 w-[700px] max-w-[95vw] max-h-[95vh] overflow-hidden ${
              isClosingModal
                ? "animate-out zoom-out-95 slide-out-to-bottom-2 duration-200"
                : "animate-in zoom-in-95 slide-in-from-bottom-2 duration-200"
            }`}
          >
            {/* Modal Body */}
            <div className="overflow-y-auto max-h-[calc(95vh-80px)] p-1">
              <ConfigurationPanel
                selectedNode={modalSelectedNode}
                onNodeSelect={(nodeId) => {
                  if (nodeId) {
                    setModalSelectedNode(nodeId);
                    onNodeSelect(nodeId);
                  } else {
                    handleCloseModal();
                  }
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Execution Mode Selector Modal */}
      {showExecutionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center animate-in fade-in-0 duration-200">
          {/* Background Overlay */}
          <div
            className="absolute inset-0 bg-black/30 backdrop-blur-sm animate-in fade-in-0 duration-200"
            onClick={() => setShowExecutionModal(false)}
          />

          {/* Modal Content */}
          <div className="relative bg-white dark:bg-gray-900 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 w-[95vw] max-w-6xl max-h-[95vh] overflow-hidden animate-in zoom-in-95 slide-in-from-bottom-2 duration-200">
            {/* Modal Header */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Execute Workflow</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowExecutionModal(false)}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="overflow-y-auto max-h-[calc(95vh-120px)] p-6">
              <ExecutionModeSelector
                workflowId={currentWorkflow?.id ?? Date.now().toString()}
                workflowName={currentWorkflow?.name || "Untitled Workflow"}
                workflowComplexity={complexityLevel}
                onModeSelect={handleModeSelect}
                onCancel={() => setShowExecutionModal(false)}
                estimatedDuration={estimatedDuration}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function NoCodeWorkflowEditor(props: NoCodeWorkflowEditorProps) {
  return (
    <ReactFlowProvider>
      <NoCodeWorkflowEditorInner {...props} />
    </ReactFlowProvider>
  );
}

export function NoCodeWorkflowEditorWrapper(props: NoCodeWorkflowEditorProps) {
  return <NoCodeWorkflowEditor {...props} />;
}
