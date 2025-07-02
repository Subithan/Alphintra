import React from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle } from 'lucide-react';

interface CustomDatasetNodeData {
  label: string;
  parameters: {
    fileName?: string;
    fileSize?: string;
    columns?: string[];
    dateColumn?: string;
    ohlcMapping?: {
      open?: string;
      high?: string;
      low?: string;
      close?: string;
      volume?: string;
    };
    dataQuality?: 'good' | 'warning' | 'error';
    rowCount?: number;
    missingValues?: number;
  };
}

export function CustomDatasetNode({ data, selected }: NodeProps<CustomDatasetNodeData>) {
  const { label, parameters } = data;
  const fileName = parameters?.fileName || 'No file uploaded';
  const dataQuality = parameters?.dataQuality || 'warning';
  const rowCount = parameters?.rowCount || 0;
  const fileSize = parameters?.fileSize || '';

  const getQualityIcon = (quality: string) => {
    switch (quality) {
      case 'good': return <CheckCircle className="h-3 w-3 text-green-500" />;
      case 'warning': return <AlertCircle className="h-3 w-3 text-yellow-500" />;
      case 'error': return <AlertCircle className="h-3 w-3 text-red-500" />;
      default: return <Upload className="h-3 w-3 text-gray-500" />;
    }
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'good': return 'bg-green-100 text-green-800 border-green-300';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'error': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const hasFile = fileName !== 'No file uploaded';

  return (
    <Card className={`min-w-[200px] ${selected ? 'ring-2 ring-blue-500' : ''} dark:bg-card dark:border-border`} suppressHydrationWarning>
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          <FileSpreadsheet className="h-4 w-4 text-green-600 dark:text-green-400" />
          <span className="font-medium text-sm dark:text-foreground">{label}</span>
        </div>
        
        <div className="space-y-1.5">
          {hasFile ? (
            <>
              <div className="text-xs font-medium truncate" title={fileName}>
                {fileName}
              </div>
              
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="text-xs">
                  {rowCount.toLocaleString()} rows
                </Badge>
                <div className="flex items-center space-x-1">
                  {getQualityIcon(dataQuality)}
                  <span className="text-xs text-muted-foreground">{fileSize}</span>
                </div>
              </div>
              
              <div className={`text-xs px-1.5 py-0.5 rounded border ${getQualityColor(dataQuality)}`}>
                {dataQuality === 'good' && 'Data Valid'}
                {dataQuality === 'warning' && 'Minor Issues'}
                {dataQuality === 'error' && 'Validation Errors'}
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center space-x-1">
                <Upload className="h-3 w-3 text-gray-400" />
                <span className="text-xs text-muted-foreground">No file uploaded</span>
              </div>
              
              <div className="text-xs text-muted-foreground">
                CSV/Excel file required
              </div>
            </>
          )}
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