'use client'

import React, { useState, useRef, useEffect, useCallback, useMemo, memo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Send, 
  Lightbulb, 
  Bug, 
  TestTube, 
  Zap, 
  MessageSquare, 
  Code, 
  Settings,
  Bot,
  User,
  RefreshCw,
  Copy,
  Trash2,
  Star,
  FileText,
  Database,
  BarChart3,
  Activity,
  Download,
  AlertCircle,
  File,
  X
} from 'lucide-react'
import { EditorMode } from './EnhancedIDE'

// Memoized constants for performance
const TRADING_TEMPLATES = [
  {
    title: 'Trading Strategy',
    description: 'Basic strategy class with buy/sell signals',
    prompt: 'Create a basic trading strategy class with buy/sell signals',
    icon: <Code className="h-4 w-4 text-blue-500" />
  },
  {
    title: 'Technical Indicators',
    description: 'SMA, EMA, RSI calculator functions',
    prompt: 'Create a technical indicator calculator with SMA, EMA, RSI',
    icon: <Database className="h-4 w-4 text-green-500" />
  },
  {
    title: 'Backtesting Framework',
    description: 'Performance metrics and analysis',
    prompt: 'Create a backtesting framework with performance metrics',
    icon: <TestTube className="h-4 w-4 text-purple-500" />
  },
  {
    title: 'Risk Management',
    description: 'Position sizing and risk controls',
    prompt: 'Create a risk management system with position sizing',
    icon: <Settings className="h-4 w-4 text-orange-500" />
  }
]

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  metadata?: {
    operation?: string
    tokensUsed?: number
    provider?: string
    confidence?: number
  }
}

interface CodeSuggestion {
  id: string
  title: string
  description: string
  code: string
  confidence: number
  category: 'generation' | 'optimization' | 'debugging' | 'testing'
}

interface File {
  id: string
  name: string
  content: string
  language: string
}

interface AIAssistantPanelProps {
  mode: EditorMode
  currentFile: File | null
  onGenerate: (prompt: string) => Promise<void>
  onExplain: (selectedText?: string) => Promise<void>
  onOptimize: () => Promise<void>
  onDebug: (errorMessage?: string) => Promise<void>
  isGenerating: boolean
  error: string | null
}

