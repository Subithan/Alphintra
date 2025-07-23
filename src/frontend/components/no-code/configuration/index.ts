// Export all configuration modules
export * from './types';
export * from './commonFields';
export * from './TechnicalIndicatorConfig';
export * from './ConditionConfig';
export * from './ActionConfig';
export * from './DataSourceConfig';
export * from './RiskManagementConfig';
export * from './LogicConfig';

// Main configuration getter function
import { NodeConfigResult } from './types';
import { getTechnicalIndicatorConfig, validateTechnicalIndicatorConfig } from './TechnicalIndicatorConfig';
import { getConditionConfig, validateConditionConfig } from './ConditionConfig';
import { getActionConfig, validateActionConfig } from './ActionConfig';
import { getDataSourceConfig, getCustomDatasetConfig, validateDataSourceConfig, validateCustomDatasetConfig } from './DataSourceConfig';
import { getRiskManagementConfig, validateRiskManagementConfig } from './RiskManagementConfig';
import { getLogicConfig, validateLogicConfig } from './LogicConfig';

export function getNodeConfiguration(nodeType: string): NodeConfigResult {
  switch (nodeType) {
    case 'technicalIndicator':
      return getTechnicalIndicatorConfig();
    
    case 'condition':
      return getConditionConfig();
    
    case 'action':
      return getActionConfig();
    
    case 'dataSource':
      return getDataSourceConfig();
    
    case 'customDataset':
      return getCustomDatasetConfig();
    
    case 'risk':
      return getRiskManagementConfig();
    
    case 'logic':
      return getLogicConfig();
    
    default:
      return { fields: {} };
  }
}

export function validateNodeConfiguration(nodeType: string, params: Record<string, any>): string[] {
  switch (nodeType) {
    case 'technicalIndicator':
      return validateTechnicalIndicatorConfig(params);
    
    case 'condition':
      return validateConditionConfig(params);
    
    case 'action':
      return validateActionConfig(params);
    
    case 'dataSource':
      return validateDataSourceConfig(params);
    
    case 'customDataset':
      return validateCustomDatasetConfig(params);
    
    case 'risk':
      return validateRiskManagementConfig(params);
    
    case 'logic':
      return validateLogicConfig(params);
    
    default:
      return [];
  }
}