import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { 
  Target, TrendingUp, GitMerge, Search, Clock, 
  Network, Zap, Layers, Volume2, Brain,
  CheckCircle2, Gauge, Eye
} from 'lucide-react';
import { useNoCodeStore } from '@/lib/stores/no-code-store';

interface ConditionNodeData {
  label: string;
  parameters: {
    conditionType?: string;
    condition?: string;
    value?: number;
    value2?: number;
    lookback?: number;
    confirmationBars?: number;
    higherTimeframe?: string;
  };
}

export function ConditionNode({ id, selected }: NodeProps<ConditionNodeData>) {
  // Get the node data directly from the store and subscribe to updates
  const { data, lastModified } = useNoCodeStore(
    (state) => {
      const node = state.currentWorkflow?.nodes.find(n => n.id === id);
      return { 
        data: node?.data || { label: 'Condition', parameters: {} },
        lastModified: node?.data?.lastModified
      };
    }
  );

  const { label, parameters } = data;
  const conditionType = parameters?.conditionType || 'comparison';
  const condition = parameters?.condition || 'greater_than';
  const value = parameters?.value || 0;
  const value2 = parameters?.value2;
  const confirmationBars = parameters?.confirmationBars;
  const higherTimeframe = parameters?.higherTimeframe;
  const complexityLevel = parameters?.complexityLevel || 'simple';
  
  // Get complexity level for visual styling
  const getComplexityFromCondition = (condition: string) => {
    const complexityMap: Record<string, string> = {
      // Simple conditions
      'greater_than': 'simple', 'less_than': 'simple', 'equal_to': 'simple',
      'rising': 'simple', 'falling': 'simple', 'oversold': 'simple', 'overbought': 'simple',
      'higher_high': 'simple', 'lower_low': 'simple',
      
      // Medium conditions  
      'range': 'medium', 'crossover': 'medium', 'golden_cross': 'medium',
      'breakout_up': 'medium', 'flag_pattern': 'medium', 'volume_spike': 'medium',
      'trend_strength': 'medium', 'support_level': 'medium', 'atr_multiple': 'medium',
      
      // Advanced conditions
      'bullish_divergence': 'advanced', 'head_shoulders': 'advanced', 
      'bollinger_squeeze': 'advanced', 'correlation_strength': 'advanced',
      'z_score': 'advanced', 'ichimoku_cross': 'advanced',
      
      // Expert conditions
      'elliott_wave_count': 'expert', 'wyckoff_phase': 'expert',
      'market_maker_move': 'expert', 'fractal_alignment': 'expert'
    };
    return complexityMap[condition] || 'simple';
  };
  
  const actualComplexity = complexityLevel === 'all' ? getComplexityFromCondition(condition) : complexityLevel;

  const getCategoryIcon = (category: string, complexity: string = 'simple') => {
    const iconProps = complexity === 'expert' ? 'h-5 w-5' : 'h-4 w-4';
    
    switch (category) {
      case 'comparison': return <Target className={`${iconProps} text-orange-600 dark:text-orange-400`} />;
      case 'crossover': return <GitMerge className={`${iconProps} text-blue-600 dark:text-blue-400`} />;
      case 'trend': return <TrendingUp className={`${iconProps} text-green-600 dark:text-green-400`} />;
      case 'pattern': return <Search className={`${iconProps} text-purple-600 dark:text-purple-400`} />;
      case 'timeframe': return <Clock className={`${iconProps} text-red-600 dark:text-red-400`} />;
      case 'volume': return <Volume2 className={`${iconProps} text-cyan-600 dark:text-cyan-400`} />;
      case 'structure': return <Layers className={`${iconProps} text-indigo-600 dark:text-indigo-400`} />;
      case 'volatility': return <Zap className={`${iconProps} text-yellow-600 dark:text-yellow-400`} />;
      case 'correlation': return <Network className={`${iconProps} text-pink-600 dark:text-pink-400`} />;
      default: return <Target className={`${iconProps} text-orange-600 dark:text-orange-400`} />;
    }
  };


  const getCategoryColor = (category: string, complexity: string = 'simple') => {
    const baseColors = {
      comparison: 'orange',
      crossover: 'blue', 
      trend: 'green',
      pattern: 'purple',
      timeframe: 'red',
      volume: 'cyan',
      structure: 'indigo',
      volatility: 'yellow',
      correlation: 'pink'
    };
    
    const color = baseColors[category as keyof typeof baseColors] || 'orange';
    
    // Different intensity based on complexity
    switch (complexity) {
      case 'expert':
        return `bg-${color}-200 text-${color}-900 dark:text-${color}-200 border-${color}-400 font-bold`;
      case 'advanced':
        return `bg-${color}-200 text-${color}-900 dark:text-${color}-200 border-${color}-400 font-semibold`;
      case 'medium':
        return `bg-${color}-100 text-${color}-800 dark:text-${color}-200 border-${color}-300`;
      default:
        return `bg-${color}-50 text-${color}-700 dark:text-${color}-200 border-${color}-200`;
    }
  };
  
  const getComplexityBadge = (complexity: string) => {
    const complexityConfig = {
      simple: { icon: <CheckCircle2 className="h-3 w-3" />, color: 'bg-green-100 text-green-700 dark:text-green-200', label: 'Basic' },
      medium: { icon: <Gauge className="h-3 w-3" />, color: 'bg-blue-100 text-blue-700 dark:text-blue-200', label: 'Medium' },
      advanced: { icon: <Eye className="h-3 w-3" />, color: 'bg-purple-100 text-purple-700 dark:text-purple-200', label: 'Advanced' },
      expert: { icon: <Brain className="h-3 w-3" />, color: 'bg-red-100 text-red-700 dark:text-red-200', label: 'Expert' }
    };
    
    const config = complexityConfig[complexity as keyof typeof complexityConfig] || complexityConfig.simple;
    return (
      <div className={`flex items-center space-x-1 px-1.5 py-0.5 rounded text-xs border glass-badge ${config.color}`}>
        {config.icon}
        <span>{config.label}</span>
      </div>
    );
  };

  const getConditionDisplay = (condition: string) => {
    const conditionMap: Record<string, string> = {
      // Basic comparisons
      'greater_than': '>', 'less_than': '<', 'equal_to': '=', 'not_equal': '!=',
      'greater_equal': '>=', 'less_equal': '<=', 'range': '⬌', 'outside_range': '⬆⬇',
      'percentage_change': '%Δ', 'rate_of_change': 'ROC', 'absolute_change': 'Δ',
      'z_score': 'Z', 'percentile_rank': '%R',
      
      // Crossovers
      'crossover': '↗', 'crossunder': '↘', 'golden_cross': '🥇', 'death_cross': '💀',
      'macd_signal_cross': 'MACD×', 'rsi_level_cross': 'RSI×', 'stoch_level_cross': 'STOCH×',
      'triple_ma_cross': '3MA×', 'ichimoku_cross': 'ICH×',
      
      // Trends
      'rising': '📈', 'falling': '📉', 'sideways': '→', 'trend_strength': '💪',
      'momentum_change': 'MOM', 'adx_trend': 'ADX', 'parabolic_sar': 'PSAR',
      'trend_acceleration': '⚡', 'trend_exhaustion': '🔋', 'elliott_wave_count': 'EW',
      
      // Patterns
      'support_level': '🛡️', 'resistance_level': '⛔', 'breakout_up': '🚀', 'breakout_down': '⬇️',
      'oversold': '📉', 'overbought': '📈', 'double_top': 'M', 'double_bottom': 'W',
      'head_shoulders': 'H&S', 'triangle_pattern': '△', 'flag_pattern': '🏳️',
      'hammer': '🔨', 'doji': '✚', 'engulfing_bullish': '🟢', 'morning_star': '⭐',
      
      // Volume
      'volume_spike': '🔊', 'volume_dry_up': '🔇', 'on_balance_volume': 'OBV',
      'money_flow_index': 'MFI', 'chaikin_oscillator': 'CHO',
      
      // Structure
      'higher_high': 'HH', 'lower_low': 'LL', 'structure_break': '💥',
      'liquidity_sweep': '🧹', 'fair_value_gap': 'FVG', 'order_block': '📦',
      
      // Volatility
      'volatility_expansion': '💥', 'volatility_contraction': '🤏', 'atr_multiple': 'ATR',
      'bollinger_squeeze': 'BB🤏', 'keltner_squeeze': 'KEL🤏',
      
      // Correlation
      'correlation_strength': '🔗', 'correlation_divergence': '↗↘', 
      'sector_rotation': '🔄', 'market_regime_change': '🔀'
    };
    
    return conditionMap[condition] || '?';
  };
  
  // Dynamic node width based on complexity
  const getNodeWidth = (complexity: string) => {
    switch (complexity) {
      case 'expert': return 'min-w-[280px]';
      case 'advanced': return 'min-w-[240px]';
      case 'medium': return 'min-w-[220px]';
      default: return 'min-w-[200px]';
    }
  };
  
  const renderAdditionalInfo = () => {
    const items = [];
    
    if (parameters?.volumeThreshold) {
      items.push(`Vol: ${parameters.volumeThreshold}x`);
    }
    if (parameters?.patternStrength && parameters.patternStrength !== 'moderate') {
      items.push(`Strength: ${parameters.patternStrength}`);
    }
    if (parameters?.volatilityMultiplier && parameters.volatilityMultiplier !== 1.5) {
      items.push(`Vol Mult: ${parameters.volatilityMultiplier}`);
    }
    if (parameters?.correlationThreshold) {
      items.push(`Corr: ${parameters.correlationThreshold}`);
    }
    if (parameters?.referenceSymbol && parameters.referenceSymbol !== 'SPY') {
      items.push(`Ref: ${parameters.referenceSymbol}`);
    }
    
    return items.length > 0 ? (
      <div className="text-xs text-muted-foreground">
        {items.join(' • ')}
      </div>
    ) : null;
  };

  const getValueDisplay = () => {
    if (value2 !== undefined && ['range', 'outside_range'].includes(condition)) {
      return `${value}-${value2}`;
    }
    if (higherTimeframe && conditionType === 'timeframe') {
      return higherTimeframe;
    }
    if (condition === 'percentage_change') {
      return `${value}%`;
    }
    return value !== undefined ? value.toString() : '';
  };

  return (
    <Card
      variant="glass"
      className={`${getNodeWidth(actualComplexity)} node-glow ${selected ? 'ring-2 ring-blue-500 shadow-lg' : ''} transition-all duration-200`}
      suppressHydrationWarning
    >
      <CardContent className="p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            {getCategoryIcon(conditionType, actualComplexity)}
            <span className="font-medium text-sm text-foreground truncate">{label}</span>
          </div>
          {getComplexityBadge(actualComplexity)}
        </div>
        
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2 flex-wrap gap-1">
            <Badge variant="default" className={`glass-badge text-xs font-semibold ${actualComplexity === 'expert' ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white' : ''}`}>
              {getConditionDisplay(condition)} {getValueDisplay()}
            </Badge>
            {confirmationBars && confirmationBars > 0 && (
              <Badge variant="outline" className="glass-badge text-xs">
                {confirmationBars}b
              </Badge>
            )}
            {higherTimeframe && conditionType === 'timeframe' && (
              <Badge variant="secondary" className="glass-badge text-xs">
                {higherTimeframe}
              </Badge>
            )}
          </div>

          <div className={`text-xs px-1.5 py-0.5 rounded border glass-badge ${getCategoryColor(conditionType, actualComplexity)}`}>
            {conditionType.toUpperCase()}
          </div>
          
          <div className="text-xs text-muted-foreground">
            {condition.replace(/_/g, ' ')}
          </div>
          
          {renderAdditionalInfo()}
        </div>

        {/* Dynamic Input Handles based on condition type */}
        <Handle
          type="target"
          position={Position.Left}
          id="data-input"
          className={`w-3 h-3 ${actualComplexity === 'expert' ? 'bg-purple-500' : 'bg-gray-400'}`}
          style={{ left: -6, top: '25%' }}
        />
        <div
          className="absolute text-xs font-medium text-gray-600 dark:text-gray-300 pointer-events-none"
          style={{
            left: -50,
            top: 'calc(25% - 8px)',
            fontSize: '10px'
          }}
        >
          Data
        </div>

        <Handle
          type="target"
          position={Position.Left}
          id="value-input"
          className={`w-3 h-3 ${actualComplexity === 'expert' ? 'bg-pink-500' : 'bg-blue-500'}`}
          style={{ left: -6, top: '50%' }}
        />
        <div
          className="absolute text-xs font-medium text-gray-600 dark:text-gray-300 pointer-events-none"
          style={{
            left: -50,
            top: 'calc(50% - 8px)',
            fontSize: '10px'
          }}
        >
          {conditionType === 'crossover' ? 'Threshold' : conditionType === 'correlation' ? 'Reference' : 'Value'}
        </div>

        {/* Additional input for complex conditions */}
        {['correlation', 'structure', 'volatility'].includes(conditionType) && (
          <>
            <Handle
              type="target"
              position={Position.Left}
              id="aux-input"
              className="w-3 h-3 bg-amber-500"
              style={{ left: -6, top: '75%' }}
            />
            <div
              className="absolute text-xs font-medium text-gray-600 dark:text-gray-300 pointer-events-none"
              style={{
                left: -50,
                top: 'calc(75% - 8px)',
                fontSize: '10px'
              }}
            >
              {conditionType === 'correlation' ? 'Market' : conditionType === 'structure' ? 'Levels' : 'Context'}
            </div>
          </>
        )}

        {/* Output Handle with enhanced styling */}
        <Handle
          type="source"
          position={Position.Right}
          id="signal-output"
          className={`w-3 h-3 ${actualComplexity === 'expert' ? 'bg-gradient-to-r from-green-400 to-emerald-600' : 'bg-green-500'}`}
          style={{ right: -6 }}
        />
        <div
          className="absolute text-xs font-medium text-gray-600 dark:text-gray-300 pointer-events-none"
          style={{
            right: -45,
            top: 'calc(50% - 8px)',
            fontSize: '10px'
          }}
        >
          Signal
        </div>
      </CardContent>
    </Card>
  );
}