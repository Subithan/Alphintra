"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { AlertCircle, Clock, Zap, Settings, TrendingUp, Brain, CheckCircle, ArrowRight } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface ExecutionModeConfig {
  // Strategy Mode Config
  backtest_start?: string
  backtest_end?: string
  initial_capital?: number
  commission?: number
  
  // Model Mode Config
  optimization_objective?: string
  max_trials?: number
  timeout_hours?: number
  instance_type?: string
  priority?: string
  advanced_options?: {
    early_stopping?: boolean
    cross_validation_folds?: number
    validation_split?: number
    parameter_space_reduction?: boolean
  }
}

interface ExecutionModeSelectorProps {
  workflowId: number
  workflowName: string
  workflowComplexity?: 'simple' | 'medium' | 'complex'
  onModeSelect: (mode: 'strategy' | 'model', config: ExecutionModeConfig) => void
  onCancel?: () => void
  isLoading?: boolean
  estimatedDuration?: {
    strategy: string
    model: string
  }
}

export function ExecutionModeSelector({
  workflowId,
  workflowName,
  workflowComplexity = 'medium',
  onModeSelect,
  onCancel,
  isLoading = false,
  estimatedDuration = { strategy: '< 1 minute', model: '2-6 hours' }
}: ExecutionModeSelectorProps) {
  const [selectedMode, setSelectedMode] = useState<'strategy' | 'model' | null>(null)
  const [strategyConfig, setStrategyConfig] = useState<ExecutionModeConfig>({
    backtest_start: '2023-01-01',
    backtest_end: '2023-12-31',
    initial_capital: 10000,
    commission: 0.001
  })
  const [modelConfig, setModelConfig] = useState<ExecutionModeConfig>({
    optimization_objective: 'sharpe_ratio',
    max_trials: 100,
    timeout_hours: 24,
    instance_type: 'CPU_MEDIUM',
    priority: 'normal',
    advanced_options: {
      early_stopping: true,
      cross_validation_folds: 5,
      validation_split: 0.2,
      parameter_space_reduction: false
    }
  })
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false)

  const handleExecute = () => {
    if (!selectedMode) return
    
    const config = selectedMode === 'strategy' ? strategyConfig : modelConfig
    onModeSelect(selectedMode, config)
  }

  const getComplexityInfo = () => {
    switch (workflowComplexity) {
      case 'simple':
        return {
          badge: 'Simple',
          color: 'bg-green-100 text-green-800',
          recommendations: {
            strategy: 'Perfect for quick testing and immediate results',
            model: 'Basic optimization will complete quickly (1-2 hours)'
          }
        }
      case 'medium':
        return {
          badge: 'Medium',
          color: 'bg-yellow-100 text-yellow-800',
          recommendations: {
            strategy: 'Good for standard backtesting with your parameters',
            model: 'Thorough optimization recommended (4-8 hours)'
          }
        }
      case 'complex':
        return {
          badge: 'Complex',
          color: 'bg-red-100 text-red-800',
          recommendations: {
            strategy: 'May need parameter tuning for optimal results',
            model: 'Highly recommended for best performance (8-24 hours)'
          }
        }
    }
  }

  const complexityInfo = getComplexityInfo()

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Choose Execution Mode</h2>
        <p className="text-muted-foreground">
          How would you like to execute "{workflowName}"?
        </p>
        <div className="flex items-center justify-center space-x-2">
          <Badge variant="outline">Workflow ID: {workflowId}</Badge>
          <Badge className={complexityInfo.color}>{complexityInfo.badge} Complexity</Badge>
        </div>
      </div>

      {/* Mode Selection Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Strategy Mode Card */}
        <Card 
          className={`cursor-pointer transition-all duration-200 ${
            selectedMode === 'strategy' 
              ? 'ring-2 ring-blue-500 shadow-lg' 
              : 'hover:shadow-md'
          }`}
          onClick={() => setSelectedMode('strategy')}
        >
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Zap className="h-6 w-6 text-blue-600" />
              <CardTitle className="text-xl">Strategy Mode</CardTitle>
              <Badge variant="outline" className="text-xs">Quick</Badge>
            </div>
            <CardDescription>
              Execute immediately with your specified parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>Duration: {estimatedDuration.strategy}</span>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium text-sm">What happens:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li className="flex items-center space-x-2">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  <span>Uses your exact parameter values</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  <span>Generates executable strategy code</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  <span>Ready for immediate backtesting</span>
                </li>
              </ul>
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-xs">
                {complexityInfo.recommendations.strategy}
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>

        {/* Model Mode Card */}
        <Card 
          className={`cursor-pointer transition-all duration-200 ${
            selectedMode === 'model' 
              ? 'ring-2 ring-purple-500 shadow-lg' 
              : 'hover:shadow-md'
          }`}
          onClick={() => setSelectedMode('model')}
        >
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Brain className="h-6 w-6 text-purple-600" />
              <CardTitle className="text-xl">Model Mode</CardTitle>
              <Badge variant="outline" className="text-xs bg-purple-50">AI Optimized</Badge>
            </div>
            <CardDescription>
              Use ML to find optimal parameters for maximum performance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>Duration: {estimatedDuration.model}</span>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium text-sm">What happens:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li className="flex items-center space-x-2">
                  <TrendingUp className="h-3 w-3 text-purple-500" />
                  <span>ML discovers optimal parameters</span>
                </li>
                <li className="flex items-center space-x-2">
                  <TrendingUp className="h-3 w-3 text-purple-500" />
                  <span>Extensive backtesting & validation</span>
                </li>
                <li className="flex items-center space-x-2">
                  <TrendingUp className="h-3 w-3 text-purple-500" />
                  <span>Performance-optimized strategy code</span>
                </li>
              </ul>
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-xs">
                {complexityInfo.recommendations.model}
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>

      {/* Configuration Panel */}
      {selectedMode && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>
                {selectedMode === 'strategy' ? 'Strategy Configuration' : 'Model Training Configuration'}
              </span>
            </CardTitle>
            <CardDescription>
              {selectedMode === 'strategy' 
                ? 'Configure backtesting parameters for your strategy'
                : 'Configure ML training parameters for optimization'
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {selectedMode === 'strategy' ? (
              // Strategy Mode Configuration
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="backtest-start">Backtest Start Date</Label>
                  <Input
                    id="backtest-start"
                    type="date"
                    value={strategyConfig.backtest_start}
                    onChange={(e) => setStrategyConfig(prev => ({
                      ...prev,
                      backtest_start: e.target.value
                    }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="backtest-end">Backtest End Date</Label>
                  <Input
                    id="backtest-end"
                    type="date"
                    value={strategyConfig.backtest_end}
                    onChange={(e) => setStrategyConfig(prev => ({
                      ...prev,
                      backtest_end: e.target.value
                    }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="initial-capital">Initial Capital ($)</Label>
                  <Input
                    id="initial-capital"
                    type="number"
                    value={strategyConfig.initial_capital}
                    onChange={(e) => setStrategyConfig(prev => ({
                      ...prev,
                      initial_capital: parseFloat(e.target.value)
                    }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="commission">Commission (%)</Label>
                  <Input
                    id="commission"
                    type="number"
                    step="0.001"
                    value={strategyConfig.commission}
                    onChange={(e) => setStrategyConfig(prev => ({
                      ...prev,
                      commission: parseFloat(e.target.value)
                    }))}
                  />
                </div>
              </div>
            ) : (
              // Model Mode Configuration
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="optimization-objective">Optimization Objective</Label>
                    <Select
                      value={modelConfig.optimization_objective}
                      onValueChange={(value) => setModelConfig(prev => ({
                        ...prev,
                        optimization_objective: value
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select objective" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="sharpe_ratio">Sharpe Ratio</SelectItem>
                        <SelectItem value="sortino_ratio">Sortino Ratio</SelectItem>
                        <SelectItem value="calmar_ratio">Calmar Ratio</SelectItem>
                        <SelectItem value="total_return">Total Return</SelectItem>
                        <SelectItem value="max_drawdown">Max Drawdown</SelectItem>
                        <SelectItem value="profit_factor">Profit Factor</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max-trials">Max Optimization Trials</Label>
                    <Input
                      id="max-trials"
                      type="number"
                      value={modelConfig.max_trials}
                      onChange={(e) => setModelConfig(prev => ({
                        ...prev,
                        max_trials: parseInt(e.target.value)
                      }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="timeout-hours">Timeout (Hours)</Label>
                    <Input
                      id="timeout-hours"
                      type="number"
                      value={modelConfig.timeout_hours}
                      onChange={(e) => setModelConfig(prev => ({
                        ...prev,
                        timeout_hours: parseInt(e.target.value)
                      }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="instance-type">Compute Instance</Label>
                    <Select
                      value={modelConfig.instance_type}
                      onValueChange={(value) => setModelConfig(prev => ({
                        ...prev,
                        instance_type: value
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select instance" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="CPU_SMALL">CPU Small (2 cores, 4GB)</SelectItem>
                        <SelectItem value="CPU_MEDIUM">CPU Medium (4 cores, 8GB)</SelectItem>
                        <SelectItem value="CPU_LARGE">CPU Large (8 cores, 16GB)</SelectItem>
                        <SelectItem value="GPU_T4">GPU T4 (4 cores, 16GB, T4 GPU)</SelectItem>
                        <SelectItem value="GPU_V100">GPU V100 (8 cores, 32GB, V100 GPU)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="priority">Priority</Label>
                    <Select
                      value={modelConfig.priority}
                      onValueChange={(value) => setModelConfig(prev => ({
                        ...prev,
                        priority: value
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select priority" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="normal">Normal</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="critical">Critical</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Advanced Options Toggle */}
                <div className="flex items-center space-x-2">
                  <Switch
                    id="advanced-options"
                    checked={showAdvancedOptions}
                    onCheckedChange={setShowAdvancedOptions}
                  />
                  <Label htmlFor="advanced-options">Show Advanced Options</Label>
                </div>

                {/* Advanced Options */}
                {showAdvancedOptions && (
                  <div className="space-y-4 p-4 border rounded-lg bg-muted/20">
                    <h4 className="font-medium">Advanced Training Options</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="flex items-center space-x-2">
                        <Switch
                          id="early-stopping"
                          checked={modelConfig.advanced_options?.early_stopping}
                          onCheckedChange={(checked) => setModelConfig(prev => ({
                            ...prev,
                            advanced_options: {
                              ...prev.advanced_options,
                              early_stopping: checked
                            }
                          }))}
                        />
                        <Label htmlFor="early-stopping">Early Stopping</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Switch
                          id="param-reduction"
                          checked={modelConfig.advanced_options?.parameter_space_reduction}
                          onCheckedChange={(checked) => setModelConfig(prev => ({
                            ...prev,
                            advanced_options: {
                              ...prev.advanced_options,
                              parameter_space_reduction: checked
                            }
                          }))}
                        />
                        <Label htmlFor="param-reduction">Parameter Space Reduction</Label>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="cv-folds">Cross-Validation Folds</Label>
                        <Input
                          id="cv-folds"
                          type="number"
                          min="3"
                          max="10"
                          value={modelConfig.advanced_options?.cross_validation_folds}
                          onChange={(e) => setModelConfig(prev => ({
                            ...prev,
                            advanced_options: {
                              ...prev.advanced_options,
                              cross_validation_folds: parseInt(e.target.value)
                            }
                          }))}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="validation-split">Validation Split</Label>
                        <Input
                          id="validation-split"
                          type="number"
                          step="0.1"
                          min="0.1"
                          max="0.5"
                          value={modelConfig.advanced_options?.validation_split}
                          onChange={(e) => setModelConfig(prev => ({
                            ...prev,
                            advanced_options: {
                              ...prev.advanced_options,
                              validation_split: parseFloat(e.target.value)
                            }
                          }))}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
          <CardFooter className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <AlertCircle className="h-4 w-4" />
              <span>
                {selectedMode === 'strategy' 
                  ? 'Strategy will be generated and ready for backtesting'
                  : 'Training job will be queued and you can monitor progress'
                }
              </span>
            </div>
            <div className="flex space-x-2">
              {onCancel && (
                <Button variant="outline" onClick={onCancel} disabled={isLoading}>
                  Cancel
                </Button>
              )}
              <Button 
                onClick={handleExecute} 
                disabled={isLoading}
                className="flex items-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <span>Execute {selectedMode === 'strategy' ? 'Strategy' : 'Training'}</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </CardFooter>
        </Card>
      )}
    </div>
  )
}