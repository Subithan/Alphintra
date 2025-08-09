'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
  Info
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
        return 'text-blue-400'
      case 'output':
        return 'text-foreground'
      case 'error':
        return 'text-red-400'
      case 'info':
        return 'text-yellow-400'
      default:
        return 'text-foreground'
    }
  }

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  return (
    <div className="h-full flex flex-col bg-background border-t border-border">
      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b border-border bg-muted/30">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
          <TabsList className="h-8">
            <TabsTrigger value="terminal" className="text-xs">
              <Terminal className="h-3 w-3 mr-1" />
              Terminal
            </TabsTrigger>
            <TabsTrigger value="tests" className="text-xs">
              <CheckCircle className="h-3 w-3 mr-1" />
              Tests ({testResults.length})
            </TabsTrigger>
            <TabsTrigger value="logs" className="text-xs">
              <FileText className="h-3 w-3 mr-1" />
              Logs
            </TabsTrigger>
          </TabsList>
        </Tabs>
        
        <div className="flex items-center space-x-1">
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={clearTerminal}>
            <RotateCcw className="h-3 w-3" />
          </Button>
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={onClose}>
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1">
        <TabsContent value="terminal" className="h-full m-0 p-0">
          <div className="h-full flex flex-col">
            {/* Terminal Output */}
            <ScrollArea ref={terminalRef} className="flex-1 p-3">
              <div className="font-mono text-sm space-y-1">
                {terminalOutput.map((output) => (
                  <div key={output.id} className="flex">
                    <span className="text-muted-foreground mr-2 text-xs">
                      {formatTimestamp(output.timestamp)}
                    </span>
                    <span className={getOutputColor(output.type)}>
                      {output.content}
                    </span>
                  </div>
                ))}
                {isRunning && (
                  <div className="flex items-center space-x-2 text-yellow-400">
                    <div className="animate-spin w-3 h-3 border border-current border-t-transparent rounded-full" />
                    <span>Running...</span>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Command Input */}
            <div className="border-t border-border p-3">
              <div className="flex items-center space-x-2 font-mono text-sm">
                <span className="text-blue-400">$</span>
                <Input
                  ref={inputRef}
                  value={currentCommand}
                  onChange={(e) => setCurrentCommand(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Enter command..."
                  disabled={isRunning}
                  className="font-mono bg-transparent border-none p-0 h-auto focus-visible:ring-0"
                />
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="tests" className="h-full m-0 p-0">
          <ScrollArea className="h-full p-3">
            {testResults.length > 0 ? (
              <div className="space-y-2">
                {testResults.map((test) => (
                  <div
                    key={test.id}
                    className="flex items-center justify-between p-2 border border-border rounded"
                  >
                    <div className="flex items-center space-x-2">
                      {test.status === 'passed' && (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      )}
                      {test.status === 'failed' && (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                      {test.status === 'skipped' && (
                        <Info className="h-4 w-4 text-yellow-500" />
                      )}
                      <span className="font-mono text-sm">{test.name}</span>
                    </div>
                    <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                      <span>{test.duration.toFixed(2)}s</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        test.status === 'passed' ? 'bg-green-100 text-green-800' :
                        test.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {test.status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <div className="text-center">
                  <CheckCircle className="h-8 w-8 mx-auto mb-2" />
                  <p className="text-sm">No test results yet</p>
                  <p className="text-xs">Run `pytest` to see test results here</p>
                </div>
              </div>
            )}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="logs" className="h-full m-0 p-0">
          <ScrollArea className="h-full p-3">
            <div className="font-mono text-sm space-y-1">
              {logs.length > 0 ? (
                logs.map((log) => (
                  <div key={log.id} className="flex">
                    <span className="text-muted-foreground mr-2 text-xs">
                      {formatTimestamp(log.timestamp)}
                    </span>
                    <span className={getOutputColor(log.type)}>
                      {log.content}
                    </span>
                  </div>
                ))
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <div className="text-center">
                    <FileText className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">No logs yet</p>
                    <p className="text-xs">Application logs will appear here</p>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>
      </div>
    </div>
  )
}