// Node Properties Panel
// Panel for configuring selected node parameters

import React, { useState, useEffect } from 'react';
import { Node } from 'reactflow';

interface NodePropertiesPanelProps {
  selectedNodeId: string | null;
  nodes: Node[];
  onUpdateNode: (nodeId: string, parameters: Record<string, any>) => void;
  readOnly?: boolean;
}

export const NodePropertiesPanel: React.FC<NodePropertiesPanelProps> = ({
  selectedNodeId,
  nodes,
  onUpdateNode,
  readOnly = false,
}) => {
  const [localParameters, setLocalParameters] = useState<Record<string, any>>({});

  const selectedNode = selectedNodeId ? nodes.find(node => node.id === selectedNodeId) : null;

  // Update local parameters when selected node changes
  useEffect(() => {
    if (selectedNode) {
      setLocalParameters(selectedNode.data.parameters || {});
    } else {
      setLocalParameters({});
    }
  }, [selectedNode]);

  // Apply changes to the node
  const handleParameterChange = (key: string, value: any) => {
    const newParameters = { ...localParameters, [key]: value };
    setLocalParameters(newParameters);
    
    if (selectedNodeId && !readOnly) {
      onUpdateNode(selectedNodeId, newParameters);
    }
  };

  // Get parameter schema based on node type
  const getParameterSchema = (nodeType: string) => {
    switch (nodeType) {
      case 'technicalIndicator':
        return [
          {
            key: 'indicator',
            label: 'Indicator Type',
            type: 'select',
            options: [
              { value: 'SMA', label: 'Simple Moving Average' },
              { value: 'EMA', label: 'Exponential Moving Average' },
              { value: 'RSI', label: 'Relative Strength Index' },
              { value: 'MACD', label: 'MACD' },
              { value: 'BollingerBands', label: 'Bollinger Bands' },
              { value: 'Ichimoku', label: 'Ichimoku Cloud' },
              { value: 'VolumeProfile', label: 'Volume Profile' },
              { value: 'MarketStructure', label: 'Market Structure' },
            ],
            default: 'SMA',
          },
          {
            key: 'period',
            label: 'Period',
            type: 'number',
            min: 1,
            max: 200,
            default: 20,
          },
          {
            key: 'source',
            label: 'Price Source',
            type: 'select',
            options: [
              { value: 'close', label: 'Close' },
              { value: 'open', label: 'Open' },
              { value: 'high', label: 'High' },
              { value: 'low', label: 'Low' },
            ],
            default: 'close',
          },
        ];
      
      case 'condition':
        return [
          {
            key: 'conditionType',
            label: 'Condition Type',
            type: 'select',
            options: [
              { value: 'priceAbove', label: 'Price Above' },
              { value: 'priceBelow', label: 'Price Below' },
              { value: 'crossover', label: 'Crossover' },
              { value: 'crossunder', label: 'Crossunder' },
              { value: 'and', label: 'AND Logic' },
              { value: 'or', label: 'OR Logic' },
            ],
            default: 'priceAbove',
          },
          {
            key: 'value',
            label: 'Threshold Value',
            type: 'number',
            default: 0,
          },
          {
            key: 'sensitivity',
            label: 'Sensitivity',
            type: 'range',
            min: 0.1,
            max: 2.0,
            step: 0.1,
            default: 1.0,
          },
        ];
      
      case 'action':
        return [
          {
            key: 'actionType',
            label: 'Action Type',
            type: 'select',
            options: [
              { value: 'buy', label: 'Buy Order' },
              { value: 'sell', label: 'Sell Order' },
              { value: 'closePosition', label: 'Close Position' },
              { value: 'setStopLoss', label: 'Set Stop Loss' },
              { value: 'setTakeProfit', label: 'Set Take Profit' },
            ],
            default: 'buy',
          },
          {
            key: 'quantity',
            label: 'Quantity (%)',
            type: 'range',
            min: 1,
            max: 100,
            step: 1,
            default: 10,
          },
          {
            key: 'orderType',
            label: 'Order Type',
            type: 'select',
            options: [
              { value: 'market', label: 'Market Order' },
              { value: 'limit', label: 'Limit Order' },
              { value: 'stopLimit', label: 'Stop Limit' },
            ],
            default: 'market',
          },
        ];
      
      case 'riskManagement':
        return [
          {
            key: 'riskType',
            label: 'Risk Type',
            type: 'select',
            options: [
              { value: 'positionSize', label: 'Position Sizing' },
              { value: 'portfolioHeat', label: 'Portfolio Heat' },
              { value: 'maxDrawdown', label: 'Max Drawdown' },
            ],
            default: 'positionSize',
          },
          {
            key: 'riskPercentage',
            label: 'Risk Percentage',
            type: 'range',
            min: 0.1,
            max: 10.0,
            step: 0.1,
            default: 2.0,
          },
          {
            key: 'maxRisk',
            label: 'Maximum Risk ($)',
            type: 'number',
            min: 0,
            default: 1000,
          },
        ];
      
      case 'dataSource':
        return [
          {
            key: 'symbol',
            label: 'Symbol',
            type: 'text',
            default: 'BTCUSDT',
          },
          {
            key: 'timeframe',
            label: 'Timeframe',
            type: 'select',
            options: [
              { value: '1m', label: '1 Minute' },
              { value: '5m', label: '5 Minutes' },
              { value: '15m', label: '15 Minutes' },
              { value: '30m', label: '30 Minutes' },
              { value: '1h', label: '1 Hour' },
              { value: '4h', label: '4 Hours' },
              { value: '1d', label: '1 Day' },
            ],
            default: '1h',
          },
        ];
      
      default:
        return [];
    }
  };

  const renderParameterInput = (param: any) => {
    const value = localParameters[param.key] ?? param.default;

    switch (param.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleParameterChange(param.key, e.target.value)}
            disabled={readOnly}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          />
        );
      
      case 'number':
        return (
          <input
            type="number"
            value={value || ''}
            min={param.min}
            max={param.max}
            onChange={(e) => handleParameterChange(param.key, parseFloat(e.target.value) || 0)}
            disabled={readOnly}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          />
        );
      
      case 'range':
        return (
          <div className="space-y-2">
            <input
              type="range"
              value={value || param.default}
              min={param.min}
              max={param.max}
              step={param.step}
              onChange={(e) => handleParameterChange(param.key, parseFloat(e.target.value))}
              disabled={readOnly}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:cursor-not-allowed"
            />
            <div className="text-sm text-gray-600 text-center">{value || param.default}</div>
          </div>
        );
      
      case 'select':
        return (
          <select
            value={value || param.default}
            onChange={(e) => handleParameterChange(param.key, e.target.value)}
            disabled={readOnly}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          >
            {param.options.map((option: any) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );
      
      case 'checkbox':
        return (
          <input
            type="checkbox"
            checked={value || false}
            onChange={(e) => handleParameterChange(param.key, e.target.checked)}
            disabled={readOnly}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 disabled:cursor-not-allowed"
          />
        );
      
      default:
        return (
          <div className="text-sm text-gray-500">Unsupported parameter type</div>
        );
    }
  };

  if (!selectedNode) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Properties</h3>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <svg className="mx-auto h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.122 2.122" />
            </svg>
            <p className="text-lg font-medium mb-2">No Component Selected</p>
            <p className="text-sm">Select a component to configure its properties</p>
          </div>
        </div>
      </div>
    );
  }

  const parameterSchema = getParameterSchema(selectedNode.type || '');

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Properties</h3>
        <p className="text-sm text-gray-500 mt-1">{selectedNode.data.label}</p>
      </div>

      {/* Properties Form */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Basic Properties */}
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Component Name
            </label>
            <input
              type="text"
              value={selectedNode.data.label}
              onChange={(e) => {
                if (!readOnly) {
                  // Update node label
                  // This would need to be handled differently as it's not a parameter
                }
              }}
              disabled={readOnly}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
            />
          </div>
        </div>

        {/* Dynamic Parameters */}
        {parameterSchema.length > 0 && (
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-gray-900 border-b border-gray-200 pb-2">
              Configuration
            </h4>
            {parameterSchema.map((param) => (
              <div key={param.key}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {param.label}
                </label>
                {renderParameterInput(param)}
              </div>
            ))}
          </div>
        )}

        {/* Advanced Settings */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-900 border-b border-gray-200 pb-2">
            Advanced
          </h4>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Component ID
            </label>
            <input
              type="text"
              value={selectedNode.id}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type
            </label>
            <input
              type="text"
              value={selectedNode.type || 'unknown'}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-500"
            />
          </div>
        </div>

        {/* Documentation */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-900 border-b border-gray-200 pb-2">
            Help
          </h4>
          
          <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
            <p className="font-medium text-blue-900 mb-1">Component Usage:</p>
            <p>Configure the parameters above to customize this component's behavior. Changes are applied automatically.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NodePropertiesPanel;