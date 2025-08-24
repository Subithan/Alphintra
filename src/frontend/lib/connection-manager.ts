import { Edge, Node } from 'reactflow';

export interface ConnectionRule {
  id: string;
  sourceType: string;
  targetType: string;
  sourceHandle: string;
  targetHandle: string;
  dataType: string;
  transformation?: {
    type: 'scale' | 'normalize' | 'invert' | 'filter' | 'custom';
    parameters?: Record<string, any>;
  };
  condition?: {
    type: 'always' | 'threshold' | 'signal' | 'custom';
    parameters?: Record<string, any>;
  };
  label?: string;
  description?: string;
}

export interface ConnectionConfig {
  edge: Edge;
  rule?: ConnectionRule;
  transformation?: any;
  condition?: any;
  metadata?: {
    label?: string;
    description?: string;
    color?: string;
    animated?: boolean;
    style?: Record<string, any>;
  };
}

export class ConnectionManager {
  private rules: ConnectionRule[] = [];
  private connections: Map<string, ConnectionConfig> = new Map();

  constructor() {
    this.initializeDefaultRules();
  }

  private initializeDefaultRules(): void {
    // Technical Indicator to Condition connections
    this.addRule({
      id: 'ti-to-condition-value',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'value-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Value Feed',
      description: 'Feeds indicator value to condition'
    });

    this.addRule({
      id: 'ti-to-condition-signal',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'signal-output',
      targetHandle: 'signal-input',
      dataType: 'signal',
      label: 'Signal Feed',
      description: 'Feeds indicator signal to condition'
    });

    // Bollinger Bands specific connections
    this.addRule({
      id: 'bb-upper-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'upper-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'BB Upper Band',
      description: 'Bollinger Band upper band value'
    });

    this.addRule({
      id: 'bb-middle-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'middle-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'BB Middle Line',
      description: 'Bollinger Band middle line (SMA)'
    });

    this.addRule({
      id: 'bb-lower-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'lower-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'BB Lower Band',
      description: 'Bollinger Band lower band value'
    });

    this.addRule({
      id: 'bb-width-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'width-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'BB Width',
      description: 'Bollinger Band width indicator'
    });

    // MACD specific connections
    this.addRule({
      id: 'macd-line-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'macd-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'MACD Line',
      description: 'MACD main line value'
    });

    this.addRule({
      id: 'macd-signal-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'signal-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'MACD Signal',
      description: 'MACD signal line value'
    });

    this.addRule({
      id: 'macd-histogram-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'histogram-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'MACD Histogram',
      description: 'MACD histogram for momentum analysis'
    });

    // Generic output handles to Condition connections
    this.addRule({
      id: 'output-1-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'output-1',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Output 1 to Condition',
      description: 'Use first output for condition evaluation'
    });

    this.addRule({
      id: 'output-2-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'output-2',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Output 2 to Condition',
      description: 'Use second output for condition evaluation'
    });

    this.addRule({
      id: 'output-3-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'output-3',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Output 3 to Condition',
      description: 'Use third output for condition evaluation'
    });

    this.addRule({
      id: 'output-4-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'output-4',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Output 4 to Condition',
      description: 'Use fourth output for condition evaluation'
    });

    // Stochastic specific connections
    this.addRule({
      id: 'stoch-k-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'k-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Stochastic %K',
      description: 'Stochastic %K line value'
    });

    this.addRule({
      id: 'stoch-d-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'd-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Stochastic %D',
      description: 'Stochastic %D line value'
    });

    // Keltner Channels specific connections
    this.addRule({
      id: 'kc-upper-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'upper-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'KC Upper Band',
      description: 'Keltner Channel upper band value'
    });

    this.addRule({
      id: 'kc-middle-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'middle-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'KC Middle Line',
      description: 'Keltner Channel middle line value'
    });

    this.addRule({
      id: 'kc-lower-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'lower-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'KC Lower Band',
      description: 'Keltner Channel lower band value'
    });

    // Donchian Channels specific connections
    this.addRule({
      id: 'dc-upper-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'upper-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'DC Upper Band',
      description: 'Donchian Channel upper band value'
    });

    this.addRule({
      id: 'dc-lower-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'lower-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'DC Lower Band',
      description: 'Donchian Channel lower band value'
    });

    // Aroon specific connections
    this.addRule({
      id: 'aroon-up-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'aroon_up-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Aroon Up',
      description: 'Aroon Up indicator value'
    });

    this.addRule({
      id: 'aroon-down-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'aroon_down-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Aroon Down',
      description: 'Aroon Down indicator value'
    });

    // DMI specific connections
    this.addRule({
      id: 'dmi-plus-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'dmi_plus-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'DMI+',
      description: 'Positive Directional Movement Index'
    });

    this.addRule({
      id: 'dmi-minus-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'dmi_minus-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'DMI-',
      description: 'Negative Directional Movement Index'
    });

    // PPO specific connections
    this.addRule({
      id: 'ppo-line-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'ppo-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'PPO Line',
      description: 'Percentage Price Oscillator line'
    });

    this.addRule({
      id: 'ppo-histogram-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'histogram-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'PPO Histogram',
      description: 'PPO histogram for momentum analysis'
    });

    // TSI specific connections
    this.addRule({
      id: 'tsi-line-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'tsi-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'TSI Line',
      description: 'True Strength Index line'
    });

    // KDJ specific connections
    this.addRule({
      id: 'kdj-k-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'k-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'KDJ %K',
      description: 'KDJ %K line value'
    });

    this.addRule({
      id: 'kdj-d-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'd-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'KDJ %D',
      description: 'KDJ %D line value'
    });

    this.addRule({
      id: 'kdj-j-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'j-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'KDJ %J',
      description: 'KDJ %J line value'
    });

    // Vortex specific connections
    this.addRule({
      id: 'vortex-plus-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'vi_plus-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'VI+',
      description: 'Positive Vortex Indicator'
    });

    this.addRule({
      id: 'vortex-minus-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'vi_minus-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'VI-',
      description: 'Negative Vortex Indicator'
    });

    // Technical Indicator to Technical Indicator connections (for indicator-based indicators)
    this.addRule({
      id: 'ti-value-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'value-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Indicator Chain',
      description: 'Chain technical indicators together'
    });

    this.addRule({
      id: 'ti-signal-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'signal-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Signal Chain',
      description: 'Chain technical indicator signals together'
    });

    // Generic output handles to Technical Indicator connections
    this.addRule({
      id: 'output-1-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'output-1',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Output 1 Chain',
      description: 'Use first output as input to another indicator'
    });

    this.addRule({
      id: 'output-2-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'output-2',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Output 2 Chain',
      description: 'Use second output as input to another indicator'
    });

    this.addRule({
      id: 'output-3-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'output-3',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Output 3 Chain',
      description: 'Use third output as input to another indicator'
    });

    this.addRule({
      id: 'output-4-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'output-4',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Output 4 Chain',
      description: 'Use fourth output as input to another indicator'
    });

    // MACD to Technical Indicator connections
    this.addRule({
      id: 'macd-line-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'macd-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'MACD Chain',
      description: 'Use MACD line as input to another indicator'
    });

    this.addRule({
      id: 'macd-signal-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'signal-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'MACD Signal Chain',
      description: 'Use MACD signal as input to another indicator'
    });

    this.addRule({
      id: 'macd-histogram-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'histogram-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'MACD Histogram Chain',
      description: 'Use MACD histogram as input to another indicator'
    });

    // Bollinger Bands to Technical Indicator connections
    this.addRule({
      id: 'bb-upper-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'upper-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'BB Upper Chain',
      description: 'Use BB upper band as input to another indicator'
    });

    this.addRule({
      id: 'bb-middle-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'middle-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'BB Middle Chain',
      description: 'Use BB middle line as input to another indicator'
    });

    this.addRule({
      id: 'bb-lower-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'lower-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'BB Lower Chain',
      description: 'Use BB lower band as input to another indicator'
    });

    this.addRule({
      id: 'bb-width-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'width-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'BB Width Chain',
      description: 'Use BB width as input to another indicator'
    });

    // Stochastic to Technical Indicator connections
    this.addRule({
      id: 'stoch-k-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'k-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Stoch %K Chain',
      description: 'Use Stochastic %K as input to another indicator'
    });

    this.addRule({
      id: 'stoch-d-to-ti',
      sourceType: 'technicalIndicator',
      targetType: 'technicalIndicator',
      sourceHandle: 'd-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Stoch %D Chain',
      description: 'Use Stochastic %D as input to another indicator'
    });

    // Multi-output to Action connections
    this.addRule({
      id: 'bb-upper-to-action',
      sourceType: 'technicalIndicator',
      targetType: 'action',
      sourceHandle: 'upper-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'BB Upper to Action',
      description: 'Use Bollinger Band upper band for action trigger'
    });

    this.addRule({
      id: 'bb-lower-to-action',
      sourceType: 'technicalIndicator',
      targetType: 'action',
      sourceHandle: 'lower-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'BB Lower to Action',
      description: 'Use Bollinger Band lower band for action trigger'
    });

    this.addRule({
      id: 'macd-histogram-to-action',
      sourceType: 'technicalIndicator',
      targetType: 'action',
      sourceHandle: 'histogram-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'MACD Histogram to Action',
      description: 'Use MACD histogram for action trigger'
    });

    this.addRule({
      id: 'adx-to-action',
      sourceType: 'technicalIndicator',
      targetType: 'action',
      sourceHandle: 'adx-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'ADX to Action',
      description: 'Use ADX strength for action trigger'
    });

    this.addRule({
      id: 'stoch-k-to-action',
      sourceType: 'technicalIndicator',
      targetType: 'action',
      sourceHandle: 'k-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'Stochastic %K to Action',
      description: 'Use Stochastic %K for action trigger'
    });

    // Multi-output to Risk Management connections
    this.addRule({
      id: 'bb-width-to-risk',
      sourceType: 'technicalIndicator',
      targetType: 'risk',
      sourceHandle: 'width-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'BB Width to Risk',
      description: 'Use Bollinger Band width for volatility-based risk management'
    });

    this.addRule({
      id: 'adx-to-risk',
      sourceType: 'technicalIndicator',
      targetType: 'risk',
      sourceHandle: 'adx-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      label: 'ADX to Risk',
      description: 'Use ADX trend strength for risk assessment'
    });

    // Condition to Action connections
    this.addRule({
      id: 'condition-to-action',
      sourceType: 'condition',
      targetType: 'action',
      sourceHandle: 'signal-output',
      targetHandle: 'signal-input',
      dataType: 'signal',
      label: 'Trigger Signal',
      description: 'Triggers action when condition is met'
    });

    // Data source connections
    this.addRule({
      id: 'data-to-indicator',
      sourceType: 'dataSource',
      targetType: 'technicalIndicator',
      sourceHandle: 'data-output',
      targetHandle: 'data-input',
      dataType: 'ohlcv',
      label: 'Market Data',
      description: 'Feeds market data to technical indicator'
    });

    this.addRule({
      id: 'custom-data-to-indicator',
      sourceType: 'customDataset',
      targetType: 'technicalIndicator',
      sourceHandle: 'data-output',
      targetHandle: 'data-input',
      dataType: 'ohlcv',
      transformation: {
        type: 'normalize',
        parameters: { method: 'minmax' }
      },
      label: 'Custom Data',
      description: 'Feeds custom dataset to technical indicator'
    });

    // Risk management connections
    this.addRule({
      id: 'action-to-risk',
      sourceType: 'action',
      targetType: 'risk',
      sourceHandle: 'execution-output',
      targetHandle: 'monitor-input',
      dataType: 'execution',
      label: 'Risk Monitor',
      description: 'Monitors action execution for risk management'
    });

    // Logic gate connections
    this.addRule({
      id: 'condition-to-logic',
      sourceType: 'condition',
      targetType: 'logic',
      sourceHandle: 'signal-output',
      targetHandle: 'input',
      dataType: 'signal',
      label: 'Logic Input',
      description: 'Condition signal to logic gate'
    });

    // Condition to Logic specific input handles
    this.addRule({
      id: 'condition-to-logic-input-0',
      sourceType: 'condition',
      targetType: 'logic',
      sourceHandle: 'signal-output',
      targetHandle: 'input-0',
      dataType: 'signal',
      label: 'Logic Input 1',
      description: 'Condition signal to logic gate input 1'
    });

    this.addRule({
      id: 'condition-to-logic-input-1',
      sourceType: 'condition',
      targetType: 'logic',
      sourceHandle: 'signal-output',
      targetHandle: 'input-1',
      dataType: 'signal',
      label: 'Logic Input 2',
      description: 'Condition signal to logic gate input 2'
    });

    this.addRule({
      id: 'condition-to-logic-input-2',
      sourceType: 'condition',
      targetType: 'logic',
      sourceHandle: 'signal-output',
      targetHandle: 'input-2',
      dataType: 'signal',
      label: 'Logic Input 3',
      description: 'Condition signal to logic gate input 3'
    });

    this.addRule({
      id: 'condition-to-logic-input-3',
      sourceType: 'condition',
      targetType: 'logic',
      sourceHandle: 'signal-output',
      targetHandle: 'input-3',
      dataType: 'signal',
      label: 'Logic Input 4',
      description: 'Condition signal to logic gate input 4'
    });

    // Logic to Logic connections (for nested logic operations)
    this.addRule({
      id: 'logic-to-logic-input-0',
      sourceType: 'logic',
      targetType: 'logic',
      sourceHandle: 'output',
      targetHandle: 'input-0',
      dataType: 'signal',
      label: 'Logic Chain Input 1',
      description: 'Connect logic gate output to another logic gate input 1'
    });

    this.addRule({
      id: 'logic-to-logic-input-1',
      sourceType: 'logic',
      targetType: 'logic',
      sourceHandle: 'output',
      targetHandle: 'input-1',
      dataType: 'signal',
      label: 'Logic Chain Input 2',
      description: 'Connect logic gate output to another logic gate input 2'
    });

    this.addRule({
      id: 'logic-to-logic-input-2',
      sourceType: 'logic',
      targetType: 'logic',
      sourceHandle: 'output',
      targetHandle: 'input-2',
      dataType: 'signal',
      label: 'Logic Chain Input 3',
      description: 'Connect logic gate output to another logic gate input 3'
    });

    this.addRule({
      id: 'logic-to-logic-input-3',
      sourceType: 'logic',
      targetType: 'logic',
      sourceHandle: 'output',
      targetHandle: 'input-3',
      dataType: 'signal',
      label: 'Logic Chain Input 4',
      description: 'Connect logic gate output to another logic gate input 4'
    });

    this.addRule({
      id: 'logic-to-action',
      sourceType: 'logic',
      targetType: 'action',
      sourceHandle: 'output',
      targetHandle: 'signal-input',
      dataType: 'signal',
      label: 'Logic Output',
      description: 'Logic gate result triggers action'
    });
  }

