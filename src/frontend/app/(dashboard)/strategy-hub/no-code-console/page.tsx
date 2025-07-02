'use client';

import { useState } from 'react';
import { NoCodeWorkflowEditorWrapper } from '@/components/no-code/NoCodeWorkflowEditor';
import { ComponentLibrary } from '@/components/no-code/ComponentLibrary';
import { ConfigurationPanel } from '@/components/no-code/ConfigurationPanel';
import { WorkflowToolbar } from '@/components/no-code/WorkflowToolbar';
import { ClientOnly } from '@/components/no-code/ClientOnly';
import { DatasetSelector } from '@/components/no-code/DatasetSelector';
import { TrainingProgress } from '@/components/no-code/TrainingProgress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Play, Save, Download, Upload, Settings, Database, Zap } from 'lucide-react';

export default function NoCodeConsolePage() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [workflowName, setWorkflowName] = useState('Untitled Strategy');
  const [isTraining, setIsTraining] = useState(false);
  const [currentStep, setCurrentStep] = useState<'design' | 'dataset' | 'training' | 'testing'>('design');

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

  return (
    <div className="h-screen flex flex-col dark:bg-background">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 dark:border-border">
        <div className="flex h-14 items-center justify-between px-4">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold dark:text-foreground">{workflowName}</h1>
            <Badge variant={currentStep === 'design' ? 'default' : 'secondary'}>
              {currentStep === 'design' && 'Design'}
              {currentStep === 'dataset' && 'Dataset Selection'}
              {currentStep === 'training' && 'Training'}
              {currentStep === 'testing' && 'Testing'}
            </Badge>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Save className="h-4 w-4 mr-2" />
              Save
            </Button>
            <Button variant="outline" size="sm">
              <Upload className="h-4 w-4 mr-2" />
              Import
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button 
              onClick={handleCompileAndTrain}
              disabled={isTraining}
              className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700"
            >
              <Play className="h-4 w-4 mr-2" />
              Compile & Train
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex min-h-0">
        {currentStep === 'design' && (
          <>
            {/* Component Library Sidebar */}
            <div className="w-80 border-r bg-background/50 dark:border-border dark:bg-background/50 flex flex-col">
              <ClientOnly fallback={<div className="p-4">Loading components...</div>}>
                <ComponentLibrary />
              </ClientOnly>
            </div>

            {/* Main Workflow Editor */}
            <div className="flex-1 flex flex-col min-w-0">
              <WorkflowToolbar />
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
            <div className="w-80 border-l bg-background/50 dark:border-border dark:bg-background/50 flex flex-col">
              <ClientOnly fallback={<div className="p-4">Loading settings...</div>}>
                <ConfigurationPanel selectedNode={selectedNode} />
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