import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Shield, AlertTriangle, Activity, BarChart3, TrendingDown, Eye } from 'lucide-react';

interface RiskManagementNodeData {
  label: string;
  parameters: {
    riskCategory?: string;
    riskType?: string;
    riskLevel?: number;
    maxLoss?: number;
    positionSize?: number;
    portfolioHeat?: number;
    drawdownLimit?: number;
    emergencyAction?: string;
  };
}

export function RiskManagementNode({ data, selected }: NodeProps<RiskManagementNodeData>) {
  const { label, parameters } = data;
  const riskCategory = parameters?.riskCategory || 'position';
  const riskType = parameters?.riskType || 'position_size';
  const riskLevel = parameters?.riskLevel || 2;
  const maxLoss = parameters?.maxLoss;
  const portfolioHeat = parameters?.portfolioHeat;
  const drawdownLimit = parameters?.drawdownLimit;
  const emergencyAction = parameters?.emergencyAction;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'position': return <Shield className="h-4 w-4 text-blue-600 dark:text-blue-400" />;
      case 'portfolio': return <BarChart3 className="h-4 w-4 text-green-600 dark:text-green-400" />;
      case 'market': return <Activity className="h-4 w-4 text-orange-600 dark:text-orange-400" />;
      case 'drawdown': return <TrendingDown className="h-4 w-4 text-red-600 dark:text-red-400" />;
      case 'exposure': return <Eye className="h-4 w-4 text-purple-600 dark:text-purple-400" />;
      default: return <Shield className="h-4 w-4 text-blue-600 dark:text-blue-400" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'position': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'portfolio': return 'bg-green-100 text-green-800 border-green-300';
      case 'market': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'drawdown': return 'bg-red-100 text-red-800 border-red-300';
      case 'exposure': return 'bg-purple-100 text-purple-800 border-purple-300';
      default: return 'bg-blue-100 text-blue-800 border-blue-300';
    }
  };

  const getRiskColor = (level: number) => {
    if (level <= 1) return 'bg-green-100 text-green-800 border-green-300';
    if (level <= 2) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    if (level <= 3) return 'bg-orange-100 text-orange-800 border-orange-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };

  const getEmergencyActionIcon = (action: string) => {
    switch (action) {
      case 'alert_only': return '🔔';
      case 'stop_new_trades': return '⛔';
      case 'reduce_positions': return '📉';
      case 'close_all': return '🚫';
      case 'hedge_portfolio': return '🛡️';
      default: return '🔔';
    }
  };

  const getDisplayValue = () => {
    if (maxLoss) return `${maxLoss}% loss`;
    if (portfolioHeat) return `${portfolioHeat}% heat`;
    if (drawdownLimit) return `${drawdownLimit}% DD`;
    return `Level ${riskLevel}`;
  };

  return (
    <Card className={`min-w-[220px] ${selected ? 'ring-2 ring-blue-500' : ''} dark:bg-card dark:border-border`} suppressHydrationWarning>
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          {getCategoryIcon(riskCategory)}
          <span className="font-medium text-sm dark:text-foreground">{label}</span>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2">
            <Badge variant="default" className="text-xs font-semibold">
              {riskType.replace(/_/g, ' ').toUpperCase()}
            </Badge>
            {emergencyAction && emergencyAction !== 'alert_only' && (
              <Badge variant="outline" className="text-xs">
                {getEmergencyActionIcon(emergencyAction)}
              </Badge>
            )}
          </div>
          
          <div className={`text-xs px-1.5 py-0.5 rounded border ${getCategoryColor(riskCategory)}`}>
            {riskCategory.toUpperCase()} RISK
          </div>
          
          <div className={`text-xs px-1.5 py-0.5 rounded border ${getRiskColor(riskLevel)}`}>
            {getDisplayValue()}
          </div>
        </div>

        {/* Input Handles */}
        <Handle
          type="target"
          position={Position.Left}
          id="data-input"
          className="w-3 h-3 bg-gray-400"
          style={{ left: -6, top: '30%' }}
        />
        <Handle
          type="target"
          position={Position.Left}
          id="signal-input"
          className="w-3 h-3 bg-blue-500"
          style={{ left: -6, top: '70%' }}
        />

        {/* Output Handle */}
        <Handle
          type="source"
          position={Position.Right}
          id="risk-output"
          className="w-3 h-3 bg-orange-500"
          style={{ right: -6 }}
        />
      </CardContent>
    </Card>
  );
}