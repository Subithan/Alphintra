// Common types for node configurations

export interface ConfigFieldOption {
  value: string;
  label: string;
  category?: string;
}

export interface BaseConfigField {
  label: string;
  description: string;
  default?: any;
}

export interface NumberConfigField extends BaseConfigField {
  type: 'number';
  min?: number;
  max?: number;
  step?: number;
}

export interface SelectConfigField extends BaseConfigField {
  type: 'select';
  options: ConfigFieldOption[];
}

export interface BooleanConfigField extends BaseConfigField {
  type: 'boolean';
}

export interface RangeConfigField extends BaseConfigField {
  type: 'range';
  min: number;
  max: number;
  step: number;
}

export interface TextConfigField extends BaseConfigField {
  type: 'text';
  placeholder?: string;
}

export type ConfigField = 
  | NumberConfigField 
  | SelectConfigField 
  | BooleanConfigField 
  | RangeConfigField 
  | TextConfigField;

export type NodeConfigFields = Record<string, ConfigField>;

export interface NodeConfigResult {
  fields: NodeConfigFields;
  shouldShowField?: (key: string, config: ConfigField, params: Record<string, any>) => boolean;
}

// Common field validation function type
export type FieldValidator = (params: Record<string, any>) => string[];

// Common field groups that can be reused
export interface CommonFields {
  period: NumberConfigField;
  source: SelectConfigField;
  smoothing: RangeConfigField;
  timeframe: SelectConfigField;
  symbol: SelectConfigField;
  riskLevel: RangeConfigField;
  positionSize: NumberConfigField;
  maxLoss: NumberConfigField;
  quantity: NumberConfigField;
  stopLoss: NumberConfigField;
  takeProfit: NumberConfigField;
}