  addRule(rule: ConnectionRule): void {
    this.rules.push(rule);
  }

  removeRule(ruleId: string): void {
    this.rules = this.rules.filter(rule => rule.id !== ruleId);
  }

  getValidConnectionsForHandle(
    sourceNode: Node,
    sourceHandle: string,
    targetNode: Node,
    targetHandle: string
  ): ConnectionRule[] {
    return this.rules.filter(rule =>
      rule.sourceType === sourceNode.type &&
      rule.targetType === targetNode.type &&
      rule.sourceHandle === sourceHandle &&
      rule.targetHandle === targetHandle
    );
  }

  validateConnection(
    sourceNode: Node,
    sourceHandle: string,
    targetNode: Node,
    targetHandle: string
  ): { valid: boolean; rule?: ConnectionRule; reason?: string } {
    const validRules = this.getValidConnectionsForHandle(
      sourceNode,
      sourceHandle,
      targetNode,
      targetHandle
    );

    if (validRules.length === 0) {
      return {
        valid: false,
        reason: `No valid connection rule found for ${sourceNode.type}:${sourceHandle} -> ${targetNode.type}:${targetHandle}`
      };
    }

    // Use the first valid rule
    const rule = validRules[0];

    // Check conditions if specified
    if (rule.condition) {
      const conditionMet = this.evaluateCondition(rule.condition, sourceNode, targetNode);
      if (!conditionMet) {
        return {
          valid: false,
          rule,
          reason: 'Connection condition not met'
        };
      }
    }

    return {
      valid: true,
      rule
    };
  }

