import { NodeConfigFields, NodeConfigResult } from './types';
import { commonFields, orderTypeOptions, timeInForceOptions, positionSizingOptions } from './commonFields';

// Action options organized by category
const actionOptions = [
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
];

export function getActionConfig(): NodeConfigResult {
  const fields: NodeConfigFields = {
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
      options: actionOptions,
      default: 'buy'
    },

    order_type: {
      type: 'select',
      label: 'Order Type',
      description: 'Type of order to place',
      options: orderTypeOptions,
      default: 'market'
    },

    positionSizing: {
      type: 'select',
      label: 'Position Sizing Method',
      description: 'How to calculate position size',
      options: positionSizingOptions,
      default: 'percentage'
    },

    quantity: commonFields.quantity,

    price_offset: {
      type: 'number',
      label: 'Price Offset %',
      description: 'Price offset from current price',
      min: -50,
      max: 50,
      step: 0.1,
      default: 0
    },

    stop_loss: commonFields.stopLoss,
    take_profit: commonFields.takeProfit,

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
      options: timeInForceOptions,
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

  const shouldShowField = (key: string, config: any, params: Record<string, any>) => {
    switch (key) {
      case 'price_offset':
        return ['limit', 'stop_limit', 'iceberg', 'bracket'].includes(params.order_type);
      
      case 'stop_loss':
      case 'take_profit':
        return ['buy', 'sell', 'buy_limit', 'sell_limit'].includes(params.action);
      
      case 'trailing_distance':
        return params.order_type === 'trailing_stop' || params.action === 'trailing_stop';
      
      case 'slippage_tolerance':
        return ['market', 'twap', 'vwap'].includes(params.order_type);
      
      case 'execution_algorithm':
        return ['market', 'limit', 'twap', 'vwap'].includes(params.order_type);
      
      default:
        return true;
    }
  };

  return { fields, shouldShowField };
}

export function validateActionConfig(params: Record<string, any>): string[] {
  const errors: string[] = [];

  if (params.quantity < 0) {
    errors.push('Quantity cannot be negative');
  }

  if (params.price_offset < -50 || params.price_offset > 50) {
    errors.push('Price offset must be between -50% and 50%');
  }

  if (params.stop_loss && (params.stop_loss <= 0 || params.stop_loss > 50)) {
    errors.push('Stop loss must be between 0.1% and 50%');
  }

  if (params.take_profit && (params.take_profit <= 0 || params.take_profit > 100)) {
    errors.push('Take profit must be between 0.1% and 100%');
  }

  if (params.slippage_tolerance && (params.slippage_tolerance < 0.01 || params.slippage_tolerance > 5.0)) {
    errors.push('Slippage tolerance must be between 0.01% and 5.0%');
  }

  return errors;
}