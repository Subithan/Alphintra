'use client'

import React, { useState, useRef, useEffect, useCallback, memo, startTransition } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import {
  Terminal,
  X,
  Play,
  Square,
  RotateCcw,
  Copy,
  Trash2,
  AlertCircle,
  CheckCircle,
  Info,
  Download
} from 'lucide-react'

// Optimized types
interface TerminalOutput {
  id: string
  timestamp: Date
  type: 'input' | 'output' | 'error' | 'info'
  content: string
}

interface TerminalPanelProps {
  onClose: () => void
}

// Constants for performance
const MAX_OUTPUT_LINES = 1000 // Limit output history for performance
const BUFFER_SCROLL_THRESHOLD = 100 // Lines before auto-scroll stops

// Memoized output line component
const OutputLine = memo(({ output }: { output: TerminalOutput }) => {
  const getIcon = () => {
    switch (output.type) {
      case 'error':
        return <AlertCircle className="h-3 w-3 text-red-500 flex-shrink-0" />
      case 'info':
        return <Info className="h-3 w-3 text-blue-500 flex-shrink-0" />
      case 'input':
        return <span className="text-green-500 flex-shrink-0">$</span>
      default:
        return null
    }
  }

  const getTextColor = () => {
    switch (output.type) {
      case 'error':
        return 'text-red-400'
      case 'info':
        return 'text-blue-400'
      case 'input':
        return 'text-green-400'
      default:
        return 'text-foreground'
    }
  }

  return (
    <div className="flex items-start space-x-2 font-mono text-sm py-1 group">
      <span className="text-xs text-muted-foreground w-16 flex-shrink-0">
        {output.timestamp.toLocaleTimeString()}
      </span>
      {getIcon()}
      <span className={`flex-1 whitespace-pre-wrap break-words ${getTextColor()}`}>
        {output.content}
      </span>
      <Button
        variant="ghost"
        size="sm"
        className="h-4 w-4 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={() => navigator.clipboard.writeText(output.content)}
      >
        <Copy className="h-3 w-3" />
      </Button>
    </div>
  )
})

OutputLine.displayName = 'OutputLine'

// Virtualized output list for performance
const VirtualizedOutput = memo(({
  outputs,
  autoScroll
}: {
  outputs: TerminalOutput[]
  autoScroll: boolean
}) => {
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new output is added
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [outputs, autoScroll])

  return (
    <ScrollArea ref={scrollRef} className="h-full">
      <div className="p-4 space-y-1">
        {outputs.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-center space-y-2">
              <Terminal className="h-8 w-8 mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Terminal output will appear here</p>
            </div>
          </div>
        ) : (
          outputs.map((output) => (
            <OutputLine key={output.id} output={output} />
          ))
        )}
      </div>
    </ScrollArea>
  )
})

VirtualizedOutput.displayName = 'VirtualizedOutput'

// Quick action buttons
const QuickActions = memo(({
  onClear,
  onDownload,
  outputCount
}: {
  onClear: () => void
  onDownload: () => void
  outputCount: number
}) => (
  <div className="flex items-center space-x-2">
    <Button
      variant="outline"
      size="sm"
      onClick={onClear}
      disabled={outputCount === 0}
    >
      <Trash2 className="h-4 w-4 mr-2" />
      Clear
    </Button>
    <Button
      variant="outline"
      size="sm"
      onClick={onDownload}
      disabled={outputCount === 0}
    >
      <Download className="h-4 w-4 mr-2" />
      Export
    </Button>
  </div>
))

QuickActions.displayName = 'QuickActions'

