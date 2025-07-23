'use client';

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { Button } from '@/components/ui/no-code/button';
import { Input } from '@/components/ui/no-code/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/no-code/tabs';
import { ScrollArea } from '@/components/ui/no-code/scroll-area';
import { Separator } from '@/components/ui/no-code/separator';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/no-code/dialog';
import { 
  Search, 
  TrendingUp, 
  Target, 
  ArrowUpDown, 
  Zap, 
  Shield, 
  Clock,
  Download,
  Eye,
  Filter,
  BarChart3
} from 'lucide-react';
import { 
  workflowTemplates, 
  searchTemplates,
  WorkflowTemplate 
} from '@/lib/workflow-templates';
import { useNoCodeStore } from '@/lib/stores/no-code-store';

interface TemplateLibraryProps {
  onTemplateSelect?: (template: WorkflowTemplate) => void;
  className?: string;
}

export function TemplateLibrary({ onTemplateSelect, className }: TemplateLibraryProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);
  const { loadWorkflow } = useNoCodeStore();

  // Filter templates based on search and filters
  const filteredTemplates = useMemo(() => {
    let templates = workflowTemplates;

    // Apply search filter
    if (searchQuery.trim()) {
      templates = searchTemplates(searchQuery);
    }

    // Apply category filter
    if (selectedCategory !== 'all') {
      templates = templates.filter(t => t.category === selectedCategory);
    }

    // Apply difficulty filter
    if (selectedDifficulty !== 'all') {
      templates = templates.filter(t => t.difficulty === selectedDifficulty);
    }

    return templates;
  }, [searchQuery, selectedCategory, selectedDifficulty]);

  const handleApplyTemplate = (template: WorkflowTemplate) => {
    // Load template into the workflow editor
    loadWorkflow({
      id: `template-${template.id}-${Date.now()}`,
      name: `${template.name} (Copy)`,
      description: template.description,
      nodes: template.nodes,
      edges: template.edges,
      parameters: {},
      createdAt: new Date().toISOString(),
      lastModified: new Date().toISOString()
    });

    if (onTemplateSelect) {
      onTemplateSelect(template);
    }
  };

  const getCategoryIcon = (category: WorkflowTemplate['category']) => {
    switch (category) {
      case 'momentum': return <TrendingUp className="h-4 w-4" />;
      case 'mean_reversion': return <Target className="h-4 w-4" />;
      case 'trend_following': return <ArrowUpDown className="h-4 w-4" />;
      case 'arbitrage': return <Zap className="h-4 w-4" />;
      case 'risk_management': return <Shield className="h-4 w-4" />;
      case 'scalping': return <Clock className="h-4 w-4" />;
      case 'swing': return <BarChart3 className="h-4 w-4" />;
      case 'breakout': return <TrendingUp className="h-4 w-4" />;
      default: return <BarChart3 className="h-4 w-4" />;
    }
  };

  const getCategoryColor = (category: WorkflowTemplate['category']) => {
    switch (category) {
      case 'momentum': return 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/30 dark:text-blue-400';
      case 'mean_reversion': return 'bg-green-100 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-400';
      case 'trend_following': return 'bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-900/30 dark:text-purple-400';
      case 'arbitrage': return 'bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'risk_management': return 'bg-red-100 text-red-800 border-red-300 dark:bg-red-900/30 dark:text-red-400';
      case 'scalping': return 'bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-900/30 dark:text-orange-400';
      case 'swing': return 'bg-indigo-100 text-indigo-800 border-indigo-300 dark:bg-indigo-900/30 dark:text-indigo-400';
      case 'breakout': return 'bg-pink-100 text-pink-800 border-pink-300 dark:bg-pink-900/30 dark:text-pink-400';
      default: return 'bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-900/30 dark:text-gray-400';
    }
  };

  const getDifficultyColor = (difficulty: WorkflowTemplate['difficulty']) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'advanced': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
    }
  };

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'momentum', label: 'Momentum' },
    { value: 'mean_reversion', label: 'Mean Reversion' },
    { value: 'trend_following', label: 'Trend Following' },
    { value: 'arbitrage', label: 'Arbitrage' },
    { value: 'risk_management', label: 'Risk Management' },
    { value: 'scalping', label: 'Scalping' },
    { value: 'swing', label: 'Swing Trading' },
    { value: 'breakout', label: 'Breakout' }
  ];

  const difficulties = [
    { value: 'all', label: 'All Levels' },
    { value: 'beginner', label: 'Beginner' },
    { value: 'intermediate', label: 'Intermediate' },
    { value: 'advanced', label: 'Advanced' }
  ];

  return (
    <div className={`h-full flex flex-col ${className}`}>
      {/* Header */}
      <div className="p-4 border-b dark:border-border">
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold">Strategy Templates</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Choose from {workflowTemplates.length} pre-built trading strategies
            </p>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500 dark:text-gray-400" />
            <Input
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Filters */}
          <div className="flex space-x-2">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="flex-1 px-3 py-2 text-sm border rounded-md bg-background text-gray-900 dark:text-gray-100"
            >
              {categories.map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>

            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="flex-1 px-3 py-2 text-sm border rounded-md bg-background text-gray-900 dark:text-gray-100"
            >
              {difficulties.map(diff => (
                <option key={diff.value} value={diff.value}>{diff.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Templates Grid */}
      <ScrollArea className="flex-1 p-4">
        <div className="grid gap-4">
          {filteredTemplates.length === 0 ? (
            <div className="text-center py-8">
              <Filter className="h-12 w-12 mx-auto text-gray-500 dark:text-gray-400 mb-4" />
              <h3 className="text-lg font-medium mb-2">No templates found</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Try adjusting your search or filters
              </p>
            </div>
          ) : (
            filteredTemplates.map((template) => (
              <Card key={template.id} className="hover:shadow-md transition-shadow cursor-pointer group">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        {getCategoryIcon(template.category)}
                        <CardTitle className="text-base">{template.name}</CardTitle>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge className={`text-xs ${getCategoryColor(template.category)}`}>
                          {template.category.replace('_', ' ')}
                        </Badge>
                        <Badge variant="outline" className={`text-xs ${getDifficultyColor(template.difficulty)}`}>
                          {template.difficulty}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedTemplate(template)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl">
                          <DialogHeader>
                            <DialogTitle className="flex items-center space-x-2">
                              {getCategoryIcon(template.category)}
                              <span>{template.name}</span>
                            </DialogTitle>
                            <DialogDescription>
                              {template.description}
                            </DialogDescription>
                          </DialogHeader>
                          
                          {selectedTemplate && (
                            <div className="space-y-4">
                              {/* Template Details */}
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <h4 className="text-sm font-medium mb-2">Performance Metrics</h4>
                                  <div className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
                                    {selectedTemplate.expectedReturn && (
                                      <div>Expected Return: <span className="font-medium">{selectedTemplate.expectedReturn}</span></div>
                                    )}
                                    {selectedTemplate.maxDrawdown && (
                                      <div>Max Drawdown: <span className="font-medium">{selectedTemplate.maxDrawdown}</span></div>
                                    )}
                                    {selectedTemplate.sharpeRatio && (
                                      <div>Sharpe Ratio: <span className="font-medium">{selectedTemplate.sharpeRatio}</span></div>
                                    )}
                                    {selectedTemplate.winRate && (
                                      <div>Win Rate: <span className="font-medium">{selectedTemplate.winRate}</span></div>
                                    )}
                                  </div>
                                </div>
                                
                                <div>
                                  <h4 className="text-sm font-medium mb-2">Specifications</h4>
                                  <div className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
                                    <div>Timeframes: <span className="font-medium">{selectedTemplate.timeframe.join(', ')}</span></div>
                                    <div>Assets: <span className="font-medium">{selectedTemplate.assetClasses.join(', ')}</span></div>
                                    <div>Nodes: <span className="font-medium">{selectedTemplate.nodes.length}</span></div>
                                    <div>Connections: <span className="font-medium">{selectedTemplate.edges.length}</span></div>
                                  </div>
                                </div>
                              </div>

                              {/* Tags */}
                              <div>
                                <h4 className="text-sm font-medium mb-2">Tags</h4>
                                <div className="flex flex-wrap gap-1">
                                  {selectedTemplate.tags.map((tag, index) => (
                                    <Badge key={index} variant="outline" className="text-xs">
                                      {tag}
                                    </Badge>
                                  ))}
                                </div>
                              </div>

                              {/* Apply Button */}
                              <div className="flex justify-end space-x-2">
                                <Button
                                  onClick={() => handleApplyTemplate(selectedTemplate)}
                                  className="flex items-center space-x-2"
                                >
                                  <Download className="h-4 w-4" />
                                  <span>Apply Template</span>
                                </Button>
                              </div>
                            </div>
                          )}
                        </DialogContent>
                      </Dialog>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                    {template.description}
                  </p>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600 dark:text-gray-400">Timeframes:</span>
                      <span className="font-medium">{template.timeframe.join(', ')}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600 dark:text-gray-400">Assets:</span>
                      <span className="font-medium">{template.assetClasses.join(', ')}</span>
                    </div>
                    {template.expectedReturn && (
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-600 dark:text-gray-400">Expected Return:</span>
                        <span className="font-medium text-green-600 dark:text-green-400">{template.expectedReturn}</span>
                      </div>
                    )}
                  </div>

                  <Separator className="my-3" />

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1 text-xs text-gray-600 dark:text-gray-400">
                      <span>{template.nodes.length} nodes</span>
                      <span>•</span>
                      <span>{template.edges.length} connections</span>
                    </div>
                    
                    <Button
                      size="sm"
                      onClick={() => handleApplyTemplate(template)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Apply
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}