  private evaluateCondition(
    condition: ConnectionRule['condition'],
    sourceNode: Node,
    targetNode: Node
  ): boolean {
    if (!condition) return true;

    switch (condition.type) {
      case 'always':
        return true;
      
      case 'threshold':
        // Check if source indicator matches condition parameters
        if (condition.parameters?.sourceIndicator) {
          return sourceNode.data.parameters?.indicator === condition.parameters.sourceIndicator;
        }
        return true;
      
      case 'signal':
        // Check signal-based conditions
        return true; // Implement specific signal logic
      
      case 'custom':
        // Implement custom condition logic
        return true;
      
      default:
        return true;
    }
  }

  createConnection(edge: Edge, rule?: ConnectionRule): ConnectionConfig {
    const config: ConnectionConfig = {
      edge,
      rule,
      metadata: {
        label: rule?.label,
        description: rule?.description,
        color: this.getConnectionColor(rule),
        animated: rule?.dataType === 'signal',
        style: this.getConnectionStyle(rule)
      }
    };

    // Apply transformations if specified
    if (rule?.transformation) {
      config.transformation = rule.transformation;
    }

    this.connections.set(edge.id, config);
    return config;
  }

  getConnection(edgeId: string): ConnectionConfig | undefined {
    return this.connections.get(edgeId);
  }

