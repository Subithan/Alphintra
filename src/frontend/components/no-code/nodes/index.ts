// Custom Node Types for Workflow Builder
// Exports all custom node components

export { TechnicalIndicatorNode } from './TechnicalIndicatorNode';
export { ConditionNode } from './ConditionNode';
export { ActionNode } from './ActionNode';
export { DataSourceNode } from './DataSourceNode';
export { RiskManagementNode } from './RiskManagementNode';
export { OutputNode } from './OutputNode';

export const CustomNodes = {
  TechnicalIndicatorNode: require('./TechnicalIndicatorNode').TechnicalIndicatorNode,
  ConditionNode: require('./ConditionNode').ConditionNode,
  ActionNode: require('./ActionNode').ActionNode,
  DataSourceNode: require('./DataSourceNode').DataSourceNode,
  RiskManagementNode: require('./RiskManagementNode').RiskManagementNode,
  OutputNode: require('./OutputNode').OutputNode,
};