export function AIAssistantPanel({
  mode,
  currentFile,
  onGenerate,
  onExplain,
  onOptimize,
  onDebug,
  isGenerating,
  error
}: AIAssistantPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hello! I\'m your AI coding assistant. I can help you generate code, explain concepts, optimize performance, debug issues, and create tests. What would you like to work on?',
      timestamp: new Date()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [activeTab, setActiveTab] = useState('chat')
  const [suggestions, setSuggestions] = useState<CodeSuggestion[]>([])
  const [complexity, setComplexity] = useState<'beginner' | 'intermediate' | 'advanced'>('intermediate')
  const [provider, setProvider] = useState<'openai' | 'anthropic'>('openai')
  const [contextMode, setContextMode] = useState<'full' | 'selection' | 'none'>('full')
  
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Optimized auto-scroll with debounce
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (scrollAreaRef.current) {
        scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
      }
    }, 50)
    
    return () => clearTimeout(timeoutId)
  }, [messages.length]) // Only depend on length, not entire messages array

  const addMessage = useCallback((message: Omit<Message, 'id'>) => {
    const newMessage: Message = {
      ...message,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    }
    setMessages(prev => {
      // Keep only last 100 messages for performance
      const newMessages = [...prev, newMessage]
      return newMessages.length > 100 ? newMessages.slice(-100) : newMessages
    })
  }, [])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isGenerating) return

    const userMessage = inputMessage.trim()
    setInputMessage('')

    // Add user message
    addMessage({
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    })

    try {
      // Determine the type of request based on content
      const lowerMessage = userMessage.toLowerCase()
      
      if (lowerMessage.includes('generate') || lowerMessage.includes('create') || lowerMessage.includes('write')) {
        // Code generation
        await onGenerate(userMessage)
        addMessage({
          type: 'assistant',
          content: 'I\'ve generated code based on your request. Check the editor for the results!',
          timestamp: new Date(),
          metadata: { operation: 'generate' }
        })
      } else if (lowerMessage.includes('explain') || lowerMessage.includes('what does')) {
        // Code explanation
        await onExplain()
        addMessage({
          type: 'assistant',
          content: 'I\'ve analyzed your code and provided an explanation. Check the results in the explanation tab.',
          timestamp: new Date(),
          metadata: { operation: 'explain' }
        })
      } else if (lowerMessage.includes('optimize') || lowerMessage.includes('improve') || lowerMessage.includes('faster')) {
        // Code optimization
        await onOptimize()
        addMessage({
          type: 'assistant',
          content: 'I\'ve optimized your code for better performance. The updated version is now in your editor.',
          timestamp: new Date(),
          metadata: { operation: 'optimize' }
        })
      } else if (lowerMessage.includes('debug') || lowerMessage.includes('error') || lowerMessage.includes('fix')) {
        // Debugging
        await onDebug(userMessage)
        addMessage({
          type: 'assistant',
          content: 'I\'ve analyzed the issue and provided a fix. Check the editor for the corrected code.',
          timestamp: new Date(),
          metadata: { operation: 'debug' }
        })
      } else {
        // General chat - use generate for now
        await onGenerate(userMessage)
        addMessage({
          type: 'assistant',
          content: 'I\'ve processed your request. Let me know if you need any clarifications or modifications!',
          timestamp: new Date()
        })
      }
    } catch (error) {
      addMessage({
        type: 'assistant',
        content: `I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        timestamp: new Date()
      })
    }
  }

  const handleQuickAction = async (action: string) => {
    switch (action) {
      case 'explain':
        addMessage({
          type: 'user',
          content: 'Please explain this code',
          timestamp: new Date()
        })
        await onExplain()
        break
      case 'optimize':
        addMessage({
          type: 'user',
          content: 'Optimize this code for better performance',
          timestamp: new Date()
        })
        await onOptimize()
        break
      case 'debug':
        addMessage({
          type: 'user',
          content: 'Help me debug this code',
          timestamp: new Date()
        })
        await onDebug()
        break
      case 'test':
        addMessage({
          type: 'user',
          content: 'Generate unit tests for this code',
          timestamp: new Date()
        })
        await onGenerate('Generate comprehensive unit tests for this code')
        break
    }
  }

  const clearChat = () => {
    setMessages([
      {
        id: '1',
        type: 'assistant',
        content: 'Chat cleared! How can I help you with your code?',
        timestamp: new Date()
      }
    ])
  }

  const copyMessage = useCallback((content: string) => {
    navigator.clipboard.writeText(content).catch(console.error)
  }, [])

  const formatTimestamp = useCallback((date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }, [])
  
  const getFileIcon = (fileName: string, language: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase()
    
    switch (extension) {
      case 'py':
        return <Code className="h-4 w-4 file-icon-python" />
      case 'js':
        return <Code className="h-4 w-4 file-icon-javascript" />
      case 'ts':
      case 'tsx':
        return <Code className="h-4 w-4 file-icon-typescript" />
      case 'json':
        return <Database className="h-4 w-4 file-icon-json" />
      case 'md':
      case 'mdx':
        return <FileText className="h-4 w-4 file-icon-markdown" />
      default:
        return <File className="h-4 w-4 file-icon-default" />
    }
  }

  return (
    <div className="h-full flex flex-col bg-card">
      {/* Enhanced Header */}
      <div className="p-4 border-b border-border bg-background">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">AI Assistant</h2>
              <p className="text-xs text-muted-foreground">Powered by {provider.toUpperCase()}</p>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <Badge 
              variant="outline" 
              className={`text-xs h-6 ${
                mode === 'ai-first' ? 'bg-primary/10 text-primary border-primary/20' :
                mode === 'ai-assisted' ? 'bg-green-500/10 text-green-600 border-green-500/20' :
                'bg-muted text-muted-foreground border-border'
              }`}
            >
              {mode.replace('-', ' ').toUpperCase()}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearChat}
              className="h-7 w-7 p-0 ide-button-ghost"
              title="Clear Chat"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <div className="px-4 py-2 border-b border-border">
          <TabsList className="grid w-full grid-cols-3 bg-background">
            <TabsTrigger value="chat" className="flex items-center space-x-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              <MessageSquare className="h-3 w-3" />
              <span className="hidden sm:inline">Chat</span>
            </TabsTrigger>
            <TabsTrigger value="actions" className="flex items-center space-x-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              <Zap className="h-3 w-3" />
              <span className="hidden sm:inline">Actions</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center space-x-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              <Settings className="h-3 w-3" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="chat" className="flex-1 flex flex-col">
          {/* Enhanced Chat Messages */}
          <ScrollArea ref={scrollAreaRef} className="flex-1 px-4">
            <div className="py-4 space-y-4">
              {messages.slice(-50).map((message) => ( // Only render last 50 messages for performance
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} group`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-4 slide-up ${
                      message.type === 'user'
                        ? 'bg-primary text-primary-foreground ml-8'
                        : 'bg-muted text-foreground border border-border mr-8'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      {message.type === 'assistant' && (
                        <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <Bot className="h-3 w-3 text-primary" />
                        </div>
                      )}
                      {message.type === 'user' && (
                        <div className="w-6 h-6 rounded-full bg-background/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <User className="h-3 w-3" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{message.content}</p>
                        <div className="flex items-center justify-between mt-3">
                          <span className={`text-xs ${
                            message.type === 'user' ? 'text-primary-foreground/70' : 'text-muted-foreground'
                          }`}>
                            {formatTimestamp(message.timestamp)}
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className={`h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity ${
                              message.type === 'user' ? 'hover:bg-background/20' : 'hover:bg-accent'
                            }`}
                            onClick={() => copyMessage(message.content)}
                            title="Copy message"
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                        {message.metadata && (
                          <div className="flex flex-wrap items-center gap-2 mt-2">
                            <Badge variant="outline" className="text-xs h-5 bg-primary/10 text-primary border-primary/20">
                              {message.metadata.operation}
                            </Badge>
                            {message.metadata.tokensUsed && (
                              <Badge variant="outline" className="text-xs h-5">
                                {message.metadata.tokensUsed} tokens
                              </Badge>
                            )}
                            {message.metadata.confidence && (
                              <Badge variant="outline" className="text-xs h-5">
                                {Math.round(message.metadata.confidence * 100)}% confidence
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {isGenerating && (
                <div className="flex justify-start">
                  <div className="bg-muted text-foreground border border-border rounded-2xl p-4 mr-8">
                    <div className="flex items-center space-x-3">
                      <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
                        <Bot className="h-3 w-3 text-primary" />
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                        <span className="text-sm text-muted-foreground">AI is thinking...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Enhanced Chat Input */}
          <div className="p-4 border-t border-border bg-background">
            <div className="space-y-3">
              <div className="flex space-x-3">
                <Textarea
                  ref={inputRef}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={
                    mode === 'ai-first' 
                      ? 'Describe what you want to build in natural language...'
                      : mode === 'ai-assisted'
                      ? 'Ask me anything about your code or request assistance...'
                      : 'Type your message here...'
                  }
                  className="ide-input flex-1 min-h-[80px] resize-none text-sm leading-relaxed"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage()
                    }
                  }}
                  disabled={isGenerating}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isGenerating}
                  className={`h-[80px] w-12 ide-button-primary ${
                    !inputMessage.trim() || isGenerating ? 'opacity-50' : 'pulse-glow'
                  }`}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              
              {/* Quick Actions Bar */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2 text-xs ide-button-ghost"
                    onClick={() => handleQuickAction('explain')}
                    disabled={!currentFile || isGenerating}
                  >
                    <Lightbulb className="h-3 w-3 mr-1" />
                    Explain
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2 text-xs ide-button-ghost"
                    onClick={() => handleQuickAction('optimize')}
                    disabled={!currentFile || isGenerating}
                  >
                    <Zap className="h-3 w-3 mr-1" />
                    Optimize
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2 text-xs ide-button-ghost"
                    onClick={() => handleQuickAction('debug')}
                    disabled={!currentFile || isGenerating}
                  >
                    <Bug className="h-3 w-3 mr-1" />
                    Debug
                  </Button>
                </div>
                <div className="text-xs text-muted-foreground">
                  {inputMessage.length}/2000
                </div>
              </div>
              
              {error && (
                <div className="text-sm text-destructive bg-destructive/10 border border-destructive/20 p-3 rounded-lg">
                  <div className="flex items-start space-x-2">
                    <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium">Error</p>
                      <p className="text-xs mt-1">{error}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="actions" className="flex-1 p-4">
          <ScrollArea className="h-full">
            <div className="space-y-6">
              {/* Enhanced Quick Actions */}
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                  <Zap className="h-4 w-4 mr-2 text-primary" />
                  Quick Actions
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickAction('explain')}
                    disabled={!currentFile || isGenerating}
                    className="ide-button-secondary justify-start h-12 flex-col space-y-1 p-2"
                  >
                    <Lightbulb className="h-4 w-4 text-primary" />
                    <span className="text-xs">Explain Code</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickAction('optimize')}
                    disabled={!currentFile || isGenerating}
                    className="ide-button-secondary justify-start h-12 flex-col space-y-1 p-2"
                  >
                    <Zap className="h-4 w-4 text-green-600" />
                    <span className="text-xs">Optimize</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickAction('debug')}
                    disabled={!currentFile || isGenerating}
                    className="ide-button-secondary justify-start h-12 flex-col space-y-1 p-2"
                  >
                    <Bug className="h-4 w-4 text-destructive" />
                    <span className="text-xs">Debug</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickAction('test')}
                    disabled={!currentFile || isGenerating}
                    className="ide-button-secondary justify-start h-12 flex-col space-y-1 p-2"
                  >
                    <TestTube className="h-4 w-4 text-blue-500" />
                    <span className="text-xs">Generate Tests</span>
                  </Button>
                </div>
              </div>

              {/* Enhanced Code Templates */}
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                  <Code className="h-4 w-4 mr-2 text-primary" />
                  Trading Templates
                </h3>
                <div className="space-y-2">
                  <Button
                    variant="ghost"
                    className="w-full justify-start h-auto p-3 ide-button-ghost"
                    onClick={() => onGenerate('Create a basic trading strategy class with buy/sell signals')}
                    disabled={isGenerating}
                  >
                    <div className="flex items-start space-x-3 text-left">
                      <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                        <Code className="h-4 w-4 text-blue-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">Trading Strategy</p>
                        <p className="text-xs text-muted-foreground mt-0.5">Basic strategy class with buy/sell signals</p>
                      </div>
                    </div>
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full justify-start h-auto p-3 ide-button-ghost"
                    onClick={() => onGenerate('Create a technical indicator calculator with SMA, EMA, RSI')}
                    disabled={isGenerating}
                  >
                    <div className="flex items-start space-x-3 text-left">
                      <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                        <Database className="h-4 w-4 text-green-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">Technical Indicators</p>
                        <p className="text-xs text-muted-foreground mt-0.5">SMA, EMA, RSI calculator functions</p>
                      </div>
                    </div>
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full justify-start h-auto p-3 ide-button-ghost"
                    onClick={() => onGenerate('Create a backtesting framework with performance metrics')}
                    disabled={isGenerating}
                  >
                    <div className="flex items-start space-x-3 text-left">
                      <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                        <TestTube className="h-4 w-4 text-purple-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">Backtesting Framework</p>
                        <p className="text-xs text-muted-foreground mt-0.5">Performance metrics and analysis</p>
                      </div>
                    </div>
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full justify-start h-auto p-3 ide-button-ghost"
                    onClick={() => onGenerate('Create a risk management system with position sizing')}
                    disabled={isGenerating}
                  >
                    <div className="flex items-start space-x-3 text-left">
                      <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                        <Settings className="h-4 w-4 text-orange-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">Risk Management</p>
                        <p className="text-xs text-muted-foreground mt-0.5">Position sizing and risk controls</p>
                      </div>
                    </div>
                  </Button>}
                </div>
              </div>

              {/* Enhanced File Context */}
              {currentFile && (
                <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                  <FileText className="h-4 w-4 mr-2 text-primary" />
                  Current File
                </h3>
                <div className="bg-background border border-border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      {getFileIcon(currentFile.name, currentFile.language)}
                      <span className="text-sm font-medium text-foreground">{currentFile.name}</span>
                    </div>
                    <Badge variant="outline" className="text-xs bg-primary/10 text-primary border-primary/20">
                      {currentFile.language.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground">
                    <div>
                      <span className="block">Lines:</span>
                      <span className="text-foreground font-medium">{currentFile.content.split('\n').length}</span>
                    </div>
                    <div>
                      <span className="block">Characters:</span>
                      <span className="text-foreground font-medium">{currentFile.content.length}</span>
                    </div>
                    <div>
                      <span className="block">Size:</span>
                      <span className="text-foreground font-medium">{(currentFile.content.length / 1024).toFixed(1)} KB</span>
                    </div>
                    <div>
                      <span className="block">Modified:</span>
                      <span className={`font-medium ${currentFile.modified ? 'text-orange-500' : 'text-green-600'}`}>
                        {currentFile.modified ? 'Yes' : 'No'}
                      </span>
                    </div>
                  </div>
                </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="settings" className="flex-1 p-4">
          <ScrollArea className="h-full">
            <div className="space-y-6">
              {/* AI Configuration */}
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                  <Bot className="h-4 w-4 mr-2 text-primary" />
                  AI Configuration
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">AI Provider</label>
                    <Select value={provider} onValueChange={(value: 'openai' | 'anthropic') => setProvider(value)}>
                      <SelectTrigger className="ide-input">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-card border-border">
                        <SelectItem value="openai" className="text-foreground hover:bg-accent">
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full" />
                            <span>OpenAI GPT-4</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="anthropic" className="text-foreground hover:bg-accent">
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-blue-500 rounded-full" />
                            <span>Anthropic Claude</span>
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">Complexity Level</label>
                    <Select value={complexity} onValueChange={(value: typeof complexity) => setComplexity(value)}>
                      <SelectTrigger className="ide-input">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-card border-border">
                        <SelectItem value="beginner" className="text-foreground hover:bg-accent">Beginner</SelectItem>
                        <SelectItem value="intermediate" className="text-foreground hover:bg-accent">Intermediate</SelectItem>
                        <SelectItem value="advanced" className="text-foreground hover:bg-accent">Advanced</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">Context Mode</label>
                    <Select value={contextMode} onValueChange={(value: typeof contextMode) => setContextMode(value)}>
                      <SelectTrigger className="ide-input">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-card border-border">
                        <SelectItem value="full" className="text-foreground hover:bg-accent">Full File Context</SelectItem>
                        <SelectItem value="selection" className="text-foreground hover:bg-accent">Selection Only</SelectItem>
                        <SelectItem value="none" className="text-foreground hover:bg-accent">No Context</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* Session Statistics */}
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                  <BarChart3 className="h-4 w-4 mr-2 text-primary" />
                  Session Statistics
                </h3>
                <div className="bg-background border border-border rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">{messages.length}</div>
                      <div className="text-xs text-muted-foreground">Messages</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {messages.reduce((acc, msg) => acc + (msg.metadata?.tokensUsed || 0), 0)}
                      </div>
                      <div className="text-xs text-muted-foreground">Tokens Used</div>
                    </div>
                    <div className="text-center col-span-2">
                      <div className="text-sm text-muted-foreground">
                        Session started: {formatTimestamp(new Date())}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                  <Activity className="h-4 w-4 mr-2 text-primary" />
                  Performance
                </h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-2 bg-background border border-border rounded">
                    <span className="text-sm text-foreground">Average Response Time</span>
                    <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                      1.2s
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-background border border-border rounded">
                    <span className="text-sm text-foreground">Success Rate</span>
                    <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                      98.5%
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-background border border-border rounded">
                    <span className="text-sm text-foreground">Model Quality</span>
                    <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">
                      Excellent
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-2">
                <Button 
                  variant="outline" 
                  className="w-full ide-button-secondary justify-start"
                  onClick={clearChat}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear Chat History
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full ide-button-secondary justify-start"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export Conversation
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full ide-button-secondary justify-start"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reset Settings
                </Button>
              </div>
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  )
}