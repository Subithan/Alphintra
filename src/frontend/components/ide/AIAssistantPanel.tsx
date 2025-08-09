'use client'

import React, { useState, useRef, useEffect } from 'react'
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
  Star
} from 'lucide-react'
import { EditorMode } from './EnhancedIDE'

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

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const addMessage = (message: Omit<Message, 'id'>) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString()
    }
    setMessages(prev => [...prev, newMessage])
  }

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

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content)
  }

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-lg">
          <div className="flex items-center space-x-2">
            <Bot className="h-5 w-5" />
            <span>AI Assistant</span>
            <Badge variant="outline" className="text-xs capitalize">
              {mode}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearChat}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </CardTitle>
      </CardHeader>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <TabsList className="mx-4 mb-2">
          <TabsTrigger value="chat" className="flex items-center space-x-1">
            <MessageSquare className="h-3 w-3" />
            <span>Chat</span>
          </TabsTrigger>
          <TabsTrigger value="actions" className="flex items-center space-x-1">
            <Zap className="h-3 w-3" />
            <span>Actions</span>
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center space-x-1">
            <Settings className="h-3 w-3" />
            <span>Settings</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="chat" className="flex-1 flex flex-col mx-4">
          {/* Chat Messages */}
          <ScrollArea ref={scrollAreaRef} className="flex-1 mb-4">
            <div className="space-y-4 pr-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.type === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {message.type === 'assistant' && <Bot className="h-4 w-4 mt-0.5" />}
                      {message.type === 'user' && <User className="h-4 w-4 mt-0.5" />}
                      <div className="flex-1">
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs opacity-70">
                            {formatTimestamp(message.timestamp)}
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={() => copyMessage(message.content)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                        {message.metadata && (
                          <div className="flex items-center space-x-1 mt-1">
                            <Badge variant="outline" className="text-xs">
                              {message.metadata.operation}
                            </Badge>
                            {message.metadata.tokensUsed && (
                              <Badge variant="outline" className="text-xs">
                                {message.metadata.tokensUsed} tokens
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
                  <div className="bg-muted text-muted-foreground rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <Bot className="h-4 w-4" />
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Chat Input */}
          <div className="space-y-2">
            <div className="flex space-x-2">
              <Textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={
                  mode === 'ai-first' 
                    ? 'Describe what you want to build in natural language...'
                    : 'Ask me anything about your code...'
                }
                className="flex-1 min-h-[60px] resize-none"
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
                className="h-[60px]"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            
            {error && (
              <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">
                {error}
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="actions" className="flex-1 mx-4">
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium mb-2">Quick Actions</h3>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickAction('explain')}
                  disabled={!currentFile || isGenerating}
                  className="flex items-center space-x-1"
                >
                  <Lightbulb className="h-3 w-3" />
                  <span>Explain</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickAction('optimize')}
                  disabled={!currentFile || isGenerating}
                  className="flex items-center space-x-1"
                >
                  <Zap className="h-3 w-3" />
                  <span>Optimize</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickAction('debug')}
                  disabled={!currentFile || isGenerating}
                  className="flex items-center space-x-1"
                >
                  <Bug className="h-3 w-3" />
                  <span>Debug</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickAction('test')}
                  disabled={!currentFile || isGenerating}
                  className="flex items-center space-x-1"
                >
                  <TestTube className="h-3 w-3" />
                  <span>Test</span>
                </Button>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-2">Code Templates</h3>
              <div className="space-y-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs"
                  onClick={() => onGenerate('Create a basic trading strategy class with buy/sell signals')}
                >
                  Trading Strategy Template
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs"
                  onClick={() => onGenerate('Create a technical indicator calculator with SMA, EMA, RSI')}
                >
                  Technical Indicators
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs"
                  onClick={() => onGenerate('Create a backtesting framework with performance metrics')}
                >
                  Backtesting Framework
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs"
                  onClick={() => onGenerate('Create a risk management system with position sizing')}
                >
                  Risk Management
                </Button>
              </div>
            </div>

            {currentFile && (
              <div>
                <h3 className="text-sm font-medium mb-2">File Context</h3>
                <div className="bg-muted p-2 rounded text-xs">
                  <div className="flex items-center justify-between">
                    <span>{currentFile.name}</span>
                    <Badge variant="outline" className="text-xs">
                      {currentFile.language}
                    </Badge>
                  </div>
                  <div className="text-muted-foreground mt-1">
                    {currentFile.content.split('\n').length} lines
                  </div>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="settings" className="flex-1 mx-4">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">AI Provider</label>
              <Select value={provider} onValueChange={(value: 'openai' | 'anthropic') => setProvider(value)}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI GPT-4</SelectItem>
                  <SelectItem value="anthropic">Anthropic Claude</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium">Complexity Level</label>
              <Select value={complexity} onValueChange={(value: typeof complexity) => setComplexity(value)}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner</SelectItem>
                  <SelectItem value="intermediate">Intermediate</SelectItem>
                  <SelectItem value="advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium">Context Mode</label>
              <Select value={contextMode} onValueChange={(value: typeof contextMode) => setContextMode(value)}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="full">Full File</SelectItem>
                  <SelectItem value="selection">Selection Only</SelectItem>
                  <SelectItem value="none">No Context</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="pt-4 border-t">
              <h3 className="text-sm font-medium mb-2">Statistics</h3>
              <div className="text-xs text-muted-foreground space-y-1">
                <div>Messages: {messages.length}</div>
                <div>Current session: {formatTimestamp(new Date())}</div>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}