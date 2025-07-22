import { NodeConfigFields, NodeConfigResult } from './types';
import { commonFields } from './commonFields';

// Risk management options organized by category
const riskTypeOptions = [
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
];

export function getRiskManagementConfig(): NodeConfigResult {
  const fields: NodeConfigFields = {
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
      options: riskTypeOptions,
      default: 'position_size'
    },

    riskLevel: commonFields.riskLevel,
    maxLoss: commonFields.maxLoss,
    positionSize: commonFields.positionSize,

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

  const shouldShowField = (key: string, config: any, params: Record<string, any>) => {
    switch (key) {
      case 'positionSize':
        return ['position_size', 'concentration_limit'].includes(params.riskType);
      
      case 'portfolioHeat':
        return ['portfolio_heat', 'diversification'].includes(params.riskType);
      
      case 'maxPositions':
        return ['portfolio_heat', 'concentration_limit', 'diversification'].includes(params.riskType);
      
      case 'correlationThreshold':
        return params.riskType === 'correlation_limit';
      
      case 'volatilityThreshold':
        return params.riskType === 'volatility_filter';
      
      case 'timeLimit':
        return params.riskType === 'position_time';
      
      case 'drawdownLimit':
        return ['daily_drawdown', 'weekly_drawdown', 'monthly_drawdown', 'max_drawdown'].includes(params.riskType);
      
      case 'leverageLimit':
        return params.riskType === 'leverage_limit';
      
      case 'varConfidence':
        return params.riskType === 'var_limit';
      
      default:
        return true;
    }
  };

  return { fields, shouldShowField };
}

export function validateRiskManagementConfig(params: Record<string, any>): string[] {
  const errors: string[] = [];

  if (params.maxLoss <= 0 || params.maxLoss > 50) {
    errors.push('Max loss must be between 0.1% and 50%');
  }

  if (params.positionSize && (params.positionSize <= 0 || params.positionSize > 100)) {
    errors.push('Position size must be between 0.1% and 100%');
  }

  if (params.portfolioHeat && (params.portfolioHeat < 1 || params.portfolioHeat > 50)) {
    errors.push('Portfolio heat must be between 1% and 50%');
  }

  if (params.correlationThreshold && (params.correlationThreshold < 0.1 || params.correlationThreshold > 1.0)) {
    errors.push('Correlation threshold must be between 0.1 and 1.0');
  }

  if (params.leverageLimit && (params.leverageLimit < 1 || params.leverageLimit > 10)) {
    errors.push('Leverage limit must be between 1 and 10');
  }

  if (params.varConfidence && (params.varConfidence < 90 || params.varConfidence > 99.9)) {
    errors.push('VaR confidence must be between 90% and 99.9%');
  }

  return errors;
}