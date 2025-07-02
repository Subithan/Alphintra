'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Info, 
  RefreshCw,
  Zap,
  Clock,
  HardDrive,
  Shield
} from 'lucide-react';
import { UseWorkflowValidationResult } from '@/hooks/useWorkflowValidation';
import { ValidationError } from '@/lib/workflow-validation';
import { WorkflowHealthComponent } from './WorkflowHealth';
import { analyzeWorkflow } from '@/lib/workflow-analyzer';

interface ValidationPanelProps {
  validation: UseWorkflowValidationResult;
  onNodeSelect?: (nodeId: string) => void;
  className?: string;
  nodes?: any[];
  edges?: any[];
}

export function ValidationPanel({ validation, onNodeSelect, className, nodes = [], edges = [] }: ValidationPanelProps) {
  const {
    validation: result,
    isValidating,
    criticalErrors,
    warnings,
    validateNow,
    hasErrors,
    hasWarnings
  } = validation;

  const getErrorIcon = (error: ValidationError) => {
    switch (error.severity) {
      case 'critical':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'medium':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'low':
        return <Info className="h-4 w-4 text-blue-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'high':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'structure':
        return '🏗️';
      case 'connection':
        return '🔗';
      case 'parameter':
        return '⚙️';
      case 'performance':
        return '⚡';
      case 'security':
        return '🔒';
      default:
        return '❓';
    }
  };

  const handleErrorClick = (error: ValidationError) => {
    if (error.nodeId && onNodeSelect) {
      onNodeSelect(error.nodeId);
    }
  };

  // Generate workflow health analysis
  const workflowHealth = React.useMemo(() => {
    if (nodes.length === 0) return null;
    return analyzeWorkflow(nodes, edges);
  }, [nodes, edges]);

  const renderValidationList = (items: ValidationError[], title: string) => (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-muted-foreground">{title}</h4>
      {items.length === 0 ? (
        <div className="flex items-center space-x-2 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <span className="text-sm text-green-600 dark:text-green-400">No issues found</span>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((item, index) => (
            <div
              key={`${item.id}-${index}`}
              className={`p-3 border rounded cursor-pointer hover:bg-muted/50 transition-colors ${
                item.nodeId ? 'hover:border-blue-300' : ''
              }`}
              onClick={() => handleErrorClick(item)}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  {getErrorIcon(item)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-xs">{getCategoryIcon(item.category)}</span>
                    <Badge className={`text-xs ${getSeverityColor(item.severity)}`}>
                      {item.severity}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {item.category}
                    </Badge>
                  </div>
                  <p className="text-sm font-medium text-foreground">{item.message}</p>
                  {item.suggestion && (
                    <p className="text-xs text-muted-foreground mt-1">
                      💡 {item.suggestion}
                    </p>
                  )}
                  {item.nodeId && (
                    <p className="text-xs text-blue-600 mt-1">
                      📍 Node: {item.nodeId}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center space-x-2">
            {result.isValid ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500" />
            )}
            <span>Workflow Validation</span>
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={validateNow}
            disabled={isValidating}
          >
            {isValidating ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {isValidating ? 'Validating...' : 'Validate'}
          </Button>
        </div>
        
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-1">
            <XCircle className="h-4 w-4 text-red-500" />
            <span>{result.errors.length} errors</span>
          </div>
          <div className="flex items-center space-x-1">
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
            <span>{result.warnings.length} warnings</span>
          </div>
          <div className={`px-2 py-1 rounded text-xs font-medium ${
            result.isValid 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {result.isValid ? 'Valid' : 'Invalid'}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs defaultValue="errors" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="errors" className="text-xs">
              Errors ({result.errors.length})
            </TabsTrigger>
            <TabsTrigger value="warnings" className="text-xs">
              Warnings ({result.warnings.length})
            </TabsTrigger>
            <TabsTrigger value="performance" className="text-xs">
              Performance
            </TabsTrigger>
            <TabsTrigger value="health" className="text-xs">
              Health
            </TabsTrigger>
          </TabsList>

          <TabsContent value="errors" className="mt-4">
            <ScrollArea className="h-80">
              {renderValidationList(result.errors, 'Validation Errors')}
            </ScrollArea>
          </TabsContent>

          <TabsContent value="warnings" className="mt-4">
            <ScrollArea className="h-80">
              {renderValidationList(result.warnings, 'Validation Warnings')}
            </ScrollArea>
          </TabsContent>

          <TabsContent value="performance" className="mt-4">
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4">
                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center space-x-3">
                      <Zap className="h-5 w-5 text-blue-500" />
                      <div>
                        <p className="text-sm font-medium">Complexity Score</p>
                        <p className="text-2xl font-bold">{result.performance.estimatedComplexity}</p>
                        <p className="text-xs text-muted-foreground">
                          {result.performance.estimatedComplexity < 500 ? 'Low' : 
                           result.performance.estimatedComplexity < 1000 ? 'Medium' : 'High'} complexity
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center space-x-3">
                      <Clock className="h-5 w-5 text-green-500" />
                      <div>
                        <p className="text-sm font-medium">Estimated Execution</p>
                        <p className="text-2xl font-bold">{result.performance.estimatedExecutionTime}ms</p>
                        <p className="text-xs text-muted-foreground">
                          Per data point processing time
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center space-x-3">
                      <HardDrive className="h-5 w-5 text-purple-500" />
                      <div>
                        <p className="text-sm font-medium">Memory Usage</p>
                        <p className="text-2xl font-bold">
                          {(result.performance.memoryUsage / 1024).toFixed(1)}KB
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Estimated memory footprint
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Separator />

              <div className="space-y-2">
                <h4 className="text-sm font-medium">Optimization Suggestions</h4>
                <div className="space-y-2 text-sm text-muted-foreground">
                  {result.performance.estimatedComplexity > 1000 && (
                    <div className="flex items-start space-x-2">
                      <span>•</span>
                      <span>Consider reducing the number of technical indicators</span>
                    </div>
                  )}
                  {result.performance.estimatedExecutionTime > 100 && (
                    <div className="flex items-start space-x-2">
                      <span>•</span>
                      <span>Use smaller indicator periods for better performance</span>
                    </div>
                  )}
                  {result.performance.memoryUsage > 10240 && (
                    <div className="flex items-start space-x-2">
                      <span>•</span>
                      <span>Reduce the number of concurrent connections</span>
                    </div>
                  )}
                  {result.performance.estimatedComplexity <= 500 && (
                    <div className="flex items-start space-x-2">
                      <span>✓</span>
                      <span>Workflow is well-optimized for performance</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="health" className="mt-4">
            {workflowHealth ? (
              <WorkflowHealthComponent
                health={workflowHealth}
                onNodeSelect={onNodeSelect}
                className="border-0 shadow-none p-0"
              />
            ) : (
              <div className="text-center py-8">
                <div className="text-muted-foreground">
                  <p className="text-sm">Add nodes to your workflow to see health analysis</p>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}