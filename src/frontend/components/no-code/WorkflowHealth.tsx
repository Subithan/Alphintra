'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { Button } from '@/components/ui/no-code/button';
import { Progress } from '@/components/ui/no-code/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/no-code/tabs';
import { ScrollArea } from '@/components/ui/no-code/scroll-area';
import { Separator } from '@/components/ui/no-code/separator';
import { 
  Heart, 
  TrendingUp, 
  Zap, 
  Shield, 
  Wrench,
  AlertTriangle,
  CheckCircle,
  Info,
  Lightbulb,
  Target,
  BarChart3,
  Activity
} from 'lucide-react';
import { WorkflowHealth, OptimizationSuggestion } from '@/lib/workflow-analyzer';

interface WorkflowHealthProps {
  health: WorkflowHealth;
  onNodeSelect?: (nodeId: string) => void;
  className?: string;
}

export function WorkflowHealthComponent({ health, onNodeSelect, className }: WorkflowHealthProps) {
  const getStatusColor = (status: WorkflowHealth['status']) => {
    switch (status) {
      case 'excellent': return 'text-green-600 bg-green-100 border-green-300';
      case 'good': return 'text-blue-600 bg-blue-100 border-blue-300';
      case 'fair': return 'text-yellow-600 bg-yellow-100 border-yellow-300';
      case 'poor': return 'text-orange-600 bg-orange-100 border-orange-300';
      case 'critical': return 'text-red-600 bg-red-100 border-red-300';
      default: return 'text-gray-600 bg-gray-100 border-gray-300';
    }
  };

  const getStatusIcon = (status: WorkflowHealth['status']) => {
    switch (status) {
      case 'excellent': return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'good': return <CheckCircle className="h-5 w-5 text-blue-600" />;
      case 'fair': return <Info className="h-5 w-5 text-yellow-600" />;
      case 'poor': return <AlertTriangle className="h-5 w-5 text-orange-600" />;
      case 'critical': return <AlertTriangle className="h-5 w-5 text-red-600" />;
      default: return <Info className="h-5 w-5 text-gray-600" />;
    }
  };

  const getSuggestionIcon = (type: OptimizationSuggestion['type']) => {
    switch (type) {
      case 'performance': return <Zap className="h-4 w-4 text-blue-600" />;
      case 'architecture': return <BarChart3 className="h-4 w-4 text-purple-600" />;
      case 'risk': return <Shield className="h-4 w-4 text-red-600" />;
      case 'maintainability': return <Wrench className="h-4 w-4 text-green-600" />;
      default: return <Info className="h-4 w-4 text-gray-600" />;
    }
  };

  const getSeverityColor = (severity: OptimizationSuggestion['severity']) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const handleSuggestionClick = (suggestion: OptimizationSuggestion) => {
    if (suggestion.nodeIds && suggestion.nodeIds.length > 0 && onNodeSelect) {
      // Focus on the first node in the suggestion
      onNodeSelect(suggestion.nodeIds[0]);
    }
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center space-x-2">
            <Heart className="h-5 w-5 text-pink-600" />
            <span>Workflow Health</span>
          </CardTitle>
          <div className={`px-3 py-1 rounded-full border text-sm font-medium ${getStatusColor(health.status)}`}>
            <div className="flex items-center space-x-1">
              {getStatusIcon(health.status)}
              <span>{health.status.toUpperCase()}</span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview" className="text-xs">
              Overview
            </TabsTrigger>
            <TabsTrigger value="scores" className="text-xs">
              Scores
            </TabsTrigger>
            <TabsTrigger value="suggestions" className="text-xs">
              Suggestions ({health.suggestions.length})
            </TabsTrigger>
            <TabsTrigger value="metrics" className="text-xs">
              Metrics
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-4 space-y-4">
            {/* Overall Score */}
            <div className="text-center space-y-2">
              <div className="text-3xl font-bold text-foreground">
                {health.score.overall}
                <span className="text-sm text-muted-foreground ml-1">/100</span>
              </div>
              <Progress value={health.score.overall} className="w-full h-2" />
              <p className="text-sm text-muted-foreground">
                Overall Workflow Health Score
              </p>
            </div>

            <Separator />

            {/* Quick Summary */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Activity className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium">Nodes</span>
                </div>
                <div className="text-lg font-semibold">{health.metrics.nodeCount}</div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Target className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium">Connections</span>
                </div>
                <div className="text-lg font-semibold">{health.metrics.edgeCount}</div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="h-4 w-4 text-purple-600" />
                  <span className="text-sm font-medium">Depth</span>
                </div>
                <div className="text-lg font-semibold">{health.metrics.depth}</div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-orange-600" />
                  <span className="text-sm font-medium">Issues</span>
                </div>
                <div className="text-lg font-semibold">
                  {health.suggestions.filter(s => s.severity === 'critical' || s.severity === 'high').length}
                </div>
              </div>
            </div>

            {/* Top Suggestions */}
            {health.suggestions.length > 0 && (
              <>
                <Separator />
                <div className="space-y-3">
                  <h4 className="text-sm font-medium flex items-center space-x-2">
                    <Lightbulb className="h-4 w-4 text-yellow-600" />
                    <span>Top Recommendations</span>
                  </h4>
                  {health.suggestions.slice(0, 3).map((suggestion, index) => (
                    <div
                      key={suggestion.id}
                      className="p-3 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 mt-0.5">
                          {getSuggestionIcon(suggestion.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-sm font-medium">{suggestion.title}</span>
                            <Badge className={`text-xs ${getSeverityColor(suggestion.severity)}`}>
                              {suggestion.severity}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground">{suggestion.description}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </TabsContent>

          <TabsContent value="scores" className="mt-4 space-y-4">
            {/* Score Breakdown */}
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Zap className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium">Performance</span>
                  </div>
                  <span className="text-sm font-semibold">{health.score.performance}/100</span>
                </div>
                <Progress value={health.score.performance} className="h-2" />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <BarChart3 className="h-4 w-4 text-purple-600" />
                    <span className="text-sm font-medium">Architecture</span>
                  </div>
                  <span className="text-sm font-semibold">{health.score.architecture}/100</span>
                </div>
                <Progress value={health.score.architecture} className="h-2" />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Shield className="h-4 w-4 text-red-600" />
                    <span className="text-sm font-medium">Risk Management</span>
                  </div>
                  <span className="text-sm font-semibold">{health.score.risk}/100</span>
                </div>
                <Progress value={health.score.risk} className="h-2" />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Wrench className="h-4 w-4 text-green-600" />
                    <span className="text-sm font-medium">Maintainability</span>
                  </div>
                  <span className="text-sm font-semibold">{health.score.maintainability}/100</span>
                </div>
                <Progress value={health.score.maintainability} className="h-2" />
              </div>
            </div>

            <Separator />

            {/* Detailed Breakdown */}
            <div className="space-y-3">
              <h4 className="text-sm font-medium">Detailed Breakdown</h4>
              <div className="grid grid-cols-1 gap-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Node Complexity</span>
                  <span className="font-medium">{health.score.breakdown.nodeComplexity}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Connection Efficiency</span>
                  <span className="font-medium">{health.score.breakdown.connectionEfficiency}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Risk Management</span>
                  <span className="font-medium">{health.score.breakdown.riskManagement}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Parameter Optimization</span>
                  <span className="font-medium">{health.score.breakdown.parameterOptimization}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Resource Usage</span>
                  <span className="font-medium">{health.score.breakdown.resourceUsage}/100</span>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="suggestions" className="mt-4">
            <ScrollArea className="h-80">
              <div className="space-y-3">
                {health.suggestions.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="h-12 w-12 mx-auto text-green-600 mb-4" />
                    <h3 className="text-lg font-medium mb-2">All Good!</h3>
                    <p className="text-sm text-muted-foreground">
                      No optimization suggestions at this time.
                    </p>
                  </div>
                ) : (
                  health.suggestions.map((suggestion) => (
                    <Card
                      key={suggestion.id}
                      className="cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start space-x-3">
                          <div className="flex-shrink-0 mt-1">
                            {getSuggestionIcon(suggestion.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-2">
                              <h4 className="text-sm font-medium">{suggestion.title}</h4>
                              <Badge className={`text-xs ${getSeverityColor(suggestion.severity)}`}>
                                {suggestion.severity}
                              </Badge>
                              <Badge variant="outline" className="text-xs">
                                {suggestion.type}
                              </Badge>
                            </div>
                            
                            <p className="text-sm text-muted-foreground mb-2">
                              {suggestion.description}
                            </p>
                            
                            <div className="space-y-2">
                              <div className="text-xs">
                                <span className="font-medium text-red-600">Impact:</span>
                                <span className="ml-1 text-muted-foreground">{suggestion.impact}</span>
                              </div>
                              
                              <div className="text-xs">
                                <span className="font-medium text-blue-600">Suggestion:</span>
                                <span className="ml-1 text-muted-foreground">{suggestion.suggestion}</span>
                              </div>
                              
                              {suggestion.estimatedImpact && (
                                <div className="flex space-x-4 text-xs">
                                  {suggestion.estimatedImpact.performance && (
                                    <span className="text-blue-600">
                                      Performance: +{suggestion.estimatedImpact.performance}%
                                    </span>
                                  )}
                                  {suggestion.estimatedImpact.reliability && (
                                    <span className="text-green-600">
                                      Reliability: +{suggestion.estimatedImpact.reliability}%
                                    </span>
                                  )}
                                  {suggestion.estimatedImpact.maintainability && (
                                    <span className="text-purple-600">
                                      Maintainability: +{suggestion.estimatedImpact.maintainability}%
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="metrics" className="mt-4">
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Structure Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Node Count</span>
                    <span className="font-medium">{health.metrics.nodeCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Edge Count</span>
                    <span className="font-medium">{health.metrics.edgeCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Workflow Depth</span>
                    <span className="font-medium">{health.metrics.depth}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Average Fan-out</span>
                    <span className="font-medium">{health.metrics.fanOut.toFixed(1)}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Complexity Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Cyclomatic Complexity</span>
                    <span className="font-medium">{health.metrics.cyclomaticComplexity}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Technical Debt</span>
                    <span className="font-medium">{health.metrics.technicalDebt}%</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}