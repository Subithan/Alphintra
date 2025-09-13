'use client'

import React, { useState, useRef, useEffect, useCallback, useMemo, memo, startTransition } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Send,
  Bot,
  User,
  RefreshCw,
  Copy,
  Trash2,
  FileText,
  Settings,
  Code,
  Database,
  BarChart3,
  X
} from 'lucide-react'
import { EditorMode } from './EnhancedIDE'

// Types
interface File {
  id: string
  name: string
  path: string
  content: string
  language: string
  modified: boolean
}

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  isGenerating?: boolean
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

// Memoized constants
const QUICK_ACTIONS = [
  {
    id: 'explain',
    title: 'Explain Code',
    description: 'Understand the current code',
    icon: <FileText className="h-4 w-4 text-blue-500" />,
    action: 'explain'
  },
  {
    id: 'optimize',
    title: 'Optimize',
    description: 'Improve performance',
    icon: <BarChart3 className="h-4 w-4 text-green-500" />,
    action: 'optimize'
  },
  {
    id: 'debug',
    title: 'Debug',
    description: 'Find and fix issues',
    icon: <Code className="h-4 w-4 text-red-500" />,
    action: 'debug'
  }
] as const

const TEMPLATES = [
  {
    title: 'Trading Strategy',
    prompt: 'Create a basic trading strategy with buy/sell signals'
  },
  {
    title: 'Technical Indicators',
    prompt: 'Create technical indicators like SMA, EMA, RSI'
  },
  {
    title: 'Risk Management',
    prompt: 'Create a risk management system with position sizing'
  }
] as const

