'use client'

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Code, 
  FileText, 
  Play, 
  Save, 
  Settings, 
  MessageSquare, 
  Lightbulb, 
  Bug, 
  TestTube, 
  Bot, 
  Brain, 
  Zap,
  Terminal,
  FolderTree,
  Search,
  RefreshCw,
  ChevronRight,
  ChevronDown
} from 'lucide-react'
import Editor from '@monaco-editor/react'
import { ProjectExplorer } from './ProjectExplorer'
import type { ProjectFile as ExplorerFile, Project as ExplorerProject } from './ProjectExplorer'
import { AIAssistantPanel } from './AIAssistantPanel'
import { TerminalPanel } from './TerminalPanel'
import { useAICodeStore } from '@/lib/stores/ai-code-store'
import { useAICodeOperationStates } from '@/lib/stores/ai-code-store'
import { useTheme } from 'next-themes'
import { CommandPalette } from './CommandPalette'
import { StatusBar } from './StatusBar'

export type EditorMode = 'traditional' | 'ai-assisted' | 'ai-first'

type IDEFile = ExplorerFile

interface Project extends ExplorerProject {
  settings: {
    aiEnabled: boolean
    suggestions: boolean
    autoComplete: boolean
    errorDetection: boolean
    testGeneration: boolean
  }
}

interface EnhancedIDEProps {
  projectId?: string
  initialMode?: EditorMode
  onSave?: (file: IDEFile) => Promise<void>
  onRun?: (file: IDEFile) => Promise<void>
}

