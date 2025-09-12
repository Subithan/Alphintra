'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Terminal, 
  X, 
  Play, 
  Square, 
  RotateCcw, 
  Download, 
  Upload,
  FileText,
  AlertCircle,
  CheckCircle,
  Info,
  TestTube,
  Settings,
  Search,
  Filter,
  Copy
} from 'lucide-react'

interface TerminalOutput {
  id: string
  timestamp: Date
  type: 'input' | 'output' | 'error' | 'info'
  content: string
}

interface TestResult {
  id: string
  name: string
  status: 'passed' | 'failed' | 'skipped'
  duration: number
  error?: string
}

interface TerminalPanelProps {
  onClose: () => void
}

export function TerminalPanel({ onClose }: TerminalPanelProps) {
  const [activeTab, setActiveTab] = useState('terminal')
  const [terminalOutput, setTerminalOutput] = useState<TerminalOutput[]>([
    {
      id: '1',
      timestamp: new Date(),
      type: 'info',
      content: 'Terminal initialized. Ready for commands.'
    }
  ])
  const [currentCommand, setCurrentCommand] = useState('')
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [isRunning, setIsRunning] = useState(false)
  const [testResults, setTestResults] = useState<TestResult[]>([])
  const [logs, setLogs] = useState<TerminalOutput[]>([])
  
  const terminalRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll terminal to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [terminalOutput])

  // Focus input when terminal is opened
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [])

  const addOutput = (type: TerminalOutput['type'], content: string) => {
    const newOutput: TerminalOutput = {
      id: Date.now().toString(),
      timestamp: new Date(),
      type,
      content
    }
    setTerminalOutput(prev => [...prev, newOutput])
  }

  const executeCommand = async (command: string) => {
    if (!command.trim()) return

    // Add command to history
    setCommandHistory(prev => [...prev, command])
    setHistoryIndex(-1)

    // Add command to output
    addOutput('input', `$ ${command}`)

    setIsRunning(true)

    try {
      // Simulate command execution
      await simulateCommand(command.trim())
    } catch (error) {
      addOutput('error', `Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsRunning(false)
    }
  }

  const simulateCommand = async (command: string): Promise<void> => {
    const parts = command.split(' ')
    const baseCommand = parts[0]

    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 500))

    switch (baseCommand) {
      case 'python':
      case 'python3':
        if (parts.length > 1) {
          const fileName = parts[1]
          addOutput('output', `Running ${fileName}...`)
          await new Promise(resolve => setTimeout(resolve, 1000))
          addOutput('output', 'Strategy backtest completed successfully')
          addOutput('output', 'Total return: +15.7%')
          addOutput('output', 'Sharpe ratio: 1.43')
          addOutput('output', 'Max drawdown: -8.2%')
        } else {
          addOutput('output', 'Python 3.9.0 (default, Oct  9 2020, 15:07:54)')
          addOutput('output', 'Type "help", "copyright", "credits" or "license" for more information.')
          addOutput('output', '>>> ')
        }
        break

      case 'pip':
        if (parts[1] === 'install' && parts.length > 2) {
          const packageName = parts[2]
          addOutput('output', `Collecting ${packageName}...`)
          await new Promise(resolve => setTimeout(resolve, 800))
          addOutput('output', `Successfully installed ${packageName}`)
        } else if (parts[1] === 'list') {
          addOutput('output', 'Package           Version')
          addOutput('output', '----------------- -------')
          addOutput('output', 'numpy             1.24.3')
          addOutput('output', 'pandas            2.0.3')
          addOutput('output', 'scikit-learn      1.3.0')
          addOutput('output', 'fastapi           0.104.1')
        }
        break

      case 'pytest':
        addOutput('output', 'Running tests...')
        await new Promise(resolve => setTimeout(resolve, 1500))
        addOutput('output', '======================== test session starts ========================')
        addOutput('output', 'collected 12 items')
        addOutput('output', '')
        addOutput('output', 'test_strategy.py::test_buy_signal PASSED                  [ 8%]')
        addOutput('output', 'test_strategy.py::test_sell_signal PASSED                 [16%]')
        addOutput('output', 'test_strategy.py::test_risk_management PASSED             [25%]')
        addOutput('output', 'test_indicators.py::test_sma_calculation PASSED           [33%]')
        addOutput('output', 'test_indicators.py::test_rsi_calculation PASSED           [41%]')
        addOutput('output', 'test_backtest.py::test_portfolio_value PASSED             [50%]')
        addOutput('output', 'test_backtest.py::test_trade_execution PASSED             [58%]')
        addOutput('output', 'test_data.py::test_data_validation PASSED                 [66%]')
        addOutput('output', 'test_data.py::test_missing_data_handling PASSED           [75%]')
        addOutput('output', 'test_utils.py::test_date_parsing PASSED                   [83%]')
        addOutput('output', 'test_utils.py::test_logging PASSED                        [91%]')
        addOutput('output', 'test_integration.py::test_full_strategy PASSED            [100%]')
        addOutput('output', '')
        addOutput('output', '======================== 12 passed in 2.45s ========================')
        
        // Update test results
        setTestResults([
          { id: '1', name: 'test_buy_signal', status: 'passed', duration: 0.12 },
          { id: '2', name: 'test_sell_signal', status: 'passed', duration: 0.08 },
          { id: '3', name: 'test_risk_management', status: 'passed', duration: 0.15 },
          { id: '4', name: 'test_sma_calculation', status: 'passed', duration: 0.05 },
          { id: '5', name: 'test_rsi_calculation', status: 'passed', duration: 0.07 },
          { id: '6', name: 'test_portfolio_value', status: 'passed', duration: 0.23 },
          { id: '7', name: 'test_trade_execution', status: 'passed', duration: 0.18 },
          { id: '8', name: 'test_data_validation', status: 'passed', duration: 0.11 },
          { id: '9', name: 'test_missing_data_handling', status: 'passed', duration: 0.16 },
          { id: '10', name: 'test_date_parsing', status: 'passed', duration: 0.03 },
          { id: '11', name: 'test_logging', status: 'passed', duration: 0.04 },
          { id: '12', name: 'test_full_strategy', status: 'passed', duration: 0.89 }
        ])
        break

      case 'ls':
      case 'dir':
        addOutput('output', 'main.py')
        addOutput('output', 'strategy.py')
        addOutput('output', 'indicators.py')
        addOutput('output', 'backtest.py')
        addOutput('output', 'requirements.txt')
        addOutput('output', 'README.md')
        break

      case 'cat':
      case 'type':
        if (parts.length > 1) {
          const fileName = parts[1]
          addOutput('output', `Contents of ${fileName}:`)
          addOutput('output', '# Trading Strategy Implementation')
          addOutput('output', 'import pandas as pd')
          addOutput('output', 'import numpy as np')
          addOutput('output', '')
          addOutput('output', 'class TradingStrategy:')
          addOutput('output', '    def __init__(self):')
          addOutput('output', '        self.name = "AI Generated Strategy"')
        }
        break

      case 'git':
        if (parts[1] === 'status') {
          addOutput('output', 'On branch main')
          addOutput('output', 'Changes not staged for commit:')
          addOutput('output', '  (use "git add <file>..." to update what will be committed)')
          addOutput('output', '  (use "git restore <file>..." to discard changes)')
          addOutput('output', '        modified:   main.py')
          addOutput('output', '        modified:   strategy.py')
        } else if (parts[1] === 'log') {
          addOutput('output', 'commit a1b2c3d (HEAD -> main)')
          addOutput('output', 'Author: AI Assistant <ai@alphintra.com>')
          addOutput('output', 'Date:   ' + new Date().toDateString())
          addOutput('output', '')
          addOutput('output', '    Optimize trading strategy with AI suggestions')
        }
        break

      case 'clear':
      case 'cls':
        setTerminalOutput([])
        addOutput('info', 'Terminal cleared.')
        break

      case 'help':
        addOutput('output', 'Available commands:')
        addOutput('output', '  python <file>  - Run Python script')
        addOutput('output', '  pip install <package> - Install Python package')
        addOutput('output', '  pytest - Run test suite')
        addOutput('output', '  ls/dir - List files')
        addOutput('output', '  cat/type <file> - Show file contents')
        addOutput('output', '  git <command> - Git operations')
        addOutput('output', '  clear/cls - Clear terminal')
        addOutput('output', '  exit - Close terminal')
        break

      case 'exit':
        addOutput('info', 'Closing terminal...')
        setTimeout(onClose, 500)
        break

      default:
        addOutput('error', `Command not found: ${baseCommand}`)
        addOutput('output', 'Type "help" for available commands.')
        break
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      executeCommand(currentCommand)
      setCurrentCommand('')
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (historyIndex < commandHistory.length - 1) {
        const newIndex = historyIndex + 1
        setHistoryIndex(newIndex)
        setCurrentCommand(commandHistory[commandHistory.length - 1 - newIndex])
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setCurrentCommand(commandHistory[commandHistory.length - 1 - newIndex])
      } else if (historyIndex === 0) {
        setHistoryIndex(-1)
        setCurrentCommand('')
      }
    }
  }

  const clearTerminal = () => {
    setTerminalOutput([])
    addOutput('info', 'Terminal cleared.')
  }

  const getOutputColor = (type: TerminalOutput['type']) => {
    switch (type) {
      case 'input':
        return 'text-blue-500 font-medium'
      case 'output':
        return 'text-foreground'
      case 'error':
        return 'text-destructive font-medium'
      case 'info':
        return 'text-orange-500 font-medium'
      default:
        return 'text-foreground'
    }
  }

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  return (
    <div className="h-full flex flex-col bg-card border-t border-border">
      {/* Enhanced Header */}
      <div className="flex items-center justify-between p-3 border-b border-border bg-background">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 rounded bg-primary/10 flex items-center justify-center">
              <Terminal className="h-3 w-3 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground">Terminal</h3>
          </div>
          
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="h-8 bg-muted">
              <TabsTrigger 
                value="terminal" 
                className="text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              >
                <Terminal className="h-3 w-3 mr-1" />
                <span className="hidden sm:inline">Terminal</span>
              </TabsTrigger>
              <TabsTrigger 
                value="tests" 
                className="text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              >
                <CheckCircle className="h-3 w-3 mr-1" />
                <span className="hidden sm:inline">Tests</span>
                {testResults.length > 0 && (
                  <Badge variant="outline" className="ml-1 h-4 text-xs px-1">
                    {testResults.length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger 
                value="logs" 
                className="text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              >
                <FileText className="h-3 w-3 mr-1" />
                <span className="hidden sm:inline">Logs</span>
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
        
        <div className="flex items-center space-x-1">
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-7 w-7 p-0 ide-button-ghost" 
            onClick={clearTerminal}
            title="Clear Terminal"
          >
            <RotateCcw className="h-3 w-3" />
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-7 w-7 p-0 ide-button-ghost" 
            onClick={() => setIsRunning(!isRunning)}
            title={isRunning ? "Stop" : "Start"}
          >
            {isRunning ? <Square className="h-3 w-3" /> : <Play className="h-3 w-3" />}
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-7 w-7 p-0 ide-button-ghost" 
            onClick={onClose}
            title="Close Terminal"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1">
        <TabsContent value="terminal" className="h-full m-0 p-0">
          <div className="h-full flex flex-col">
            {/* Enhanced Terminal Output */}
            <ScrollArea ref={terminalRef} className="flex-1 p-4 bg-background">
              <div className="font-mono text-sm space-y-1">
                {terminalOutput.map((output) => (
                  <div key={output.id} className="flex hover:bg-muted/50 rounded px-2 py-1 -mx-2 group">
                    <span className="text-muted-foreground mr-3 text-xs font-medium min-w-[60px] flex-shrink-0">
                      {formatTimestamp(output.timestamp)}
                    </span>
                    <span className={`${getOutputColor(output.type)} flex-1`}>
                      {output.content}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 opacity-0 group-hover:opacity-100 transition-opacity ml-2"
                      onClick={() => navigator.clipboard.writeText(output.content)}
                      title="Copy line"
                    >
                      <Copy className="h-2 w-2" />
                    </Button>
                  </div>
                ))}
                {isRunning && (
                  <div className="flex items-center space-x-3 px-2 py-1 text-orange-500">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-sm">Executing command...</span>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Enhanced Command Input */}
            <div className="border-t border-border p-4 bg-muted">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 text-primary">
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                  <span className="font-mono font-bold">$</span>
                </div>
                <Input
                  ref={inputRef}
                  value={currentCommand}
                  onChange={(e) => setCurrentCommand(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a command and press Enter..."
                  disabled={isRunning}
                  className="ide-input font-mono bg-background border-border focus-visible:ring-ring"
                />
                <div className="flex items-center space-x-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 ide-button-ghost"
                    onClick={() => setCurrentCommand('')}
                    disabled={!currentCommand || isRunning}
                    title="Clear command"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    className="ide-button-primary h-8"
                    onClick={() => executeCommand(currentCommand)}
                    disabled={!currentCommand.trim() || isRunning}
                  >
                    <Play className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              
              {/* Command History Indicator */}
              {commandHistory.length > 0 && (
                <div className="mt-2 text-xs text-muted-foreground">
                  Use ↑/↓ arrows to navigate command history ({commandHistory.length} commands)
                </div>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="tests" className="h-full m-0 p-0">
          <div className="h-full flex flex-col">
            {testResults.length > 0 && (
              <div className="p-4 border-b border-border bg-background">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {testResults.filter(t => t.status === 'passed').length}
                    </div>
                    <div className="text-xs text-muted-foreground">Passed</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-destructive">
                      {testResults.filter(t => t.status === 'failed').length}
                    </div>
                    <div className="text-xs text-muted-foreground">Failed</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-orange-500">
                      {testResults.filter(t => t.status === 'skipped').length}
                    </div>
                    <div className="text-xs text-muted-foreground">Skipped</div>
                  </div>
                </div>
              </div>
            )}
            
            <ScrollArea className="flex-1 p-4">
              {testResults.length > 0 ? (
                <div className="space-y-2">
                  {testResults.map((test) => (
                    <div
                      key={test.id}
                      className={`p-3 border rounded-lg transition-colors hover:bg-ide-surface/50 ${
                        test.status === 'passed' ? 'border-ide-success/20 bg-ide-success/5' :
                        test.status === 'failed' ? 'border-ide-error/20 bg-ide-error/5' :
                        'border-ide-warning/20 bg-ide-warning/5'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                            test.status === 'passed' ? 'bg-green-500/10' :
                            test.status === 'failed' ? 'bg-destructive/10' :
                            'bg-orange-500/10'
                          }`}>
                            {test.status === 'passed' && (
                              <CheckCircle className="h-3 w-3 text-green-600" />
                            )}
                            {test.status === 'failed' && (
                              <AlertCircle className="h-3 w-3 text-destructive" />
                            )}
                            {test.status === 'skipped' && (
                              <Info className="h-3 w-3 text-orange-500" />
                            )}
                          </div>
                          <div>
                            <span className="font-mono text-sm text-foreground font-medium">{test.name}</span>
                            {test.error && (
                              <p className="text-xs text-destructive mt-1">{test.error}</p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-muted-foreground font-mono">
                            {test.duration.toFixed(2)}s
                          </span>
                          <Badge 
                            variant="outline" 
                            className={`text-xs h-5 ${
                              test.status === 'passed' ? 'bg-green-500/10 text-green-600 border-green-500/20' :
                              test.status === 'failed' ? 'bg-destructive/10 text-destructive border-destructive/20' :
                              'bg-orange-500/10 text-orange-500 border-orange-500/20'
                            }`}
                          >
                            {test.status.toUpperCase()}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <div className="text-center space-y-4">
                    <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                      <TestTube className="h-8 w-8 text-primary" />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-foreground mb-2">No Test Results</h3>
                      <p className="text-sm text-muted-foreground max-w-xs">
                        Run your test suite to see detailed results and coverage information here.
                      </p>
                    </div>
                    <div className="flex flex-col space-y-2">
                      <Button size="sm" className="ide-button-primary">
                        <TestTube className="h-4 w-4 mr-2" />
                        Run Tests
                      </Button>
                      <Button size="sm" variant="outline" className="ide-button-secondary">
                        <Settings className="h-4 w-4 mr-2" />
                        Configure Tests
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </ScrollArea>
          </div>
        </TabsContent>

        <TabsContent value="logs" className="h-full m-0 p-0">
          <div className="h-full flex flex-col">
            {/* Log Controls */}
            <div className="p-3 border-b border-border bg-background">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Select defaultValue="all">
                    <SelectTrigger className="w-32 h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Logs</SelectItem>
                      <SelectItem value="error">Errors</SelectItem>
                      <SelectItem value="warning">Warnings</SelectItem>
                      <SelectItem value="info">Info</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="sm" className="h-8 px-2 text-xs ide-button-ghost">
                    <Download className="h-3 w-3 mr-1" />
                    Export
                  </Button>
                </div>
                <div className="flex items-center space-x-1">
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0 ide-button-ghost">
                    <Search className="h-3 w-3" />
                  </Button>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0 ide-button-ghost">
                    <Filter className="h-3 w-3" />
                  </Button>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0 ide-button-ghost">
                    <RotateCcw className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </div>
            
            <ScrollArea className="flex-1 p-4">
              <div className="font-mono text-sm space-y-1">
                {logs.length > 0 ? (
                  logs.map((log) => (
                    <div key={log.id} className="flex hover:bg-muted/50 rounded px-2 py-1 -mx-2 group">
                      <span className="text-muted-foreground mr-3 text-xs font-medium min-w-[60px] flex-shrink-0">
                        {formatTimestamp(log.timestamp)}
                      </span>
                      <div className={`w-2 h-2 rounded-full mr-2 mt-1.5 flex-shrink-0 ${
                        log.type === 'error' ? 'bg-destructive' :
                        log.type === 'info' ? 'bg-blue-500' :
                        'bg-orange-500'
                      }`} />
                      <span className={`${getOutputColor(log.type)} flex-1`}>
                        {log.content}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-4 w-4 p-0 opacity-0 group-hover:opacity-100 transition-opacity ml-2"
                        onClick={() => navigator.clipboard.writeText(log.content)}
                        title="Copy log entry"
                      >
                        <Copy className="h-2 w-2" />
                      </Button>
                    </div>
                  ))
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    <div className="text-center space-y-4">
                      <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                        <FileText className="h-8 w-8 text-primary" />
                      </div>
                      <div>
                        <h3 className="text-lg font-medium text-foreground mb-2">No Logs Available</h3>
                        <p className="text-sm text-muted-foreground max-w-xs">
                          Application logs and system messages will appear here when your code runs.
                        </p>
                      </div>
                      <div className="flex flex-col space-y-2">
                        <Button size="sm" className="ide-button-primary">
                          <Play className="h-4 w-4 mr-2" />
                          Run Application
                        </Button>
                        <Button size="sm" variant="outline" className="ide-button-secondary">
                          <Settings className="h-4 w-4 mr-2" />
                          Log Settings
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </TabsContent>
      </div>
    </div>
  )
}