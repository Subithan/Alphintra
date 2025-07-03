// No-Code Components Index
// Central exports for all no-code workflow components

// Main Components
export { WorkflowBuilder } from './WorkflowBuilder';
export { WorkflowList } from './WorkflowList';
export { ComponentPalette } from './ComponentPalette';
export { NodePropertiesPanel } from './NodePropertiesPanel';
export { WorkflowToolbar } from './WorkflowToolbar';
export { ExecutionDashboard } from './ExecutionDashboard';
export { TemplateGallery } from './TemplateGallery';

// Node Types
export * from './nodes';

// Edge Types
export * from './edges';

// Re-export commonly used types
export type { NoCodeWorkflow, NoCodeState } from '../../lib/stores/no-code-store';
export type { 
  Workflow, 
  WorkflowCreate, 
  WorkflowUpdate,
  WorkflowData,
  WorkflowNode,
  WorkflowEdge,
  Execution,
  ExecutionConfig,
  Component,
  Template 
} from '../../lib/api/no-code-api';

// Component collection for easy access
export const NoCodeComponents = {
  WorkflowBuilder,
  WorkflowList,
  ComponentPalette,
  NodePropertiesPanel,
  WorkflowToolbar,
  ExecutionDashboard,
  TemplateGallery,
} as const;