export function EnhancedIDE({ 
  projectId, 
  initialMode = 'ai-assisted', 
  onSave, 
  onRun 
}: EnhancedIDEProps) {
  const [editorMode, setEditorMode] = useState<EditorMode>(initialMode)
  const [currentProject, setCurrentProject] = useState<Project | null>(null)
  const [activeFile, setActiveFile] = useState<IDEFile | null>(null)
  const [openFiles, setOpenFiles] = useState<IDEFile[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [editorTheme, setEditorTheme] = useState<'alphintra-dark' | 'alphintra-light'>('alphintra-dark')
  const [showAIPanel, setShowAIPanel] = useState(true)
  const [showTerminal, setShowTerminal] = useState(false)
  const [showCommandPalette, setShowCommandPalette] = useState(false)
  const [cursorPosition, setCursorPosition] = useState<{ lineNumber: number; column: number }>({ lineNumber: 1, column: 1 })
  const [wordWrapEnabled, setWordWrapEnabled] = useState<boolean>(true)
  const [minimapEnabled, setMinimapEnabled] = useState<boolean>(true)
  
  const editorRef = useRef<any>(null)
  const { 
    generateCode, 
    explainCode, 
    optimizeCode, 
    debugCode, 
    generateTests,
    isGenerating,
    error: aiError
  } = useAICodeStore()
  const { isExplaining, isOptimizing, isDebugging } = useAICodeOperationStates()
  const { resolvedTheme } = useTheme()

  // Initialize project
  useEffect(() => {
    if (projectId) {
      loadProject(projectId)
    } else {
      // Create default project
      const defaultProject: Project = {
        id: 'default',
        name: 'Trading Strategy',
        description: 'AI-powered trading strategy development',
        files: [
          {
            id: 'main',
            name: 'main.py',
            path: '/main.py',
            content: '# AI-powered trading strategy\n# Start typing or use the AI assistant to generate code\n\nimport pandas as pd\nimport numpy as np\nfrom typing import Dict, List\n\nclass TradingStrategy:\n    def __init__(self):\n        self.name = "AI Generated Strategy"\n        \n    def execute(self, data: pd.DataFrame) -> Dict:\n        # Your trading logic here\n        pass\n',
            language: 'python',
            modified: false,
            isActive: true
          }
        ],
        settings: {
          aiEnabled: editorMode !== 'traditional',
          suggestions: true,
          autoComplete: true,
          errorDetection: true,
          testGeneration: true
        }
      }
      setCurrentProject(defaultProject)
      setActiveFile(defaultProject.files[0])
      setOpenFiles([defaultProject.files[0]])
    }
  }, [projectId, editorMode])

  const loadProject = async (id: string) => {
    try {
      setIsLoading(true)
      // In real implementation, fetch from API
      const response = await fetch(`/api/projects/${id}`)
      if (response.ok) {
        const project = await response.json()
        setCurrentProject(project)
        if (project.files.length > 0) {
          setActiveFile(project.files[0])
          setOpenFiles([project.files[0]])
        }
      }
    } catch (error) {
      console.error('Failed to load project:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const switchMode = useCallback((newMode: EditorMode) => {
    // Preserve current code and context
    const currentContent = editorRef.current?.getValue() || ''
    
    // Update project settings based on mode
    if (currentProject) {
      const updatedProject = {
        ...currentProject,
        settings: {
          ...currentProject.settings,
          aiEnabled: newMode !== 'traditional',
          suggestions: newMode === 'ai-assisted' || newMode === 'ai-first',
          autoComplete: newMode !== 'traditional'
        }
      }
      setCurrentProject(updatedProject)
    }
    
    // Update active file content if changed
    if (activeFile && currentContent !== activeFile.content) {
      const updatedFile: IDEFile = { ...activeFile, content: currentContent, modified: true }
      setActiveFile(updatedFile)
      updateFileContent(updatedFile)
    }
    
    // Adjust UI layout for new mode
    if (newMode === 'ai-first') {
      setShowAIPanel(true)
    } else if (newMode === 'traditional') {
      setShowAIPanel(false)
    } else {
      setShowAIPanel(true)
    }
    
    setEditorMode(newMode)
  }, [currentProject, activeFile])

  const updateFileContent = (updatedFile: IDEFile) => {
    if (!currentProject) return
    
    const updatedFiles = currentProject.files.map(file =>
      file.id === updatedFile.id ? updatedFile : file
    )
    
    setCurrentProject({
      ...currentProject,
      files: updatedFiles
    })
    
    // Update open files
    setOpenFiles(prev =>
      prev.map(file => file.id === updatedFile.id ? updatedFile : file)
    )
  }

  const handleEditorChange = (value: string | undefined) => {
    if (activeFile && value !== undefined) {
      const updatedFile: IDEFile = {
        ...activeFile,
        content: value,
        modified: activeFile.content !== value
      }
      setActiveFile(updatedFile)
      updateFileContent(updatedFile)
    }
  }

  const openFile = (file: ExplorerFile) => {
    const normalized: IDEFile = { ...file, modified: !!file.modified }
    setActiveFile(normalized)
    if (!openFiles.find(f => f.id === normalized.id)) {
      setOpenFiles(prev => [...prev, normalized])
    }
  }

  const closeFile = (fileId: string) => {
    const newOpenFiles = openFiles.filter(f => f.id !== fileId)
    setOpenFiles(newOpenFiles)
    
    if (activeFile?.id === fileId) {
      setActiveFile(newOpenFiles.length > 0 ? newOpenFiles[0] : null)
    }
  }

  const saveFile = async () => {
    if (!activeFile) return
    
    try {
      if (onSave) {
        await onSave(activeFile)
      }
      
      const updatedFile: IDEFile = { ...activeFile, modified: false }
      setActiveFile(updatedFile)
      updateFileContent(updatedFile)
    } catch (error) {
      console.error('Failed to save file:', error)
    }
  }

  const runCode = async () => {
    if (!activeFile) return
    
    try {
      if (onRun) {
        await onRun(activeFile)
      }
      setShowTerminal(true)
    } catch (error) {
      console.error('Failed to run code:', error)
    }
  }

  const handleAIGenerate = async (prompt: string) => {
    if (!activeFile) return
    
    try {
      const result = await generateCode({
        prompt,
        context: activeFile.content,
        language: activeFile.language,
        complexity_level: 'intermediate',
        include_comments: true
      })
      
      if (result.code) {
        // Replace or append generated code
        const currentContent = editorRef.current?.getValue() || ''
        const newContent = currentContent + '\n\n' + result.code
        editorRef.current?.setValue(newContent)
        handleEditorChange(newContent)
      }
    } catch (error) {
      console.error('AI generation failed:', error)
    }
  }

  const handleAIExplain = async (selectedText?: string) => {
    if (!activeFile) return
    
    const codeToExplain = selectedText || activeFile.content
    
    try {
      await explainCode({
        code: codeToExplain,
        context: activeFile.content,
        focus_areas: ['functionality', 'performance', 'trading_logic']
      })
    } catch (error) {
      console.error('AI explanation failed:', error)
    }
  }

  const handleAIOptimize = async () => {
    if (!activeFile) return
    
    try {
      const result = await optimizeCode({
        code: activeFile.content,
        optimization_type: 'performance',
        context: 'Trading strategy optimization',
        preserve_functionality: true
      })
      
      if (result.optimized_code) {
        editorRef.current?.setValue(result.optimized_code)
        handleEditorChange(result.optimized_code)
      }
    } catch (error) {
      console.error('AI optimization failed:', error)
    }
  }

  // Sync Monaco theme with app theme (black-gold accent preserved)
  useEffect(() => {
    setEditorTheme(resolvedTheme === 'dark' ? 'alphintra-dark' : 'alphintra-light')
  }, [resolvedTheme])

  // Global keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase()
      if ((e.metaKey || e.ctrlKey) && key === 's') {
        e.preventDefault()
        saveFile()
      } else if ((e.metaKey || e.ctrlKey) && key === 'enter') {
        e.preventDefault()
        runCode()
      } else if ((e.metaKey || e.ctrlKey) && (key === 'k' || key === 'p')) {
        e.preventDefault()
        setShowCommandPalette(true)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [activeFile])

  // Define Monaco custom themes before mount
  const defineMonacoThemes = (monaco: any) => {
    const gold = '#FFBF00'
    const darkBg = '#000000'
    const darkCard = '#0A0A0A'
    const lightBg = '#FFFFFF'
    const lightCard = '#F9FAFB'

    monaco.editor.defineTheme('alphintra-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: '', foreground: 'FFFFFF', background: '000000' },
        { token: 'comment', foreground: '7D7D7D', fontStyle: 'italic' },
        { token: 'keyword', foreground: 'E6B800', fontStyle: 'bold' },
        { token: 'number', foreground: '9CDCFE' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'type', foreground: '4FC1FF' },
        { token: 'function', foreground: 'DCDCAA' }
      ],
      colors: {
        'editor.background': darkBg,
        'editor.foreground': '#FFFFFF',
        'editor.lineHighlightBackground': '#0D0D0D',
        'editor.selectionBackground': '#FFBF0033',
        'editor.inactiveSelectionBackground': '#FFBF001A',
        'editorCursor.foreground': gold,
        'editorWhitespace.foreground': '#2A2A2A',
        'editorLineNumber.foreground': '#6B7280',
        'editorLineNumber.activeForeground': gold,
        'editorIndentGuide.background': '#2A2A2A',
        'editorIndentGuide.activeBackground': '#3A3A3A',
        'editorGutter.background': darkCard,
        'minimap.background': darkBg,
        'tab.activeBackground': darkBg,
        'tab.inactiveBackground': '#0B0B0B',
        'tab.activeForeground': '#FFFFFF',
        'tab.inactiveForeground': '#9CA3AF'
      }
    })

    monaco.editor.defineTheme('alphintra-light', {
      base: 'vs',
      inherit: true,
      rules: [
        { token: '', foreground: '111111', background: 'FFFFFF' },
        { token: 'comment', foreground: '94A3B8', fontStyle: 'italic' },
        { token: 'keyword', foreground: 'B38600', fontStyle: 'bold' },
        { token: 'number', foreground: '1D4ED8' },
        { token: 'string', foreground: '166534' },
        { token: 'type', foreground: '0EA5E9' },
        { token: 'function', foreground: '7C3AED' }
      ],
      colors: {
        'editor.background': lightBg,
        'editor.foreground': '#111111',
        'editor.lineHighlightBackground': '#F3F4F6',
        'editor.selectionBackground': '#FFBF0026',
        'editor.inactiveSelectionBackground': '#FFBF0014',
        'editorCursor.foreground': '#CC9A00',
        'editorWhitespace.foreground': '#E5E7EB',
        'editorLineNumber.foreground': '#9CA3AF',
        'editorLineNumber.activeForeground': '#CC9A00',
        'editorIndentGuide.background': '#E5E7EB',
        'editorIndentGuide.activeBackground': '#D1D5DB',
        'editorGutter.background': lightCard,
        'minimap.background': lightBg
      }
    })
  }

  const formatDocument = useCallback(() => {
    try {
      const action = editorRef.current?.getAction?.('editor.action.formatDocument')
      action?.run()
    } catch (e) {
      // no-op
    }
  }, [])

  const toggleWrap = () => setWordWrapEnabled(prev => !prev)
  const toggleMinimap = () => setMinimapEnabled(prev => !prev)

  // Command palette commands
  const commands = useMemo(() => {
    const list = [
      { id: 'save', title: 'File: Save', shortcut: 'Ctrl/Cmd+S', action: saveFile },
      { id: 'run', title: 'Run: Execute', shortcut: 'Ctrl/Cmd+Enter', action: runCode },
      { id: 'format', title: 'Editor: Format Document', action: formatDocument },
      { id: 'toggle-ai', title: showAIPanel ? 'View: Hide AI Assistant' : 'View: Show AI Assistant', action: () => setShowAIPanel(v => !v) },
      { id: 'toggle-terminal', title: showTerminal ? 'View: Hide Terminal' : 'View: Show Terminal', action: () => setShowTerminal(v => !v) },
      { id: 'wrap', title: wordWrapEnabled ? 'Editor: Disable Word Wrap' : 'Editor: Enable Word Wrap', action: toggleWrap },
      { id: 'minimap', title: minimapEnabled ? 'Editor: Hide Minimap' : 'Editor: Show Minimap', action: toggleMinimap },
      { id: 'mode-traditional', title: 'Mode: Traditional', action: () => switchMode('traditional') },
      { id: 'mode-ai-assisted', title: 'Mode: AI Assisted', action: () => switchMode('ai-assisted') },
      { id: 'mode-ai-first', title: 'Mode: AI First', action: () => switchMode('ai-first') },
    ] as Array<{ id: string; title: string; shortcut?: string; action: () => void }>
    return list
  }, [showAIPanel, showTerminal, wordWrapEnabled, minimapEnabled, editorMode, activeFile])

  const handleAIDebug = async (errorMessage?: string) => {
    if (!activeFile) return
    
    try {
      const result = await debugCode({
        code: activeFile.content,
        error_message: errorMessage || '',
        context: 'Trading strategy debugging'
      })
      
      if (result.corrected_code) {
        editorRef.current?.setValue(result.corrected_code)
        handleEditorChange(result.corrected_code)
      }
    } catch (error) {
      console.error('AI debugging failed:', error)
    }
  }

  const getEditorModeIcon = (mode: EditorMode) => {
    switch (mode) {
      case 'traditional': return <Code className="h-4 w-4" />
      case 'ai-assisted': return <Brain className="h-4 w-4" />
      case 'ai-first': return <Zap className="h-4 w-4" />
    }
  }

  const getEditorModeDescription = (mode: EditorMode) => {
    switch (mode) {
      case 'traditional': return 'Full IDE features without AI assistance'
      case 'ai-assisted': return 'AI suggestions and chat enabled'
      case 'ai-first': return 'Natural language programming interface'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading project...</span>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Top Toolbar */}
      <div className="border-b border-border p-2 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-lg font-semibold">
            {currentProject?.name || 'Enhanced IDE'}
          </h1>
          {activeFile && (
            <div className="hidden md:flex items-center text-xs text-muted-foreground">
              <FolderTree className="h-3 w-3 mr-1 text-primary" />
              {activeFile.path.split('/').filter(Boolean).map((part, idx, arr) => (
                <div key={idx} className="flex items-center">
                  <span className={idx === arr.length - 1 ? 'text-foreground' : ''}>{part}</span>
                  {idx < arr.length - 1 && <ChevronRight className="h-3 w-3 mx-1" />}
                </div>
              ))}
            </div>
          )}
          
          {/* Mode Switcher */}
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="flex items-center space-x-2">
                {getEditorModeIcon(editorMode)}
                <span className="capitalize">{editorMode}</span>
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Switch Editor Mode</DialogTitle>
              </DialogHeader>
              <div className="space-y-3">
                {(['traditional', 'ai-assisted', 'ai-first'] as EditorMode[]).map((mode) => (
                  <Button
                    key={mode}
                    variant={editorMode === mode ? 'default' : 'outline'}
                    className="w-full justify-start"
                    onClick={() => switchMode(mode)}
                  >
                    <div className="flex items-center space-x-3">
                      {getEditorModeIcon(mode)}
                      <div className="text-left">
                        <div className="font-medium capitalize">{mode}</div>
                        <div className="text-sm text-muted-foreground">
                          {getEditorModeDescription(mode)}
                        </div>
                      </div>
                    </div>
                  </Button>
                ))}
              </div>
            </DialogContent>
          </Dialog>
          
          {/* File tabs */}
          <div className="flex items-center space-x-1">
            {openFiles.map((file: IDEFile, index: number) => (
              <div
                key={file.id || index}
                className={`flex items-center space-x-2 px-3 py-1 rounded-t-md border-b-2 cursor-pointer ${
                  file.id === activeFile?.id
                    ? 'bg-background border-primary'
                    : 'bg-muted border-transparent hover:bg-background/50'
                }`}
                onClick={() => setActiveFile(file)}
              >
                <FileText className="h-3 w-3" />
                <span className="text-sm">{file.name}</span>
                {file.modified && <div className="w-2 h-2 bg-orange-500 rounded-full" />}
                <button
                  className="text-muted-foreground hover:text-foreground"
                  onClick={(e) => {
                    e.stopPropagation()
                    closeFile(file.id)
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {(isGenerating || isExplaining || isOptimizing || isDebugging) && (
            <div className="hidden sm:flex items-center text-xs text-muted-foreground mr-2">
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary mr-2"></div>
              AI active
            </div>
          )}
          <Button variant="outline" size="sm" onClick={saveFile}>
            <Save className="h-4 w-4 mr-1" />
            Save
          </Button>
          <Button variant="outline" size="sm" onClick={runCode}>
            <Play className="h-4 w-4 mr-1" />
            Run
          </Button>
          <Button variant="outline" size="sm" onClick={formatDocument}>
            <Code className="h-4 w-4 mr-1" />
            Format
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAIPanel(!showAIPanel)}
          >
            <Bot className="h-4 w-4 mr-1" />
            AI Assistant
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCommandPalette(true)}
          >
            <Search className="h-4 w-4 mr-1" />
            Commands
          </Button>
        </div>
      </div>
      
      {/* Main Content */}
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* Left Panel - Project Explorer */}
        <ResizablePanel defaultSize={20} minSize={15}>
          <div className="h-full border-r border-border">
            <ProjectExplorer 
              project={currentProject}
              onFileSelect={openFile}
              activeFile={activeFile}
            />
          </div>
        </ResizablePanel>
        
        <ResizableHandle />
        
        {/* Center Panel - Code Editor */}
        <ResizablePanel defaultSize={showAIPanel ? 55 : 75}>
          <ResizablePanelGroup direction="vertical">
            <ResizablePanel defaultSize={showTerminal ? 70 : 100}>
              <div className="h-full">
                {activeFile ? (
                  <Editor
                    height="100%"
                    language={activeFile.language}
                    value={activeFile.content}
                    onChange={handleEditorChange}
                    theme={editorTheme}
                    beforeMount={defineMonacoThemes}
                    onMount={(editor, monaco) => {
                      editorRef.current = editor
                      // Ensure theme applied post-mount
                      try { monaco?.editor?.setTheme?.(editorTheme) } catch {}
                      // Cursor tracking
                      editor.onDidChangeCursorPosition((e: any) => setCursorPosition(e.position))
                    }}
                    options={{
                      minimap: { enabled: minimapEnabled },
                      fontSize: 14,
                      lineNumbers: 'on',
                      roundedSelection: false,
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                      suggestOnTriggerCharacters: currentProject?.settings.suggestions,
                      quickSuggestions: currentProject?.settings.autoComplete,
                      wordWrap: wordWrapEnabled ? 'on' : 'off',
                      folding: true,
                      bracketMatching: 'always'
                    }}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    Select a file to start editing
                  </div>
                )}
              </div>
            </ResizablePanel>
            
            {showTerminal && (
              <>
                <ResizableHandle />
                <ResizablePanel defaultSize={30} minSize={20}>
                  <TerminalPanel onClose={() => setShowTerminal(false)} />
                </ResizablePanel>
              </>
            )}
          </ResizablePanelGroup>
        </ResizablePanel>
        
        {/* Right Panel - AI Assistant */}
        {showAIPanel && (
          <>
            <ResizableHandle />
            <ResizablePanel defaultSize={25} minSize={20}>
              <div className="h-full border-l border-border">
                <AIAssistantPanel
                  mode={editorMode}
                  currentFile={activeFile}
                  onGenerate={handleAIGenerate}
                  onExplain={handleAIExplain}
                  onOptimize={handleAIOptimize}
                  onDebug={handleAIDebug}
                  isGenerating={isGenerating}
                  error={aiError}
                />
              </div>
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>

      {/* Status Bar */}
      <div className="border-t border-border">
        <StatusBar
          line={cursorPosition.lineNumber}
          column={cursorPosition.column}
          language={activeFile?.language || 'plaintext'}
          wordWrapEnabled={wordWrapEnabled}
          minimapEnabled={minimapEnabled}
          onToggleWrap={toggleWrap}
          onToggleMinimap={toggleMinimap}
          onFormat={formatDocument}
          themeName={editorTheme === 'alphintra-dark' ? 'Dark (Black-Gold)' : 'Light'}
        />
      </div>

      {/* Command Palette */}
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        commands={commands}
      />
    </div>
  )
}