'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { 
  Play, 
  Square, 
  RotateCcw, 
  ZoomIn, 
  ZoomOut, 
  Maximize, 
  Eye,
  Code,
  Code2,
  TestTube,
  Save,
  Sun,
  Moon,
  HelpCircle,
  Download,
  Upload,
  Share,
  Copy
} from 'lucide-react';
import { useTheme } from 'next-themes';
import { useNoCodeStore } from '@/lib/stores/no-code-store';
import { WorkflowExporter } from '@/lib/workflow-export';
import { CodeViewer } from './CodeViewer';

export function WorkflowToolbar() {
  const { theme, setTheme } = useTheme();
  const { currentWorkflow, loadWorkflow } = useNoCodeStore();
  const [mounted, setMounted] = useState(false);
  const [showCodeViewer, setShowCodeViewer] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  const handleExportWorkflow = () => {
    if (!currentWorkflow) return;
    
    try {
      WorkflowExporter.downloadWorkflow(currentWorkflow, {
        author: 'User',
        tags: ['exported']
      });
      console.log('Workflow exported successfully');
    } catch (error) {
      console.error('Failed to export workflow:', error);
    }
  };

  const handleImportWorkflow = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      WorkflowExporter.importWorkflowFromFile(file)
        .then(workflow => {
          loadWorkflow(workflow);
          console.log('Workflow imported successfully');
        })
        .catch(error => {
          console.error('Failed to import workflow:', error);
        });
    };
    input.click();
  };

  const handleShareWorkflow = () => {
    if (!currentWorkflow) return;
    
    try {
      const shareUrl = WorkflowExporter.workflowToShareableUrl(currentWorkflow);
      navigator.clipboard.writeText(shareUrl);
      console.log('Share URL copied to clipboard');
    } catch (error) {
      console.error('Failed to create share URL:', error);
    }
  };

  const handleCopyWorkflow = () => {
    if (!currentWorkflow) return;
    
    try {
      WorkflowExporter.copyWorkflowToClipboard(currentWorkflow);
      console.log('Workflow copied to clipboard');
    } catch (error) {
      console.error('Failed to copy workflow:', error);
    }
  };

  const handleGenerateCode = () => {
    if (!currentWorkflow) {
      console.log('No workflow available for code generation');
      return;
    }
    
    if (currentWorkflow.nodes.length === 0) {
      console.log('Workflow is empty - add nodes to generate code');
      return;
    }
    
    setShowCodeViewer(true);
  };

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-background/95 backdrop-blur border-b dark:border-border dark:bg-background/95">
      <div className="flex items-center space-x-2">
        {/* Execution Controls */}
        <Button size="sm" variant="outline">
          <Play className="h-4 w-4 mr-1" />
          Run
        </Button>
        <Button size="sm" variant="outline">
          <Square className="h-4 w-4 mr-1" />
          Stop
        </Button>
        <Button size="sm" variant="outline">
          <RotateCcw className="h-4 w-4 mr-1" />
          Reset
        </Button>
        
        <Separator orientation="vertical" className="h-6" />
        
        {/* View Controls */}
        <Button size="sm" variant="ghost">
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button size="sm" variant="ghost">
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button size="sm" variant="ghost">
          <Maximize className="h-4 w-4" />
        </Button>
        
        <Separator orientation="vertical" className="h-6" />
        
        {/* Mode Toggle */}
        <Button size="sm" variant="ghost">
          <Eye className="h-4 w-4 mr-1" />
          Visual
        </Button>
        <Button 
          size="sm" 
          variant="outline"
          onClick={handleGenerateCode}
          disabled={!currentWorkflow || currentWorkflow.nodes.length === 0}
          title={
            !currentWorkflow 
              ? 'No workflow loaded' 
              : currentWorkflow.nodes.length === 0 
                ? 'Add nodes to generate code'
                : 'Generate Python trading strategy code'
          }
        >
          <Code2 className="h-4 w-4 mr-1" />
          Generate Code
        </Button>
      </div>

      <div className="flex items-center space-x-2">
        {/* Status Indicators */}
        <Badge variant="secondary" className="text-xs">
          {currentWorkflow?.nodes?.length || 0} nodes
        </Badge>
        <Badge variant="secondary" className="text-xs">
          {currentWorkflow?.edges?.length || 0} connections
        </Badge>
        
        <Separator orientation="vertical" className="h-6" />
        
        {/* Action Buttons */}
        <Button size="sm" variant="outline">
          <TestTube className="h-4 w-4 mr-1" />
          Test
        </Button>
        <Button size="sm" variant="outline">
          <Save className="h-4 w-4 mr-1" />
          Save
        </Button>
        
        <Separator orientation="vertical" className="h-6" />
        
        {/* Export/Import Actions */}
        <Button size="sm" variant="ghost" onClick={handleExportWorkflow} title="Export workflow">
          <Download className="h-4 w-4" />
        </Button>
        <Button size="sm" variant="ghost" onClick={handleImportWorkflow} title="Import workflow">
          <Upload className="h-4 w-4" />
        </Button>
        <Button size="sm" variant="ghost" onClick={handleShareWorkflow} title="Share workflow">
          <Share className="h-4 w-4" />
        </Button>
        <Button size="sm" variant="ghost" onClick={handleCopyWorkflow} title="Copy workflow">
          <Copy className="h-4 w-4" />
        </Button>
        
        <Separator orientation="vertical" className="h-6" />
        
        {/* Help */}
        <Button 
          size="sm" 
          variant="ghost" 
          title="Help: Select edges and press Delete/Backspace to remove connections"
        >
          <HelpCircle className="h-4 w-4" />
        </Button>
        
        {/* Theme Toggle */}
        <Button size="sm" variant="ghost" onClick={toggleTheme} suppressHydrationWarning>
          {!mounted ? (
            <Sun className="h-4 w-4" />
          ) : theme === 'dark' ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Code Viewer Modal */}
      <CodeViewer
        isOpen={showCodeViewer}
        onClose={() => setShowCodeViewer(false)}
      />
    </div>
  );
}