  removeConnection(edgeId: string): void {
    this.connections.delete(edgeId);
  }

  private getConnectionColor(rule?: ConnectionRule): string {
    if (!rule) return '#6B7280';

    switch (rule.dataType) {
      case 'ohlcv':
        return '#3B82F6'; // Blue for market data
      case 'numeric':
        return '#10B981'; // Green for numeric values
      case 'signal':
        return '#F59E0B'; // Orange for signals
      case 'execution':
        return '#EF4444'; // Red for execution data
      default:
        return '#6B7280'; // Gray for unknown
    }
  }

  public getConnectionStyle(rule?: ConnectionRule): Record<string, any> {
    const baseStyle = {
      strokeWidth: 2,
      stroke: this.getConnectionColor(rule)
    };

    if (rule?.dataType === 'signal') {
      return {
        ...baseStyle,
        strokeDasharray: '5,5'
      };
    }

    return baseStyle;
  }

  getAllConnections(): ConnectionConfig[] {
    return Array.from(this.connections.values());
  }

  getConnectionsByType(dataType: string): ConnectionConfig[] {
    return this.getAllConnections().filter(
      config => config.rule?.dataType === dataType
    );
  }

  // Transform data according to connection rules
  transformData(data: any, transformation?: ConnectionRule['transformation']): any {
    if (!transformation) return data;

    switch (transformation.type) {
      case 'scale':
        const scale = transformation.parameters?.scale || 1;
        return Array.isArray(data) ? data.map(v => v * scale) : data * scale;
      
      case 'normalize':
        if (Array.isArray(data)) {
          const min = Math.min(...data);
          const max = Math.max(...data);
          return data.map(v => (v - min) / (max - min));
        }
        return data;
      
      case 'invert':
        return Array.isArray(data) ? data.map(v => -v) : -data;
      
      case 'filter':
        const threshold = transformation.parameters?.threshold || 0;
        if (Array.isArray(data)) {
          return data.filter(v => v > threshold);
        }
        return data > threshold ? data : null;
      
      case 'custom':
        // Implement custom transformation logic
        return data;
      
      default:
        return data;
    }
  }
}

// Global connection manager instance
export const connectionManager = new ConnectionManager();