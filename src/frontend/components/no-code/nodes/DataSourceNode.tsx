import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Database, TrendingUp, Upload, Globe, DollarSign, Bitcoin } from 'lucide-react';

interface DataSourceNodeData {
  label: string;
  parameters: {
    symbol?: string;
    timeframe?: string;
    bars?: number;
    dataSource?: 'system' | 'upload';
    assetClass?: 'crypto' | 'stocks' | 'forex';
    startDate?: string;
    endDate?: string;
  };
}

export function DataSourceNode({ data, selected }: NodeProps<DataSourceNodeData>) {
  const { label, parameters } = data;
  const symbol = parameters?.symbol || 'AAPL';
  const timeframe = parameters?.timeframe || '1h';
  const dataSource = parameters?.dataSource || 'system';
  const assetClass = parameters?.assetClass || 'stocks';

  const getAssetIcon = (assetClass: string) => {
    switch (assetClass) {
      case 'crypto': return <Bitcoin className="h-3 w-3 text-orange-500" />;
      case 'forex': return <Globe className="h-3 w-3 text-green-500" />;
      case 'stocks': return <TrendingUp className="h-3 w-3 text-blue-500" />;
      default: return <TrendingUp className="h-3 w-3 text-blue-500" />;
    }
  };

  const getDataSourceIcon = (source: string) => {
    return source === 'upload' ? 
      <Upload className="h-3 w-3 text-purple-500" /> : 
      <Database className="h-3 w-3 text-purple-600 dark:text-purple-400" />;
  };

  const getAssetClassColor = (assetClass: string) => {
    switch (assetClass) {
      case 'crypto': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'forex': return 'bg-green-100 text-green-800 border-green-300';
      case 'stocks': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-blue-100 text-blue-800 border-blue-300';
    }
  };

  return (
    <Card className={`min-w-[180px] ${selected ? 'ring-2 ring-blue-500' : ''} dark:bg-card dark:border-border`} suppressHydrationWarning>
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          {getDataSourceIcon(dataSource)}
          <span className="font-medium text-sm dark:text-foreground">{label}</span>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex items-center space-x-1">
            <Badge variant="default" className="text-xs font-semibold">
              {symbol}
            </Badge>
            {getAssetIcon(assetClass)}
          </div>
          
          <div className={`text-xs px-1.5 py-0.5 rounded border ${getAssetClassColor(assetClass)}`}>
            {assetClass.toUpperCase()}
          </div>
          
          <div className="text-xs text-muted-foreground">
            {timeframe} • {dataSource === 'system' ? 'System Data' : 'User Upload'}
          </div>
        </div>

        {/* Output Handle */}
        <Handle
          type="source"
          position={Position.Right}
          id="data-output"
          className="w-3 h-3 bg-gray-500"
          style={{ right: -6 }}
        />
      </CardContent>
    </Card>
  );
}