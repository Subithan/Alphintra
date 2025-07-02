'use client';

import React from 'react';
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
  TestTube,
  Save,
  Sun,
  Moon,
  HelpCircle
} from 'lucide-react';
import { useTheme } from 'next-themes';
import { useNoCodeStore } from '@/lib/stores/no-code-store';

export function WorkflowToolbar() {
  const { theme, setTheme } = useTheme();
  const { currentWorkflow } = useNoCodeStore();

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
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
        <Button size="sm" variant="outline">
          <Code className="h-4 w-4 mr-1" />
          Code
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
        
        {/* Help */}
        <Button 
          size="sm" 
          variant="ghost" 
          title="Help: Select edges and press Delete/Backspace to remove connections"
        >
          <HelpCircle className="h-4 w-4" />
        </Button>
        
        {/* Theme Toggle */}
        <Button size="sm" variant="ghost" onClick={toggleTheme}>
          {theme === 'dark' ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}