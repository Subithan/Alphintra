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
      targetHandle: 'threshold-input',
      dataType: 'numeric',
      condition: {
        type: 'threshold',
        parameters: { sourceIndicator: 'BB' }
      },
      label: 'Upper Band',
      description: 'Uses Bollinger Band upper band as threshold'
    });

    this.addRule({
      id: 'bb-lower-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'lower-output',
      targetHandle: 'threshold-input',
      dataType: 'numeric',
      condition: {
        type: 'threshold',
        parameters: { sourceIndicator: 'BB' }
      },
      label: 'Lower Band',
      description: 'Uses Bollinger Band lower band as threshold'
    });

    // MACD specific connections
    this.addRule({
      id: 'macd-histogram-to-condition',
      sourceType: 'technicalIndicator',
      targetType: 'condition',
      sourceHandle: 'histogram-output',
      targetHandle: 'data-input',
      dataType: 'numeric',
      transformation: {
        type: 'filter',
        parameters: { threshold: 0 }
      },
      label: 'MACD Histogram',
      description: 'MACD histogram for momentum analysis'
    });

    // Condition to Action connections
    this.addRule({
      id: 'condition-to-action',
      sourceType: 'condition',
      targetType: 'action',
      sourceHandle: 'signal-output',
      targetHandle: 'trigger-input',
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

    this.addRule({
      id: 'logic-to-action',
      sourceType: 'logic',
      targetType: 'action',
      sourceHandle: 'output',
      targetHandle: 'trigger-input',
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