// Memoized components for performance
const ChatMessage = memo(({ message, onCopy }: { message: ChatMessage, onCopy: (content: string) => void }) => (
  <div className={`flex gap-3 p-3 rounded-lg ${
    message.type === 'user'
      ? 'bg-primary/5 border border-primary/20'
      : 'bg-muted/50'
  }`}>
    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
      message.type === 'user'
        ? 'bg-primary text-primary-foreground'
        : 'bg-muted'
    }`}>
      {message.type === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
    </div>
    <div className="flex-1 min-w-0">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium">
          {message.type === 'user' ? 'You' : 'AI Assistant'}
        </span>
        <div className="flex items-center space-x-1">
          <span className="text-xs text-muted-foreground">
            {message.timestamp.toLocaleTimeString()}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onCopy(message.content)}
            className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <Copy className="h-3 w-3" />
          </Button>
        </div>
      </div>
      <div className="text-sm text-foreground whitespace-pre-wrap break-words">
        {message.isGenerating && (
          <div className="flex items-center space-x-2 text-muted-foreground">
            <RefreshCw className="h-3 w-3 animate-spin" />
            <span>Generating response...</span>
          </div>
        )}
        {!message.isGenerating && message.content}
      </div>
    </div>
  </div>
))

ChatMessage.displayName = 'ChatMessage'

const QuickAction = memo(({ action, onAction, disabled }: {
  action: typeof QUICK_ACTIONS[0],
  onAction: (actionType: string) => void,
  disabled: boolean
}) => (
  <Button
    variant="outline"
    className="h-auto p-3 justify-start"
    onClick={() => onAction(action.action)}
    disabled={disabled}
  >
    <div className="flex items-center space-x-3">
      <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center">
        {action.icon}
      </div>
      <div className="text-left">
        <p className="text-sm font-medium">{action.title}</p>
        <p className="text-xs text-muted-foreground">{action.description}</p>
      </div>
    </div>
  </Button>
))

QuickAction.displayName = 'QuickAction'

export const OptimizedAIAssistantPanel = memo(({
  mode,
  currentFile,
  onGenerate,
  onExplain,
  onOptimize,
  onDebug,
  isGenerating,
  error
}: AIAssistantPanelProps) => {
  const [activeTab, setActiveTab] = useState('chat')
  const [prompt, setPrompt] = useState('')
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])
  const [provider, setProvider] = useState<'openai' | 'anthropic'>('openai')
  const [complexity, setComplexity] = useState<'beginner' | 'intermediate' | 'advanced'>('intermediate')

  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const promptRef = useRef<HTMLTextAreaElement>(null)

  // Optimized chat history management with size limit
  const addMessage = useCallback((content: string, type: 'user' | 'assistant') => {
    const newMessage: ChatMessage = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      content,
      timestamp: new Date(),
      isGenerating: type === 'assistant' && isGenerating
    }

    startTransition(() => {
      setChatHistory(prev => {
        const updated = [...prev, newMessage]
        // Keep only last 50 messages for performance
        return updated.length > 50 ? updated.slice(-50) : updated
      })
    })
  }, [isGenerating])

  // Optimized action handlers
  const handleQuickAction = useCallback(async (actionType: string) => {
    if (isGenerating) return

    try {
      switch (actionType) {
        case 'explain':
          await onExplain()
          addMessage('Explain the current code', 'user')
          addMessage('Analyzing your code...', 'assistant')
          break
        case 'optimize':
          await onOptimize()
          addMessage('Optimize this code', 'user')
          addMessage('Optimizing your code...', 'assistant')
          break
        case 'debug':
          await onDebug()
          addMessage('Debug this code', 'user')
          addMessage('Debugging your code...', 'assistant')
          break
      }
    } catch (error) {
      console.error('Action failed:', error)
    }
  }, [isGenerating, onExplain, onOptimize, onDebug, addMessage])

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim() || isGenerating) return

    const userPrompt = prompt.trim()
    setPrompt('')

    addMessage(userPrompt, 'user')
    addMessage('', 'assistant')

    try {
      await onGenerate(userPrompt)
    } catch (error) {
      console.error('Generation failed:', error)
    }
  }, [prompt, isGenerating, onGenerate, addMessage])

  const handleTemplate = useCallback((template: typeof TEMPLATES[0]) => {
    setPrompt(template.prompt)
    promptRef.current?.focus()
  }, [])

  const copyToClipboard = useCallback((content: string) => {
    navigator.clipboard.writeText(content).catch(console.error)
  }, [])

  const clearChat = useCallback(() => {
    startTransition(() => {
      setChatHistory([])
    })
  }, [])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [chatHistory])

  // Memoized file info to prevent recalculation
  const fileInfo = useMemo(() => {
    if (!currentFile) return null

    return {
      lines: currentFile.content.split('\n').length,
      characters: currentFile.content.length,
      size: (currentFile.content.length / 1024).toFixed(1)
    }
  }, [currentFile?.content])

  return (
    <div className="h-full flex flex-col bg-card border-r border-border">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bot className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">AI Assistant</h2>
          </div>
          <Badge variant="outline" className="text-xs">
            {mode.replace('-', ' ')}
          </Badge>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mx-4 mt-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <TabsList className="grid w-full grid-cols-3 mx-4 mt-2">
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="actions">Actions</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Chat Tab */}
        <TabsContent value="chat" className="flex-1 flex flex-col p-4 space-y-4">
          {/* Chat History */}
          <ScrollArea ref={scrollAreaRef} className="flex-1">
            <div className="space-y-3">
              {chatHistory.length === 0 ? (
                <div className="text-center py-8">
                  <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-sm text-muted-foreground">
                    Start a conversation with your AI assistant
                  </p>
                </div>
              ) : (
                chatHistory.map((message) => (
                  <div key={message.id} className="group">
                    <ChatMessage message={message} onCopy={copyToClipboard} />
                  </div>
                ))
              )}
            </div>
          </ScrollArea>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <Textarea
              ref={promptRef}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ask me anything about your code..."
              className="min-h-[80px] resize-none"
              disabled={isGenerating}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault()
                  handleSubmit(e)
                }
              }}
            />
            <div className="flex justify-between items-center">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={clearChat}
                disabled={chatHistory.length === 0}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear
              </Button>
              <Button type="submit" disabled={!prompt.trim() || isGenerating}>
                {isGenerating ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Send className="h-4 w-4 mr-2" />
                )}
                Send
              </Button>
            </div>
          </form>
        </TabsContent>

        {/* Actions Tab */}
        <TabsContent value="actions" className="flex-1 p-4 space-y-4">
          <ScrollArea className="h-full">
            <div className="space-y-6">
              {/* Quick Actions */}
              <div>
                <h3 className="text-sm font-semibold mb-3">Quick Actions</h3>
                <div className="space-y-2">
                  {QUICK_ACTIONS.map((action) => (
                    <QuickAction
                      key={action.id}
                      action={action}
                      onAction={handleQuickAction}
                      disabled={isGenerating || !currentFile}
                    />
                  ))}
                </div>
              </div>

              {/* Templates */}
              <div>
                <h3 className="text-sm font-semibold mb-3">Code Templates</h3>
                <div className="space-y-2">
                  {TEMPLATES.map((template, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      className="w-full justify-start h-auto p-3"
                      onClick={() => handleTemplate(template)}
                    >
                      <div className="text-left">
                        <p className="text-sm font-medium">{template.title}</p>
                        <p className="text-xs text-muted-foreground">{template.prompt}</p>
                      </div>
                    </Button>
                  ))}
                </div>
              </div>

              {/* File Context */}
              {currentFile && fileInfo && (
                <div>
                  <h3 className="text-sm font-semibold mb-3 flex items-center">
                    <FileText className="h-4 w-4 mr-2" />
                    Current File
                  </h3>
                  <div className="bg-muted/50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">{currentFile.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {currentFile.language.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                      <div>Lines: <span className="text-foreground">{fileInfo.lines}</span></div>
                      <div>Size: <span className="text-foreground">{fileInfo.size} KB</span></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="flex-1 p-4">
          <ScrollArea className="h-full">
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-semibold mb-3">AI Configuration</h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium block mb-2">Provider</label>
                    <Select value={provider} onValueChange={(value: typeof provider) => setProvider(value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="openai">OpenAI GPT-4</SelectItem>
                        <SelectItem value="anthropic">Anthropic Claude</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium block mb-2">Complexity</label>
                    <Select value={complexity} onValueChange={(value: typeof complexity) => setComplexity(value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="beginner">Beginner</SelectItem>
                        <SelectItem value="intermediate">Intermediate</SelectItem>
                        <SelectItem value="advanced">Advanced</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  )
})

OptimizedAIAssistantPanel.displayName = 'OptimizedAIAssistantPanel'