export const OptimizedTerminalPanel = memo(({ onClose }: TerminalPanelProps) => {
  const [activeTab, setActiveTab] = useState('terminal')
  const [terminalOutput, setTerminalOutput] = useState<TerminalOutput[]>([])
  const [commandInput, setCommandInput] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)

  const commandHistoryRef = useRef<string[]>([])
  const historyIndexRef = useRef(-1)

  // Optimized output management with size limits
  const addOutput = useCallback((content: string, type: TerminalOutput['type']) => {
    const newOutput: TerminalOutput = {
      id: `output-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      type,
      content
    }

    startTransition(() => {
      setTerminalOutput(prev => {
        const updated = [...prev, newOutput]
        // Keep only last MAX_OUTPUT_LINES for performance
        return updated.length > MAX_OUTPUT_LINES
          ? updated.slice(-MAX_OUTPUT_LINES)
          : updated
      })
    })
  }, [])

  // Simulate command execution
  const executeCommand = useCallback(async (command: string) => {
    if (!command.trim() || isRunning) return

    setIsRunning(true)
    addOutput(command, 'input')

    // Add to command history
    commandHistoryRef.current.push(command)
    if (commandHistoryRef.current.length > 50) {
      commandHistoryRef.current = commandHistoryRef.current.slice(-50)
    }
    historyIndexRef.current = -1

    // Simulate command processing
    try {
      await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000))

      // Simulate different command responses
      if (command.startsWith('python')) {
        addOutput('Python script executed successfully', 'info')
        addOutput('✓ Process completed with exit code 0', 'output')
      } else if (command.includes('error')) {
        addOutput('Error: Command failed', 'error')
        addOutput('✗ Process failed with exit code 1', 'error')
      } else if (command.includes('test')) {
        addOutput('Running tests...', 'info')
        addOutput('✓ All tests passed (3/3)', 'output')
      } else {
        addOutput(`Command '${command}' executed`, 'output')
      }
    } catch (error) {
      addOutput(`Error executing command: ${error}`, 'error')
    } finally {
      setIsRunning(false)
    }
  }, [isRunning, addOutput])

  // Handle command submission
  const handleCommandSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    if (commandInput.trim()) {
      executeCommand(commandInput)
      setCommandInput('')
    }
  }, [commandInput, executeCommand])

  // Handle command history navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      const history = commandHistoryRef.current
      if (history.length > 0) {
        const newIndex = Math.min(historyIndexRef.current + 1, history.length - 1)
        historyIndexRef.current = newIndex
        setCommandInput(history[history.length - 1 - newIndex])
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndexRef.current > 0) {
        historyIndexRef.current -= 1
        const history = commandHistoryRef.current
        setCommandInput(history[history.length - 1 - historyIndexRef.current])
      } else if (historyIndexRef.current === 0) {
        historyIndexRef.current = -1
        setCommandInput('')
      }
    }
  }, [])

  // Clear terminal output
  const clearOutput = useCallback(() => {
    startTransition(() => {
      setTerminalOutput([])
    })
  }, [])

  // Download terminal output
  const downloadOutput = useCallback(() => {
    const content = terminalOutput
      .map(output => `[${output.timestamp.toISOString()}] ${output.type.toUpperCase()}: ${output.content}`)
      .join('\n')

    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `terminal-output-${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [terminalOutput])

  // Initialize with welcome message
  useEffect(() => {
    addOutput('Welcome to Alphintra Terminal', 'info')
    addOutput('Type commands to execute or run your trading strategies', 'info')
  }, [addOutput])

  return (
    <div className="h-full flex flex-col bg-card border-t border-border">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-border">
        <div className="flex items-center space-x-2">
          <Terminal className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-semibold">Terminal</h3>
          {terminalOutput.length > 0 && (
            <Badge variant="secondary" className="text-xs">
              {terminalOutput.length} lines
            </Badge>
          )}
          {isRunning && (
            <Badge variant="default" className="text-xs">
              Running
            </Badge>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <QuickActions
            onClear={clearOutput}
            onDownload={downloadOutput}
            outputCount={terminalOutput.length}
          />
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <TabsList className="grid w-full grid-cols-2 mx-3 mt-2">
          <TabsTrigger value="terminal">Terminal</TabsTrigger>
          <TabsTrigger value="output">Output Only</TabsTrigger>
        </TabsList>

        <TabsContent value="terminal" className="flex-1 flex flex-col">
          {/* Terminal Output */}
          <div className="flex-1">
            <VirtualizedOutput
              outputs={terminalOutput}
              autoScroll={autoScroll}
            />
          </div>

          {/* Command Input */}
          <div className="border-t border-border p-3">
            <form onSubmit={handleCommandSubmit}>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 font-mono text-sm">$</span>
                <Input
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Enter command..."
                  disabled={isRunning}
                  className="font-mono"
                  autoComplete="off"
                />
                <Button
                  type="submit"
                  size="sm"
                  disabled={!commandInput.trim() || isRunning}
                >
                  {isRunning ? (
                    <Square className="h-4 w-4" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </form>
          </div>
        </TabsContent>

        <TabsContent value="output" className="flex-1">
          <VirtualizedOutput
            outputs={terminalOutput.filter(o => o.type === 'output' || o.type === 'error')}
            autoScroll={autoScroll}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
})

OptimizedTerminalPanel.displayName = 'OptimizedTerminalPanel'