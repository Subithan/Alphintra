'use client';

import React, { useState, useEffect } from 'react';
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

interface ConfigurationPanelProps {
  selectedNode: string | null;
  onNodeSelect?: (nodeId: string | null) => void;
}

export function ConfigurationPanel({ selectedNode, onNodeSelect }: ConfigurationPanelProps) {
  const { currentWorkflow, updateNodeParameters, removeNode, duplicateNode } = useNoCodeStore();
  const [localParameters, setLocalParameters] = useState<Record<string, any>>({});
  
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

  // Get the selected node data from both the store and the current workflow
  const selectedNodeData = currentWorkflow?.nodes.find(node => node.id === selectedNode);
  
  console.log('ConfigurationPanel:', { selectedNode, selectedNodeData, currentWorkflow }); // Debug log

  useEffect(() => {
    if (selectedNodeData) {
      setLocalParameters(selectedNodeData.data.parameters || {});
    } else {
      setLocalParameters({});
    }
  }, [selectedNodeData]);

  const handleParameterChange = (key: string, value: any) => {
    const newParameters = { ...localParameters, [key]: value };
    setLocalParameters(newParameters);
    if (selectedNode) {
      updateNodeParameters(selectedNode, newParameters);
    }
  };

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
            <h3 className="font-medium">No Node Selected</h3>
            <p className="text-sm text-muted-foreground">
              Select a node to configure its parameters
            </p>
          </div>
        </div>
      </div>
    );
  }

  const renderParameterInput = (key: string, config: any) => {
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
        return (
          <div className="space-y-2">
            <Label htmlFor={key}>{config.label}</Label>
            <Select value={value} onValueChange={(val) => handleParameterChange(key, val)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {config.options.map((option: any) => (
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

  const getNodeConfiguration = (nodeType: string) => {
    switch (nodeType) {
      case 'technicalIndicator':
        return {
          indicatorCategory: {
            type: 'select',
            label: 'Indicator Category',
            description: 'Select the category of technical indicator',
            options: [
              { value: 'trend', label: 'Trend Indicators' },
              { value: 'momentum', label: 'Momentum Indicators' },
              { value: 'volatility', label: 'Volatility Indicators' },
              { value: 'volume', label: 'Volume Indicators' },
              { value: 'oscillators', label: 'Oscillators' },
            ],
            default: 'trend'
          },
          indicator: {
            type: 'select',
            label: 'Indicator Type',
            description: 'Select the technical indicator to calculate',
            options: [
              // Trend Indicators
              { value: 'SMA', label: 'Simple Moving Average', category: 'trend' },
              { value: 'EMA', label: 'Exponential Moving Average', category: 'trend' },
              { value: 'WMA', label: 'Weighted Moving Average', category: 'trend' },
              { value: 'VWMA', label: 'Volume Weighted Moving Average', category: 'trend' },
              { value: 'HMA', label: 'Hull Moving Average', category: 'trend' },
              { value: 'DEMA', label: 'Double Exponential Moving Average', category: 'trend' },
              { value: 'TEMA', label: 'Triple Exponential Moving Average', category: 'trend' },
              { value: 'ZLEMA', label: 'Zero Lag Exponential Moving Average', category: 'trend' },
              { value: 'ALMA', label: 'Arnaud Legoux Moving Average', category: 'trend' },
              { value: 'KAMA', label: 'Kaufman Adaptive Moving Average', category: 'trend' },
              { value: 'MAMA', label: 'MESA Adaptive Moving Average', category: 'trend' },
              { value: 'T3', label: 'T3 Moving Average', category: 'trend' },
              { value: 'FRAMA', label: 'Fractal Adaptive Moving Average', category: 'trend' },
              { value: 'TRIMA', label: 'Triangular Moving Average', category: 'trend' },
              { value: 'VIDYA', label: 'Variable Index Dynamic Average', category: 'trend' },
              
              // Momentum Indicators
              { value: 'RSI', label: 'Relative Strength Index', category: 'momentum' },
              { value: 'STOCH', label: 'Stochastic Oscillator', category: 'momentum' },
              { value: 'STOCHRSI', label: 'Stochastic RSI', category: 'momentum' },
              { value: 'WILLIAMS', label: 'Williams %R', category: 'momentum' },
              { value: 'CCI', label: 'Commodity Channel Index', category: 'momentum' },
              { value: 'ROC', label: 'Rate of Change', category: 'momentum' },
              { value: 'MOM', label: 'Momentum', category: 'momentum' },
              { value: 'TSI', label: 'True Strength Index', category: 'momentum' },
              { value: 'UO', label: 'Ultimate Oscillator', category: 'momentum' },
              { value: 'PPO', label: 'Percentage Price Oscillator', category: 'momentum' },
              { value: 'PMO', label: 'Price Momentum Oscillator', category: 'momentum' },
              { value: 'QQE', label: 'Quantitative Qualitative Estimation', category: 'momentum' },
              { value: 'RMI', label: 'Relative Momentum Index', category: 'momentum' },
              { value: 'IFT_RSI', label: 'Inverse Fisher Transform RSI', category: 'momentum' },
              { value: 'LSMA', label: 'Least Squares Moving Average', category: 'momentum' },
              
              // Volatility Indicators
              { value: 'BB', label: 'Bollinger Bands', category: 'volatility' },
              { value: 'ATR', label: 'Average True Range', category: 'volatility' },
              { value: 'KC', label: 'Keltner Channels', category: 'volatility' },
              { value: 'DC', label: 'Donchian Channels', category: 'volatility' },
              { value: 'STDDEV', label: 'Standard Deviation', category: 'volatility' },
              { value: 'VAR', label: 'Variance', category: 'volatility' },
              { value: 'NATR', label: 'Normalized Average True Range', category: 'volatility' },
              { value: 'TRANGE', label: 'True Range', category: 'volatility' },
              { value: 'BBWIDTH', label: 'Bollinger Band Width', category: 'volatility' },
              { value: 'SQUEEZE', label: 'Squeeze Momentum', category: 'volatility' },
              { value: 'UI', label: 'Ulcer Index', category: 'volatility' },
              { value: 'THERMO', label: 'Ehlers Thermal Index', category: 'volatility' },
              { value: 'CHOP', label: 'Choppiness Index', category: 'volatility' },
              
              // Volume Indicators
              { value: 'OBV', label: 'On Balance Volume', category: 'volume' },
              { value: 'VWAP', label: 'Volume Weighted Average Price', category: 'volume' },
              { value: 'AD', label: 'Accumulation/Distribution', category: 'volume' },
              { value: 'CMF', label: 'Chaikin Money Flow', category: 'volume' },
              { value: 'EMV', label: 'Ease of Movement', category: 'volume' },
              { value: 'FI', label: 'Force Index', category: 'volume' },
              { value: 'NVI', label: 'Negative Volume Index', category: 'volume' },
              { value: 'PVI', label: 'Positive Volume Index', category: 'volume' },
              { value: 'PVT', label: 'Price Volume Trend', category: 'volume' },
              { value: 'VROC', label: 'Volume Rate of Change', category: 'volume' },
              { value: 'MFI', label: 'Money Flow Index', category: 'volume' },
              { value: 'VORTEX', label: 'Vortex Indicator', category: 'volume' },
              { value: 'KVO', label: 'Klinger Volume Oscillator', category: 'volume' },
              
              // Oscillators
              { value: 'MACD', label: 'MACD', category: 'oscillators' },
              { value: 'AO', label: 'Awesome Oscillator', category: 'oscillators' },
              { value: 'AC', label: 'Accelerator Oscillator', category: 'oscillators' },
              { value: 'AROON', label: 'Aroon Oscillator', category: 'oscillators' },
              { value: 'BOP', label: 'Balance of Power', category: 'oscillators' },
              { value: 'FISHER', label: 'Fisher Transform', category: 'oscillators' },
              { value: 'INERTIA', label: 'Inertia', category: 'oscillators' },
              { value: 'KDJ', label: 'KDJ', category: 'oscillators' },
              { value: 'PSAR', label: 'Parabolic SAR', category: 'oscillators' },
              { value: 'ADX', label: 'Average Directional Index', category: 'oscillators' },
              { value: 'DMI', label: 'Directional Movement Index', category: 'oscillators' },
              { value: 'DPO', label: 'Detrended Price Oscillator', category: 'oscillators' }
            ],
            default: 'SMA'
          },
          period: {
            type: 'number',
            label: 'Period',
            description: 'Number of periods for calculation',
            min: 1,
            max: 200,
            default: 20
          },
          source: {
            type: 'select',
            label: 'Price Source',
            description: 'Which price to use for calculation',
            options: [
              { value: 'close', label: 'Close' },
              { value: 'open', label: 'Open' },
              { value: 'high', label: 'High' },
              { value: 'low', label: 'Low' },
              { value: 'hl2', label: 'HL2 (High+Low)/2' },
              { value: 'hlc3', label: 'HLC3 (High+Low+Close)/3' },
              { value: 'ohlc4', label: 'OHLC4 (Open+High+Low+Close)/4' },
              { value: 'volume', label: 'Volume' },
            ],
            default: 'close'
          },
          smoothing: {
            type: 'range',
            label: 'Smoothing Factor',
            description: 'Smoothing factor for EMA-based indicators',
            min: 0.1,
            max: 1.0,
            step: 0.1,
            default: 0.2
          },
          multiplier: {
            type: 'number',
            label: 'Multiplier',
            description: 'Multiplier for indicators like Bollinger Bands',
            min: 0.1,
            max: 5.0,
            step: 0.1,
            default: 2.0
          },
          fastPeriod: {
            type: 'number',
            label: 'Fast Period',
            description: 'Fast period for MACD and other dual-period indicators',
            min: 1,
            max: 100,
            default: 12
          },
          slowPeriod: {
            type: 'number',
            label: 'Slow Period',
            description: 'Slow period for MACD and other dual-period indicators',
            min: 1,
            max: 200,
            default: 26
          },
          signalPeriod: {
            type: 'number',
            label: 'Signal Period',
            description: 'Signal line period for MACD',
            min: 1,
            max: 50,
            default: 9
          },
          kPeriod: {
            type: 'number',
            label: '%K Period',
            description: 'Stochastic %K period',
            min: 1,
            max: 100,
            default: 14
          },
          dPeriod: {
            type: 'number',
            label: '%D Period',
            description: 'Stochastic %D period',
            min: 1,
            max: 50,
            default: 3
          },
          slowing: {
            type: 'number',
            label: 'Slowing',
            description: 'Stochastic slowing factor',
            min: 1,
            max: 10,
            default: 3
          },
          acceleration: {
            type: 'number',
            label: 'Acceleration',
            description: 'Parabolic SAR acceleration factor',
            min: 0.01,
            max: 1.0,
            step: 0.01,
            default: 0.02
          },
          maximum: {
            type: 'number',
            label: 'Maximum',
            description: 'Parabolic SAR maximum value',
            min: 0.1,
            max: 1.0,
            step: 0.01,
            default: 0.2
          },
          outputType: {
            type: 'select',
            label: 'Output Type',
            description: 'Which output to use for multi-output indicators',
            options: [
              { value: 'main', label: 'Main Line' },
              { value: 'signal', label: 'Signal Line' },
              { value: 'histogram', label: 'Histogram' },
              { value: 'upper', label: 'Upper Band' },
              { value: 'lower', label: 'Lower Band' },
              { value: 'middle', label: 'Middle Line' },
            ],
            default: 'main'
          }
        };

      case 'condition':
        return {
          conditionType: {
            type: 'select',
            label: 'Condition Category',
            description: 'Category of logical condition',
            options: [
              { value: 'comparison', label: 'Value Comparison' },
              { value: 'crossover', label: 'Crossover Detection' },
              { value: 'trend', label: 'Trend Analysis' },
              { value: 'pattern', label: 'Pattern Recognition' },
              { value: 'timeframe', label: 'Multi-Timeframe' },
            ],
            default: 'comparison'
          },
          condition: {
            type: 'select',
            label: 'Condition Type',
            description: 'Specific condition to evaluate',
            options: [
              // Comparison conditions
              { value: 'greater_than', label: 'Greater Than (>)', category: 'comparison' },
              { value: 'less_than', label: 'Less Than (<)', category: 'comparison' },
              { value: 'equal_to', label: 'Equal To (=)', category: 'comparison' },
              { value: 'not_equal', label: 'Not Equal (!=)', category: 'comparison' },
              { value: 'greater_equal', label: 'Greater or Equal (>=)', category: 'comparison' },
              { value: 'less_equal', label: 'Less or Equal (<=)', category: 'comparison' },
              { value: 'range', label: 'Within Range', category: 'comparison' },
              { value: 'outside_range', label: 'Outside Range', category: 'comparison' },
              { value: 'percentage_change', label: 'Percentage Change', category: 'comparison' },
              
              // Crossover conditions
              { value: 'crossover', label: 'Crossover Above', category: 'crossover' },
              { value: 'crossunder', label: 'Crossover Below', category: 'crossover' },
              { value: 'golden_cross', label: 'Golden Cross (50/200 MA)', category: 'crossover' },
              { value: 'death_cross', label: 'Death Cross (50/200 MA)', category: 'crossover' },
              { value: 'bullish_divergence', label: 'Bullish Divergence', category: 'crossover' },
              { value: 'bearish_divergence', label: 'Bearish Divergence', category: 'crossover' },
              
              // Trend conditions
              { value: 'rising', label: 'Rising Trend', category: 'trend' },
              { value: 'falling', label: 'Falling Trend', category: 'trend' },
              { value: 'sideways', label: 'Sideways Movement', category: 'trend' },
              { value: 'trend_strength', label: 'Trend Strength', category: 'trend' },
              { value: 'momentum_change', label: 'Momentum Change', category: 'trend' },
              
              // Pattern conditions
              { value: 'support_level', label: 'At Support Level', category: 'pattern' },
              { value: 'resistance_level', label: 'At Resistance Level', category: 'pattern' },
              { value: 'breakout_up', label: 'Upward Breakout', category: 'pattern' },
              { value: 'breakout_down', label: 'Downward Breakout', category: 'pattern' },
              { value: 'oversold', label: 'Oversold Condition', category: 'pattern' },
              { value: 'overbought', label: 'Overbought Condition', category: 'pattern' },
              
              // Multi-timeframe conditions
              { value: 'higher_timeframe_trend', label: 'Higher Timeframe Trend', category: 'timeframe' },
              { value: 'multi_tf_alignment', label: 'Multi-TF Alignment', category: 'timeframe' },
              { value: 'weekly_monthly_bias', label: 'Weekly/Monthly Bias', category: 'timeframe' }
            ],
            default: 'greater_than'
          },
          value: {
            type: 'number',
            label: 'Threshold Value',
            description: 'Primary comparison value',
            default: 0
          },
          value2: {
            type: 'number',
            label: 'Secondary Value',
            description: 'Secondary value for range/comparison conditions',
            default: 100
          },
          lookback: {
            type: 'number',
            label: 'Lookback Period',
            description: 'Number of bars to analyze',
            min: 1,
            max: 200,
            default: 1
          },
          sensitivity: {
            type: 'range',
            label: 'Sensitivity',
            description: 'Detection sensitivity (higher = more sensitive)',
            min: 0.1,
            max: 5.0,
            step: 0.1,
            default: 1.0
          },
          confirmationBars: {
            type: 'number',
            label: 'Confirmation Bars',
            description: 'Number of bars to confirm the condition',
            min: 0,
            max: 20,
            default: 0
          },
          percentageThreshold: {
            type: 'number',
            label: 'Percentage Threshold',
            description: 'Percentage threshold for change detection',
            min: 0.1,
            max: 50,
            step: 0.1,
            default: 5.0
          },
          higherTimeframe: {
            type: 'select',
            label: 'Higher Timeframe',
            description: 'Reference timeframe for multi-TF conditions',
            options: [
              { value: '15m', label: '15 Minutes' },
              { value: '1h', label: '1 Hour' },
              { value: '4h', label: '4 Hours' },
              { value: '1d', label: '1 Day' },
              { value: '1w', label: '1 Week' },
              { value: '1M', label: '1 Month' },
            ],
            default: '1h'
          },
          trendStrength: {
            type: 'select',
            label: 'Trend Strength',
            description: 'Required trend strength level',
            options: [
              { value: 'weak', label: 'Weak Trend' },
              { value: 'moderate', label: 'Moderate Trend' },
              { value: 'strong', label: 'Strong Trend' },
              { value: 'very_strong', label: 'Very Strong Trend' },
            ],
            default: 'moderate'
          },
          divergenceType: {
            type: 'select',
            label: 'Divergence Type',
            description: 'Type of divergence to detect',
            options: [
              { value: 'regular', label: 'Regular Divergence' },
              { value: 'hidden', label: 'Hidden Divergence' },
              { value: 'exaggerated', label: 'Exaggerated Divergence' },
            ],
            default: 'regular'
          }
        };

      case 'action':
        return {
          actionCategory: {
            type: 'select',
            label: 'Action Category',
            description: 'Category of trading action',
            options: [
              { value: 'entry', label: 'Position Entry' },
              { value: 'exit', label: 'Position Exit' },
              { value: 'management', label: 'Position Management' },
              { value: 'portfolio', label: 'Portfolio Actions' },
            ],
            default: 'entry'
          },
          action: {
            type: 'select',
            label: 'Action Type',
            description: 'Specific trading action to execute',
            options: [
              // Entry actions
              { value: 'buy', label: 'Buy (Long Entry)', category: 'entry' },
              { value: 'sell', label: 'Sell (Short Entry)', category: 'entry' },
              { value: 'buy_limit', label: 'Buy Limit Entry', category: 'entry' },
              { value: 'sell_limit', label: 'Sell Limit Entry', category: 'entry' },
              { value: 'buy_stop', label: 'Buy Stop Entry', category: 'entry' },
              { value: 'sell_stop', label: 'Sell Stop Entry', category: 'entry' },
              
              // Exit actions
              { value: 'close_long', label: 'Close Long Position', category: 'exit' },
              { value: 'close_short', label: 'Close Short Position', category: 'exit' },
              { value: 'close_all', label: 'Close All Positions', category: 'exit' },
              { value: 'take_profit', label: 'Take Profit', category: 'exit' },
              { value: 'stop_loss', label: 'Stop Loss', category: 'exit' },
              { value: 'trailing_stop', label: 'Trailing Stop', category: 'exit' },
              
              // Management actions
              { value: 'scale_in', label: 'Scale Into Position', category: 'management' },
              { value: 'scale_out', label: 'Scale Out of Position', category: 'management' },
              { value: 'modify_stop', label: 'Modify Stop Loss', category: 'management' },
              { value: 'modify_target', label: 'Modify Take Profit', category: 'management' },
              { value: 'hedge_position', label: 'Hedge Position', category: 'management' },
              
              // Portfolio actions
              { value: 'rebalance', label: 'Portfolio Rebalance', category: 'portfolio' },
              { value: 'risk_off', label: 'Risk Off (Close All)', category: 'portfolio' },
              { value: 'emergency_exit', label: 'Emergency Exit', category: 'portfolio' }
            ],
            default: 'buy'
          },
          order_type: {
            type: 'select',
            label: 'Order Type',
            description: 'Type of order to place',
            options: [
              { value: 'market', label: 'Market Order' },
              { value: 'limit', label: 'Limit Order' },
              { value: 'stop', label: 'Stop Order' },
              { value: 'stop_limit', label: 'Stop Limit Order' },
              { value: 'trailing_stop', label: 'Trailing Stop' },
              { value: 'iceberg', label: 'Iceberg Order' },
              { value: 'twap', label: 'TWAP (Time Weighted)' },
              { value: 'vwap', label: 'VWAP (Volume Weighted)' },
              { value: 'bracket', label: 'Bracket Order' },
              { value: 'oco', label: 'One-Cancels-Other' },
            ],
            default: 'market'
          },
          positionSizing: {
            type: 'select',
            label: 'Position Sizing Method',
            description: 'How to calculate position size',
            options: [
              { value: 'fixed_amount', label: 'Fixed Amount' },
              { value: 'percentage', label: 'Percentage of Portfolio' },
              { value: 'fixed_risk', label: 'Fixed Risk Amount' },
              { value: 'kelly_criterion', label: 'Kelly Criterion' },
              { value: 'volatility_based', label: 'Volatility Based' },
              { value: 'equal_weight', label: 'Equal Weight' },
            ],
            default: 'percentage'
          },
          quantity: {
            type: 'number',
            label: 'Quantity/Amount',
            description: 'Position size (depends on sizing method)',
            min: 0,
            default: 10
          },
          price_offset: {
            type: 'number',
            label: 'Price Offset %',
            description: 'Price offset from current price',
            min: -50,
            max: 50,
            step: 0.1,
            default: 0
          },
          stop_loss: {
            type: 'number',
            label: 'Stop Loss %',
            description: 'Stop loss as percentage from entry',
            min: 0.1,
            max: 50,
            step: 0.1,
            default: 2.0
          },
          take_profit: {
            type: 'number',
            label: 'Take Profit %',
            description: 'Take profit as percentage from entry',
            min: 0.1,
            max: 100,
            step: 0.1,
            default: 4.0
          },
          trailing_distance: {
            type: 'number',
            label: 'Trailing Distance %',
            description: 'Trailing stop distance',
            min: 0.1,
            max: 20,
            step: 0.1,
            default: 1.0
          },
          time_in_force: {
            type: 'select',
            label: 'Time in Force',
            description: 'How long the order remains active',
            options: [
              { value: 'GTC', label: 'Good Till Canceled' },
              { value: 'DAY', label: 'Day Order' },
              { value: 'IOC', label: 'Immediate or Cancel' },
              { value: 'FOK', label: 'Fill or Kill' },
              { value: 'GTD', label: 'Good Till Date' },
              { value: 'ATC', label: 'At The Close' },
              { value: 'ATO', label: 'At The Open' },
            ],
            default: 'GTC'
          },
          execution_algorithm: {
            type: 'select',
            label: 'Execution Algorithm',
            description: 'Algorithm for order execution',
            options: [
              { value: 'standard', label: 'Standard Execution' },
              { value: 'stealth', label: 'Stealth (Hide Size)' },
              { value: 'aggressive', label: 'Aggressive Fill' },
              { value: 'passive', label: 'Passive Fill' },
              { value: 'smart_routing', label: 'Smart Order Routing' },
            ],
            default: 'standard'
          },
          slippage_tolerance: {
            type: 'number',
            label: 'Slippage Tolerance %',
            description: 'Maximum acceptable slippage',
            min: 0.01,
            max: 5.0,
            step: 0.01,
            default: 0.1
          },
          conditional_execution: {
            type: 'boolean',
            label: 'Conditional Execution',
            description: 'Execute only if conditions are met',
            default: false
          }
        };

      case 'dataSource':
        return {
          assetClass: {
            type: 'select',
            label: 'Asset Class',
            description: 'Type of financial instrument',
            options: [
              { value: 'stocks', label: 'Stocks (Equities)' },
              { value: 'crypto', label: 'Cryptocurrency' },
              { value: 'forex', label: 'Foreign Exchange' },
            ],
            default: 'stocks'
          },
          symbol: {
            type: 'select',
            label: 'Symbol',
            description: 'Trading symbol with autocomplete',
            options: [
              // Popular Stocks
              { value: 'AAPL', label: 'AAPL - Apple Inc.' },
              { value: 'GOOGL', label: 'GOOGL - Alphabet Inc.' },
              { value: 'MSFT', label: 'MSFT - Microsoft Corp.' },
              { value: 'AMZN', label: 'AMZN - Amazon.com Inc.' },
              { value: 'TSLA', label: 'TSLA - Tesla Inc.' },
              { value: 'META', label: 'META - Meta Platforms Inc.' },
              { value: 'NVDA', label: 'NVDA - NVIDIA Corp.' },
              { value: 'SPY', label: 'SPY - SPDR S&P 500 ETF' },
              { value: 'QQQ', label: 'QQQ - Invesco QQQ Trust' },
              // Crypto
              { value: 'BTCUSD', label: 'BTCUSD - Bitcoin' },
              { value: 'ETHUSD', label: 'ETHUSD - Ethereum' },
              { value: 'ADAUSD', label: 'ADAUSD - Cardano' },
              { value: 'SOLUSD', label: 'SOLUSD - Solana' },
              { value: 'DOTUSD', label: 'DOTUSD - Polkadot' },
              // Forex
              { value: 'EURUSD', label: 'EURUSD - Euro/US Dollar' },
              { value: 'GBPUSD', label: 'GBPUSD - British Pound/US Dollar' },
              { value: 'USDJPY', label: 'USDJPY - US Dollar/Japanese Yen' },
              { value: 'AUDUSD', label: 'AUDUSD - Australian Dollar/US Dollar' },
              { value: 'USDCAD', label: 'USDCAD - US Dollar/Canadian Dollar' },
            ],
            default: 'AAPL'
          },
          timeframe: {
            type: 'select',
            label: 'Timeframe',
            description: 'Chart timeframe for analysis',
            options: [
              { value: '1m', label: '1 Minute' },
              { value: '5m', label: '5 Minutes' },
              { value: '15m', label: '15 Minutes' },
              { value: '30m', label: '30 Minutes' },
              { value: '1h', label: '1 Hour' },
              { value: '4h', label: '4 Hours' },
              { value: '1d', label: '1 Day' },
              { value: '1w', label: '1 Week' },
              { value: '1M', label: '1 Month' },
            ],
            default: '1h'
          },
          dataSource: {
            type: 'select',
            label: 'Data Source',
            description: 'Choose between system datasets or user upload',
            options: [
              { value: 'system', label: 'System Dataset' },
              { value: 'upload', label: 'Upload Custom Data' },
            ],
            default: 'system'
          },
          bars: {
            type: 'number',
            label: 'Number of Bars',
            description: 'How many historical bars to fetch',
            min: 100,
            max: 50000,
            default: 1000
          },
          startDate: {
            type: 'text',
            label: 'Start Date (Optional)',
            description: 'Start date for historical data (YYYY-MM-DD)',
            placeholder: '2023-01-01'
          },
          endDate: {
            type: 'text',
            label: 'End Date (Optional)',
            description: 'End date for historical data (YYYY-MM-DD)',
            placeholder: '2024-01-01'
          }
        };

      case 'customDataset':
        return {
          fileName: {
            type: 'text',
            label: 'File Name',
            description: 'Name of the uploaded file',
            placeholder: 'my_dataset.csv',
            default: 'No file uploaded'
          },
          fileUpload: {
            type: 'text',
            label: 'Upload Dataset',
            description: 'Upload CSV or Excel file with OHLCV data',
            placeholder: 'Click to upload file...'
          },
          dateColumn: {
            type: 'select',
            label: 'Date Column',
            description: 'Column containing date/timestamp',
            options: [
              { value: 'Date', label: 'Date' },
              { value: 'Timestamp', label: 'Timestamp' },
              { value: 'DateTime', label: 'DateTime' },
              { value: 'Time', label: 'Time' },
            ],
            default: 'Date'
          },
          openColumn: {
            type: 'select',
            label: 'Open Price Column',
            description: 'Column containing opening prices',
            options: [
              { value: 'Open', label: 'Open' },
              { value: 'open', label: 'open' },
              { value: 'OPEN', label: 'OPEN' },
              { value: 'O', label: 'O' },
            ],
            default: 'Open'
          },
          highColumn: {
            type: 'select',
            label: 'High Price Column',
            description: 'Column containing high prices',
            options: [
              { value: 'High', label: 'High' },
              { value: 'high', label: 'high' },
              { value: 'HIGH', label: 'HIGH' },
              { value: 'H', label: 'H' },
            ],
            default: 'High'
          },
          lowColumn: {
            type: 'select',
            label: 'Low Price Column',
            description: 'Column containing low prices',
            options: [
              { value: 'Low', label: 'Low' },
              { value: 'low', label: 'low' },
              { value: 'LOW', label: 'LOW' },
              { value: 'L', label: 'L' },
            ],
            default: 'Low'
          },
          closeColumn: {
            type: 'select',
            label: 'Close Price Column',
            description: 'Column containing closing prices',
            options: [
              { value: 'Close', label: 'Close' },
              { value: 'close', label: 'close' },
              { value: 'CLOSE', label: 'CLOSE' },
              { value: 'C', label: 'C' },
            ],
            default: 'Close'
          },
          volumeColumn: {
            type: 'select',
            label: 'Volume Column (Optional)',
            description: 'Column containing volume data',
            options: [
              { value: 'Volume', label: 'Volume' },
              { value: 'volume', label: 'volume' },
              { value: 'VOLUME', label: 'VOLUME' },
              { value: 'Vol', label: 'Vol' },
              { value: 'V', label: 'V' },
            ],
            default: 'Volume'
          },
          normalization: {
            type: 'select',
            label: 'Data Normalization',
            description: 'How to normalize the data',
            options: [
              { value: 'none', label: 'No Normalization' },
              { value: 'minmax', label: 'Min-Max Scaling' },
              { value: 'zscore', label: 'Z-Score Normalization' },
              { value: 'percentage', label: 'Percentage Change' },
            ],
            default: 'none'
          },
          missingValues: {
            type: 'select',
            label: 'Missing Value Handling',
            description: 'How to handle missing values',
            options: [
              { value: 'drop', label: 'Drop Missing Rows' },
              { value: 'forward_fill', label: 'Forward Fill' },
              { value: 'backward_fill', label: 'Backward Fill' },
              { value: 'interpolate', label: 'Linear Interpolation' },
              { value: 'zero', label: 'Fill with Zero' },
            ],
            default: 'forward_fill'
          },
          validateData: {
            type: 'boolean',
            label: 'Validate Data Quality',
            description: 'Run data quality checks on upload',
            default: true
          }
        };

      case 'logic':
        return {
          operation: {
            type: 'select',
            label: 'Logic Operation',
            description: 'Type of logical operation',
            options: [
              { value: 'AND', label: 'AND - All inputs must be true' },
              { value: 'OR', label: 'OR - Any input must be true' },
              { value: 'NOT', label: 'NOT - Invert input signal' },
              { value: 'XOR', label: 'XOR - Exclusive OR' },
            ],
            default: 'AND'
          },
          inputs: {
            type: 'number',
            label: 'Number of Inputs',
            description: 'How many inputs to connect',
            min: 1,
            max: 8,
            default: 2
          }
        };

      case 'risk':
        return {
          riskCategory: {
            type: 'select',
            label: 'Risk Category',
            description: 'Category of risk management',
            options: [
              { value: 'position', label: 'Position Level Risk' },
              { value: 'portfolio', label: 'Portfolio Level Risk' },
              { value: 'market', label: 'Market Risk Controls' },
              { value: 'drawdown', label: 'Drawdown Protection' },
              { value: 'exposure', label: 'Exposure Management' },
            ],
            default: 'position'
          },
          riskType: {
            type: 'select',
            label: 'Risk Control Type',
            description: 'Specific risk management control',
            options: [
              // Position level
              { value: 'position_size', label: 'Position Sizing', category: 'position' },
              { value: 'stop_loss', label: 'Stop Loss Management', category: 'position' },
              { value: 'take_profit', label: 'Take Profit Management', category: 'position' },
              { value: 'position_time', label: 'Position Time Limits', category: 'position' },
              
              // Portfolio level
              { value: 'portfolio_heat', label: 'Portfolio Heat Monitoring', category: 'portfolio' },
              { value: 'correlation_limit', label: 'Correlation Limits', category: 'portfolio' },
              { value: 'concentration_limit', label: 'Concentration Limits', category: 'portfolio' },
              { value: 'diversification', label: 'Diversification Rules', category: 'portfolio' },
              
              // Market risk
              { value: 'volatility_filter', label: 'Volatility Filter', category: 'market' },
              { value: 'liquidity_check', label: 'Liquidity Check', category: 'market' },
              { value: 'news_filter', label: 'News Event Filter', category: 'market' },
              { value: 'market_hours', label: 'Market Hours Control', category: 'market' },
              
              // Drawdown protection
              { value: 'daily_drawdown', label: 'Daily Drawdown Limit', category: 'drawdown' },
              { value: 'weekly_drawdown', label: 'Weekly Drawdown Limit', category: 'drawdown' },
              { value: 'monthly_drawdown', label: 'Monthly Drawdown Limit', category: 'drawdown' },
              { value: 'max_drawdown', label: 'Maximum Drawdown Limit', category: 'drawdown' },
              
              // Exposure management
              { value: 'sector_exposure', label: 'Sector Exposure Limit', category: 'exposure' },
              { value: 'currency_exposure', label: 'Currency Exposure Limit', category: 'exposure' },
              { value: 'leverage_limit', label: 'Leverage Limits', category: 'exposure' },
              { value: 'var_limit', label: 'Value at Risk Limit', category: 'exposure' }
            ],
            default: 'position_size'
          },
          riskLevel: {
            type: 'range',
            label: 'Risk Level',
            description: 'Risk tolerance level (1=Conservative, 5=Aggressive)',
            min: 1,
            max: 5,
            step: 1,
            default: 2
          },
          maxLoss: {
            type: 'number',
            label: 'Max Loss %',
            description: 'Maximum loss percentage per trade',
            min: 0.1,
            max: 50,
            step: 0.1,
            default: 2.0
          },
          positionSize: {
            type: 'number',
            label: 'Position Size %',
            description: 'Percentage of portfolio per position',
            min: 0.1,
            max: 100,
            step: 0.1,
            default: 5.0
          },
          portfolioHeat: {
            type: 'number',
            label: 'Portfolio Heat %',
            description: 'Maximum percentage of portfolio at risk',
            min: 1,
            max: 50,
            step: 0.5,
            default: 20
          },
          maxPositions: {
            type: 'number',
            label: 'Max Concurrent Positions',
            description: 'Maximum number of open positions',
            min: 1,
            max: 50,
            default: 10
          },
          correlationThreshold: {
            type: 'number',
            label: 'Correlation Threshold',
            description: 'Maximum correlation between positions',
            min: 0.1,
            max: 1.0,
            step: 0.05,
            default: 0.7
          },
          volatilityThreshold: {
            type: 'number',
            label: 'Volatility Threshold %',
            description: 'Maximum acceptable volatility',
            min: 1,
            max: 100,
            step: 1,
            default: 30
          },
          timeLimit: {
            type: 'number',
            label: 'Position Time Limit (hours)',
            description: 'Maximum time to hold position',
            min: 1,
            max: 720,
            default: 168
          },
          drawdownLimit: {
            type: 'number',
            label: 'Drawdown Limit %',
            description: 'Maximum allowable drawdown',
            min: 1,
            max: 50,
            step: 0.5,
            default: 10
          },
          leverageLimit: {
            type: 'number',
            label: 'Maximum Leverage',
            description: 'Maximum leverage ratio',
            min: 1,
            max: 10,
            step: 0.1,
            default: 2.0
          },
          varConfidence: {
            type: 'number',
            label: 'VaR Confidence %',
            description: 'Value at Risk confidence level',
            min: 90,
            max: 99.9,
            step: 0.1,
            default: 95
          },
          emergencyAction: {
            type: 'select',
            label: 'Emergency Action',
            description: 'Action when risk limits exceeded',
            options: [
              { value: 'alert_only', label: 'Alert Only' },
              { value: 'stop_new_trades', label: 'Stop New Trades' },
              { value: 'reduce_positions', label: 'Reduce Positions' },
              { value: 'close_all', label: 'Close All Positions' },
              { value: 'hedge_portfolio', label: 'Hedge Portfolio' },
            ],
            default: 'alert_only'
          }
        };

      default:
        return {};
    }
  };

  // Helper function to determine if a field should be shown based on conditions
  const shouldShowField = (key: string, config: any, params: Record<string, any>) => {
    // Technical Indicator specific fields
    if (key === 'multiplier') {
      return ['BB', 'KC', 'SQUEEZE'].includes(params.indicator);
    }
    
    if (key === 'smoothing') {
      return ['EMA', 'DEMA', 'TEMA', 'ZLEMA', 'ALMA', 'KAMA', 'MAMA', 'T3', 'FRAMA', 'VIDYA', 'MACD'].includes(params.indicator);
    }
    
    if (key === 'fastPeriod' || key === 'slowPeriod') {
      return ['MACD', 'PPO', 'AROON', 'STOCHRSI', 'TSI'].includes(params.indicator);
    }
    
    if (key === 'signalPeriod') {
      return ['MACD', 'PPO', 'TSI'].includes(params.indicator);
    }
    
    if (key === 'kPeriod' || key === 'dPeriod' || key === 'slowing') {
      return ['STOCH', 'STOCHRSI', 'KDJ'].includes(params.indicator);
    }
    
    if (key === 'acceleration' || key === 'maximum') {
      return params.indicator === 'PSAR';
    }
    
    if (key === 'outputType') {
      return ['MACD', 'BB', 'KC', 'DC', 'STOCH', 'AROON', 'DMI'].includes(params.indicator);
    }
    
    // Condition specific fields
    if (key === 'value2') {
      return ['range', 'outside_range'].includes(params.condition);
    }
    
    if (key === 'confirmationBars') {
      return ['crossover', 'crossunder', 'breakout_up', 'breakout_down', 'golden_cross', 'death_cross'].includes(params.condition);
    }
    
    if (key === 'percentageThreshold') {
      return ['percentage_change', 'breakout_up', 'breakout_down', 'momentum_change'].includes(params.condition);
    }
    
    if (key === 'higherTimeframe') {
      return ['higher_timeframe_trend', 'multi_tf_alignment', 'weekly_monthly_bias'].includes(params.condition);
    }
    
    if (key === 'trendStrength') {
      return ['trend_strength', 'rising', 'falling', 'higher_timeframe_trend'].includes(params.condition);
    }
    
    if (key === 'divergenceType') {
      return ['bullish_divergence', 'bearish_divergence'].includes(params.condition);
    }
    
    // Action specific fields
    if (key === 'price_offset') {
      return ['limit', 'stop_limit', 'iceberg', 'bracket'].includes(params.order_type);
    }
    
    if (key === 'stop_loss' || key === 'take_profit') {
      return ['buy', 'sell', 'buy_limit', 'sell_limit'].includes(params.action);
    }
    
    if (key === 'trailing_distance') {
      return params.order_type === 'trailing_stop' || params.action === 'trailing_stop';
    }
    
    if (key === 'slippage_tolerance') {
      return ['market', 'twap', 'vwap'].includes(params.order_type);
    }
    
    if (key === 'execution_algorithm') {
      return ['market', 'limit', 'twap', 'vwap'].includes(params.order_type);
    }
    
    // Risk Management specific fields
    if (key === 'positionSize') {
      return ['position_size', 'concentration_limit'].includes(params.riskType);
    }
    
    if (key === 'portfolioHeat') {
      return ['portfolio_heat', 'diversification'].includes(params.riskType);
    }
    
    if (key === 'maxPositions') {
      return ['portfolio_heat', 'concentration_limit', 'diversification'].includes(params.riskType);
    }
    
    if (key === 'correlationThreshold') {
      return params.riskType === 'correlation_limit';
    }
    
    if (key === 'volatilityThreshold') {
      return params.riskType === 'volatility_filter';
    }
    
    if (key === 'timeLimit') {
      return params.riskType === 'position_time';
    }
    
    if (key === 'drawdownLimit') {
      return ['daily_drawdown', 'weekly_drawdown', 'monthly_drawdown', 'max_drawdown'].includes(params.riskType);
    }
    
    if (key === 'leverageLimit') {
      return params.riskType === 'leverage_limit';
    }
    
    if (key === 'varConfidence') {
      return params.riskType === 'var_limit';
    }
    
    // Data Source specific fields
    if (key === 'startDate' || key === 'endDate') {
      return params.dataSource === 'system';
    }
    
    if (key === 'bars') {
      return params.dataSource === 'system';
    }
    
    return true; // Show by default
  };

  // Helper function to get validation errors
  const getValidationErrors = () => {
    const errors: string[] = [];
    const nodeType = selectedNodeData?.type;
    const params = localParameters;

    if (nodeType === 'technicalIndicator') {
      if (params.period < 1 || params.period > 200) {
        errors.push('Period must be between 1 and 200');
      }
    }

    if (nodeType === 'condition') {
      if (params.condition === 'range' && params.value >= params.value2) {
        errors.push('Upper threshold must be greater than lower threshold');
      }
    }

    if (nodeType === 'action') {
      if (params.quantity < 0) {
        errors.push('Quantity cannot be negative');
      }
      if (params.price_offset < -50 || params.price_offset > 50) {
        errors.push('Price offset must be between -50% and 50%');
      }
    }

    if (nodeType === 'risk') {
      if (params.maxLoss <= 0 || params.maxLoss > 50) {
        errors.push('Max loss must be between 0.1% and 50%');
      }
    }

    return errors;
  };

  // Helper function to get node inputs with connection status
  const getNodeInputs = () => {
    if (!selectedNode || !currentWorkflow) return [];
    
    const nodeType = selectedNodeData?.type;
    const edges = currentWorkflow.edges;
    
    const inputs = [];
    
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

  const nodeConfig = getNodeConfiguration(selectedNodeData?.type || 'unknown');

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 space-y-4">
        {/* Node Header */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Node Configuration</h2>
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
              <span className="text-sm font-medium">{selectedNodeData.data.label}</span>
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
                <CardTitle className="text-sm">Node Parameters</CardTitle>
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
                <CardTitle className="text-sm">Input Connections</CardTitle>
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
                <CardTitle className="text-sm">Output Connections</CardTitle>
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