'use client';

import { useState } from 'react';
import { NoCodeWorkflowEditorWrapper } from '@/components/no-code/NoCodeWorkflowEditor';
import { ComponentLibrary } from '@/components/no-code/ComponentLibrary';
import { TemplateLibrary } from '@/components/no-code/TemplateLibrary';
import { ConfigurationPanel } from '@/components/no-code/ConfigurationPanel';
import { ClientOnly } from '@/components/no-code/ClientOnly';
import { DatasetSelector } from '@/components/no-code/DatasetSelector';
import { TrainingProgress } from '@/components/no-code/TrainingProgress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Icon } from '@iconify/react';
import { Play, Save, Download, Upload, Settings, Database, Zap, FileText, Pause, RotateCcw, Search, ZoomIn, Eye, Code, TestTube, Sun, Moon } from 'lucide-react';

export default function NoCodeConsolePage() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [workflowName, setWorkflowName] = useState('Untitled Strategy');
  const [isTraining, setIsTraining] = useState(false);
  const [currentStep, setCurrentStep] = useState<'design' | 'dataset' | 'training' | 'testing'>('design');
  const [leftSidebar, setLeftSidebar] = useState<'components' | 'templates'>('components');
  const [nodeCount, setNodeCount] = useState(2);
  const [connectionCount, setConnectionCount] = useState(1);
  const [isDarkMode, setIsDarkMode] = useState(false);

  const handleStepChange = (step: 'design' | 'dataset' | 'training' | 'testing') => {
    setCurrentStep(step);
  };

  const handleCompileAndTrain = () => {
    setCurrentStep('dataset');
  };

  const handleStartTraining = () => {
    setIsTraining(true);
    setCurrentStep('training');
  };

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <div className="h-screen flex flex-col dark:bg-background">
      {/* Header */}
      <div className="border-b bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700">
        <div className="flex h-14 items-center justify-between px-4">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{workflowName}</h1>
            <Badge variant={currentStep === 'design' ? 'default' : 'secondary'}>
              {currentStep === 'design' && 'Design'}
              {currentStep === 'dataset' && 'Dataset Selection'}
              {currentStep === 'training' && 'Training'}
              {currentStep === 'testing' && 'Testing'}
            </Badge>
          </div>
          <div className="flex items-center space-x-2">
            <Button 
              variant="secondary" 
              size="sm"
              onClick={toggleTheme}
              className="p-2"
            >
              {isDarkMode ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
            <Button variant="secondary" size="sm">
              <Save className="h-4 w-4 mr-2" />
              Save
            </Button>
            <Button variant="secondary" size="sm">
              <Upload className="h-4 w-4 mr-2" />
              Import
            </Button>
            <Button variant="secondary" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button 
              onClick={handleCompileAndTrain}
              disabled={isTraining}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Play className="h-4 w-4 mr-2" />
              Compile & Train
            </Button>
          </div>
        </div>
      </div>

      {/* Workflow Toolbar */}
      <div className="border-b bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
        <div className="flex h-12 items-center justify-between px-4">
          {/* Left Section - Control Buttons */}
          <div className="flex items-center space-x-3">
            <Button size="sm" className="bg-green-600 hover:bg-green-700">
              <Play className="h-4 w-4 mr-1" />
              Run
            </Button>
            <Button size="sm" variant="secondary">
              <Pause className="h-4 w-4 mr-1" />
              Stop
            </Button>
            <Button size="sm" variant="secondary">
              <RotateCcw className="h-4 w-4 mr-1" />
              Reset
            </Button>
            
            <div className="w-px h-6 bg-border mx-2"></div>
            
            <Button size="sm" variant="secondary" className="p-2">
              <Search className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="secondary" className="p-2">
              <Search className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="secondary" className="p-2">
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>

          {/* Center Section - View Controls */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Button size="sm" variant="secondary">
                <Eye className="h-4 w-4 mr-1" />
                Visual
              </Button>
              <Button size="sm" variant="secondary">
                <Code className="h-4 w-4 mr-1" />
                Generate Code
              </Button>
            </div>
            
            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
              <div className="flex items-center space-x-1">
                <span className="font-medium">{nodeCount}</span>
                <span>nodes</span>
              </div>
              <div className="flex items-center space-x-1">
                <span className="font-medium">{connectionCount}</span>
                <span>connections</span>
              </div>
            </div>
          </div>

          {/* Right Section - Additional Actions */}
          <div className="flex items-center space-x-2">
            <Button size="sm" variant="secondary">
              <TestTube className="h-4 w-4 mr-1" />
              Test
            </Button>
            <Button size="sm" variant="secondary">
              <Save className="h-4 w-4 mr-1" />
              Save
            </Button>
            <Button size="sm" variant="secondary" className="p-2">
              <Download className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="secondary" className="p-2">
              <Upload className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="secondary" className="p-2">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex min-h-0">
        {currentStep === 'design' && (
          <>
            {/* Left Sidebar - Components/Templates */}
            <div className="w-80 border-r bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 flex flex-col">
              {/* Sidebar Tabs */}
              <div className="border-b border-gray-200 dark:border-gray-700">
                <Tabs value={leftSidebar} onValueChange={(value) => setLeftSidebar(value as 'components' | 'templates')} className="w-full">
                  <TabsList className="grid w-full grid-cols-2 rounded-none">
                    <TabsTrigger value="components" className="flex items-center space-x-2">
                      <Database className="h-4 w-4" />
                      <span>Components</span>
                    </TabsTrigger>
                    <TabsTrigger value="templates" className="flex items-center space-x-2">
                      <FileText className="h-4 w-4" />
                      <span>Templates</span>
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              {/* Sidebar Content */}
              <div className="flex-1 overflow-hidden">
                {leftSidebar === 'components' && (
                  <ClientOnly fallback={<div className="p-4">Loading components...</div>}>
                    <ComponentLibrary />
                  </ClientOnly>
                )}
                {leftSidebar === 'templates' && (
                  <ClientOnly fallback={<div className="p-4">Loading templates...</div>}>
                    <TemplateLibrary onTemplateSelect={() => setLeftSidebar('components')} />
                  </ClientOnly>
                )}
              </div>
            </div>

            {/* Main Workflow Editor */}
            <div className="flex-1 flex flex-col min-w-0">
              <div className="flex-1 relative overflow-hidden">
                <ClientOnly fallback={
                  <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                      <p className="text-sm text-muted-foreground">Loading workflow editor...</p>
                    </div>
                  </div>
                }>
                  <NoCodeWorkflowEditorWrapper
                    selectedNode={selectedNode}
                    onNodeSelect={setSelectedNode}
                  />
                </ClientOnly>
              </div>
            </div>

            {/* Configuration Panel */}
            <div className="w-80 border-l bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 flex flex-col">
              <ClientOnly fallback={<div className="p-4">Loading settings...</div>}>
                <ConfigurationPanel 
                  selectedNode={selectedNode} 
                  onNodeSelect={setSelectedNode}
                />
              </ClientOnly>
            </div>
          </>
        )}

        {currentStep === 'dataset' && (
          <div className="flex-1 p-6">
            <DatasetSelector onNext={handleStartTraining} />
          </div>
        )}

        {currentStep === 'training' && (
          <div className="flex-1 p-6">
            <TrainingProgress 
              onComplete={() => setCurrentStep('testing')}
              onCancel={() => setCurrentStep('design')}
            />
          </div>
        )}

        {currentStep === 'testing' && (
          <div className="flex-1 p-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Zap className="h-5 w-5 mr-2" />
                  Model Testing & Validation
                </CardTitle>
                <CardDescription>
                  Your model is being tested for security, performance, and accuracy.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <span>Security Validation</span>
                    <Badge variant="default">Passed</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <span>Performance Benchmarks</span>
                    <Badge variant="default">Passed</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <span>Accuracy Testing</span>
                    <Badge variant="default">Passed</Badge>
                  </div>
                  <Button 
                    className="w-full"
                    onClick={() => setCurrentStep('design')}
                  >
                    Deploy Model
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}