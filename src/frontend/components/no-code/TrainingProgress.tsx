'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/no-code/card';
import { Button } from '@/components/ui/no-code/button';
import { Badge } from '@/components/ui/no-code/badge';
import { Progress } from '@/components/ui/no-code/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/no-code/tabs';
import { 
  Play, 
  Pause, 
  Square, 
  Activity, 
  Cpu, 
  MemoryStick,
  Clock,
  TrendingUp,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

interface TrainingProgressProps {
  onComplete: () => void;
  onCancel: () => void;
}

export function TrainingProgress({ onComplete, onCancel }: TrainingProgressProps) {
  const [progress, setProgress] = useState(0);
  const [currentEpoch, setCurrentEpoch] = useState(0);
  const [totalEpochs] = useState(100);
  const [isRunning, setIsRunning] = useState(true);
  const [trainingLoss, setTrainingLoss] = useState(0.0);
  const [validationLoss, setValidationLoss] = useState(0.0);
  const [eta, setEta] = useState('Calculating...');

  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      setCurrentEpoch(prev => {
        const newEpoch = prev + 1;
        const newProgress = (newEpoch / totalEpochs) * 100;
        setProgress(newProgress);
        
        // Simulate training metrics
        setTrainingLoss(0.5 - (newEpoch / totalEpochs) * 0.3 + Math.random() * 0.1);
        setValidationLoss(0.6 - (newEpoch / totalEpochs) * 0.35 + Math.random() * 0.1);
        
        // Calculate ETA
        const remainingEpochs = totalEpochs - newEpoch;
        const timePerEpoch = 30; // seconds
        const remainingTime = remainingEpochs * timePerEpoch;
        const hours = Math.floor(remainingTime / 3600);
        const minutes = Math.floor((remainingTime % 3600) / 60);
        setEta(`${hours}h ${minutes}m`);
        
        if (newEpoch >= totalEpochs) {
          setIsRunning(false);
          setTimeout(() => onComplete(), 2000);
        }
        
        return newEpoch;
      });
    }, 1000); // Simulate 1 epoch per second for demo

    return () => clearInterval(interval);
  }, [isRunning, totalEpochs, onComplete]);

  const handlePause = () => {
    setIsRunning(!isRunning);
  };

  const handleStop = () => {
    setIsRunning(false);
    onCancel();
  };

  const resourceUsage = {
    cpu: 85,
    memory: 65,
    gpu: 92
  };

  const trainingMetrics = [
    { epoch: 1, trainLoss: 0.45, valLoss: 0.52, accuracy: 0.62 },
    { epoch: 10, trainLoss: 0.32, valLoss: 0.38, accuracy: 0.74 },
    { epoch: 20, trainLoss: 0.28, valLoss: 0.31, accuracy: 0.79 },
    { epoch: 30, trainLoss: 0.25, valLoss: 0.29, accuracy: 0.82 },
    { epoch: currentEpoch, trainLoss: trainingLoss, valLoss: validationLoss, accuracy: 0.85 }
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold">Training in Progress</h2>
        <p className="text-muted-foreground">
          Your model is being trained on the selected dataset
        </p>
      </div>

      {/* Training Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center">
              <Activity className="h-4 w-4 mr-2" />
              Training Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Progress</span>
                <Badge variant={isRunning ? "default" : "secondary"}>
                  {isRunning ? "Running" : "Paused"}
                </Badge>
              </div>
              <Progress value={progress} className="h-2" />
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Epoch {currentEpoch}/{totalEpochs}</span>
                <span>{progress.toFixed(1)}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center">
              <Clock className="h-4 w-4 mr-2" />
              Time Estimate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>ETA:</span>
                <span className="font-medium">{eta}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Elapsed:</span>
                <span className="font-medium">{Math.floor(currentEpoch * 30 / 60)}m {(currentEpoch * 30) % 60}s</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Per Epoch:</span>
                <span className="font-medium">~30s</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center">
              <TrendingUp className="h-4 w-4 mr-2" />
              Current Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Train Loss:</span>
                <span className="font-medium">{trainingLoss.toFixed(4)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Val Loss:</span>
                <span className="font-medium">{validationLoss.toFixed(4)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Accuracy:</span>
                <span className="font-medium">85.2%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Training Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Training Controls</CardTitle>
          <CardDescription>
            Control your training process and monitor resource usage
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Button 
                size="sm" 
                variant={isRunning ? "outline" : "default"}
                onClick={handlePause}
              >
                {isRunning ? (
                  <>
                    <Pause className="h-4 w-4 mr-2" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Resume
                  </>
                )}
              </Button>
              <Button 
                size="sm" 
                variant="destructive"
                onClick={handleStop}
              >
                <Square className="h-4 w-4 mr-2" />
                Stop
              </Button>
            </div>
            
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <Cpu className="h-4 w-4 text-muted-foreground" />
                <span>CPU: {resourceUsage.cpu}%</span>
              </div>
              <div className="flex items-center space-x-2">
                <MemoryStick className="h-4 w-4 text-muted-foreground" />
                <span>Memory: {resourceUsage.memory}%</span>
              </div>
              <div className="flex items-center space-x-2">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span>GPU: {resourceUsage.gpu}%</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Metrics */}
      <Tabs defaultValue="metrics" className="w-full">
        <TabsList>
          <TabsTrigger value="metrics">Training Metrics</TabsTrigger>
          <TabsTrigger value="logs">Training Logs</TabsTrigger>
          <TabsTrigger value="resources">Resource Usage</TabsTrigger>
        </TabsList>

        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle>Training History</CardTitle>
              <CardDescription>
                Loss and accuracy metrics over training epochs
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-4 gap-4 text-sm font-medium border-b pb-2">
                  <span>Epoch</span>
                  <span>Train Loss</span>
                  <span>Val Loss</span>
                  <span>Accuracy</span>
                </div>
                {trainingMetrics.map((metric, index) => (
                  <div key={index} className="grid grid-cols-4 gap-4 text-sm py-2 border-b">
                    <span>{metric.epoch}</span>
                    <span>{metric.trainLoss.toFixed(4)}</span>
                    <span>{metric.valLoss.toFixed(4)}</span>
                    <span>{(metric.accuracy * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>Training Logs</CardTitle>
              <CardDescription>
                Real-time training output and system messages
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
                <div className="space-y-1">
                  <div>[2024-01-01 12:00:00] Starting training session...</div>
                  <div>[2024-01-01 12:00:01] Loading dataset: crypto-1h-2020-2024</div>
                  <div>[2024-01-01 12:00:02] Dataset loaded: 2.5M records</div>
                  <div>[2024-01-01 12:00:03] Initializing model architecture...</div>
                  <div>[2024-01-01 12:00:04] Model initialized with 1.2M parameters</div>
                  <div>[2024-01-01 12:00:05] Starting epoch 1/100...</div>
                  <div>[2024-01-01 12:00:35] Epoch 1 completed - Loss: 0.45, Val Loss: 0.52</div>
                  <div>[2024-01-01 12:01:05] Epoch 2 completed - Loss: 0.43, Val Loss: 0.50</div>
                  <div className="text-yellow-400">[2024-01-01 12:01:35] Epoch {currentEpoch} in progress...</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resources">
          <Card>
            <CardHeader>
              <CardTitle>Resource Monitoring</CardTitle>
              <CardDescription>
                System resource usage during training
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">CPU Usage</span>
                    <span className="text-sm">{resourceUsage.cpu}%</span>
                  </div>
                  <Progress value={resourceUsage.cpu} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Memory Usage</span>
                    <span className="text-sm">{resourceUsage.memory}%</span>
                  </div>
                  <Progress value={resourceUsage.memory} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">GPU Usage</span>
                    <span className="text-sm">{resourceUsage.gpu}%</span>
                  </div>
                  <Progress value={resourceUsage.gpu} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Status Messages */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2 text-sm text-green-600">
          <CheckCircle className="h-4 w-4" />
          <span>Data preprocessing completed</span>
        </div>
        <div className="flex items-center space-x-2 text-sm text-green-600">
          <CheckCircle className="h-4 w-4" />
          <span>Model architecture validated</span>
        </div>
        <div className="flex items-center space-x-2 text-sm text-blue-600">
          <Activity className="h-4 w-4" />
          <span>Training in progress - Epoch {currentEpoch}/{totalEpochs}</span>
        </div>
        {currentEpoch >= totalEpochs && (
          <div className="flex items-center space-x-2 text-sm text-green-600">
            <CheckCircle className="h-4 w-4" />
            <span>Training completed successfully!</span>
          </div>
        )}
      </div>
    </div>
  );
}