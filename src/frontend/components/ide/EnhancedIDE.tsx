'use client'

import React, { useState, useEffect, useRef, useCallback, useMemo, memo } from 'react'
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
  ChevronDown,
  Sun,
  Moon,
  Monitor,
  Maximize2,
  Minimize2,
  MoreHorizontal,
  GitBranch,
  Package,
  Database,
  Layers,
  Command,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Split,
  Folder,
  X
} from 'lucide-react'
import { useTheme } from 'next-themes'
import { OptimizedMonacoEditor } from './LazyComponents'
import { ProjectExplorer } from './ProjectExplorer'
import { AIAssistantPanel } from './AIAssistantPanel'
import { TerminalPanel } from './TerminalPanel'
import { useAICodeStore } from '@/lib/stores/ai-code-store'
import { optimizeForPerformance, PerformanceMonitor } from './PerformanceOptimizer'

// Memoized components for performance
const MemoizedProjectExplorer = memo(ProjectExplorer)
const MemoizedAIAssistantPanel = memo(AIAssistantPanel)
const MemoizedTerminalPanel = memo(TerminalPanel)

export type EditorMode = 'traditional' | 'ai-assisted' | 'ai-first'

interface File {
  id: string
  name: string
  path: string
  content: string
  language: string
  modified: boolean
  isActive?: boolean
}

interface Project {
  id: string
  name: string
  description: string
  files: File[]
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
  onSave?: (file: File) => Promise<void>
  onRun?: (file: File) => Promise<void>
}

export function EnhancedIDE({ 
  projectId, 
  initialMode = 'ai-assisted', 
  onSave, 
  onRun 
}: EnhancedIDEProps) {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  
  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true)
  }, [])
  const [editorMode, setEditorMode] = useState<EditorMode>(initialMode)
  const [currentProject, setCurrentProject] = useState<Project | null>(null)
  const [activeFile, setActiveFile] = useState<File | null>(null)
  const [openFiles, setOpenFiles] = useState<File[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showAIPanel, setShowAIPanel] = useState(true)
  const [showLeftPanel, setShowLeftPanel] = useState(true)
  const [showTerminal, setShowTerminal] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  
  // Performance optimizations on mount
  useEffect(() => {
    optimizeForPerformance()
  }, [])

  // Handle responsive design - optimized with debounce
  useEffect(() => {
    let timeoutId: NodeJS.Timeout
    
    const checkScreenSize = () => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => {
        const mobile = window.innerWidth < 768
        setIsMobile(prevMobile => {
          if (prevMobile !== mobile) {
            // Auto-hide panels on mobile
            if (mobile) {
              setShowLeftPanel(false)
              setShowAIPanel(false)
            }
            return mobile
          }
          return prevMobile
        })
      }, 100) // Debounce resize events
    }
    
    checkScreenSize()
    window.addEventListener('resize', checkScreenSize, { passive: true })
    
    return () => {
      window.removeEventListener('resize', checkScreenSize)
      clearTimeout(timeoutId)
    }
  }, [])
  
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

  // Optimized editor options - split into static and dynamic parts
  const staticEditorOptions = useMemo(() => ({
    lineNumbers: 'on' as const,
    lineNumbersMinChars: 4,
    glyphMargin: true,
    folding: true,
    foldingStrategy: 'indentation' as const,
    showFoldingControls: 'mouseover' as const, // Changed from 'always' for performance
    unfoldOnClickAfterEndOfLine: true,
    roundedSelection: false,
    scrollBeyondLastLine: false,
    automaticLayout: true,
    wordWrap: 'on' as const,
    wordWrapColumn: 120,
    wrappingIndent: 'indent' as const,
    bracketMatching: 'always' as const,
    matchBrackets: 'always' as const,
    autoClosingBrackets: 'always' as const,
    autoClosingQuotes: 'always' as const,
    autoSurround: 'languageDefined' as const,
    tabCompletion: 'on' as const,
    wordBasedSuggestions: false, // Disabled for performance
    parameterHints: { enabled: true },
    autoIndent: 'advanced' as const,
    formatOnType: false, // Disabled for performance
    formatOnPaste: false, // Disabled for performance
    dragAndDrop: true,
    links: true,
    colorDecorators: false, // Disabled for performance
    codeLens: false, // Disabled for performance
    contextmenu: true,
    mouseWheelScrollSensitivity: 1,
    fastScrollSensitivity: 5,
    overviewRulerBorder: false,
    overviewRulerLanes: 2, // Reduced for performance
    hideCursorInOverviewRuler: false,
    renderLineHighlight: 'line' as const, // Changed from 'all' for performance
    renderWhitespace: 'none' as const, // Changed from 'selection' for performance
    renderControlCharacters: false,
    renderIndentGuides: true,
    highlightActiveIndentGuide: true,
    rulers: [80, 120],
    find: {
      seedSearchStringFromSelection: 'always' as const,
      autoFindInSelection: 'never' as const,
      globalFindClipboard: false,
      addExtraSpaceOnTop: true
    }
  }), [])

  const dynamicEditorOptions = useMemo(() => ({
    minimap: { 
      enabled: !isMobile,
      size: 'proportional' as const,
      maxColumn: 120,
      renderCharacters: !isMobile, // Disable on mobile for performance
      showSlider: 'mouseover' as const // Changed from 'always' for performance
    },
    fontSize: isMobile ? 12 : 14,
    suggestOnTriggerCharacters: currentProject?.settings.suggestions ?? true,
    quickSuggestions: currentProject?.settings.autoComplete ?? {
      other: true,
      comments: false,
      strings: false
    },
    scrollbar: {
      useShadows: !isMobile, // Disable shadows on mobile
      verticalHasArrows: false,
      horizontalHasArrows: false,
      vertical: 'visible' as const,
      horizontal: 'visible' as const,
      verticalScrollbarSize: isMobile ? 6 : 8, // Smaller scrollbars
      horizontalScrollbarSize: isMobile ? 6 : 8
    }
  }), [isMobile, currentProject?.settings.suggestions, currentProject?.settings.autoComplete])

  const editorOptions = useMemo(() => ({
    ...staticEditorOptions,
    ...dynamicEditorOptions
  }), [staticEditorOptions, dynamicEditorOptions])
  
  // Optimized callback functions
  const handleFileSelect = useCallback((projectFile: any) => {
    // Check if file is already open to avoid duplicates
    const existingFile = openFiles.find(f => f.id === projectFile.id)

    if (existingFile) {
      // Use existing file object to maintain React key consistency
      setActiveFile(existingFile)
    } else {
      // Convert ProjectFile to File, ensuring modified is always boolean
      const file: File = {
        ...projectFile,
        modified: projectFile.modified ?? false
      }
      openFile(file)
    }
    if (isMobile) setShowLeftPanel(false)
  }, [isMobile, openFiles])

  const handleCloseTerminal = useCallback(() => {
    setShowTerminal(false)
  }, [])

  const handleEditorMount = useCallback((editor: any) => {
    editorRef.current = editor
    
    // Optimized editor configuration
    editor.updateOptions({
      fontFamily: 'JetBrains Mono, Fira Code, Cascadia Code, SF Mono, Consolas, Liberation Mono, Menlo, monospace',
      fontSize: isMobile ? 12 : 14,
      lineHeight: 1.6,
      letterSpacing: 0.5,
      fontLigatures: true,
      cursorBlinking: 'phase',
      cursorSmoothCaretAnimation: false, // Disabled for performance
      smoothScrolling: false, // Disabled for performance
      mouseWheelZoom: false // Disabled for performance
    })
  }, [isMobile])

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
      const updatedFile = { ...activeFile, content: currentContent, modified: true }
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

  const updateFileContent = (updatedFile: File) => {
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

  const handleEditorChange = useCallback((value: string | undefined) => {
    if (activeFile && value !== undefined && value !== activeFile.content) {
      const updatedFile = {
        ...activeFile,
        content: value,
        modified: true
      }
      setActiveFile(updatedFile)
      updateFileContent(updatedFile)
    }
  }, [activeFile])

  const openFile = (file: File) => {
    setActiveFile(file)
    if (!openFiles.find(f => f.id === file.id)) {
      setOpenFiles(prev => [...prev, file])
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
      
      const updatedFile = { ...activeFile, modified: false }
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

  // Loading state with skeleton
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <div className="text-center space-y-4 fade-in">
          <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-primary" />
          </div>
          <div>
            <h3 className={`font-medium text-foreground mb-2 ${
              isMobile ? 'text-base' : 'text-lg'
            }`}>
              Loading Strategy Hub IDE
            </h3>
            <p className={`text-muted-foreground ${
              isMobile ? 'text-xs' : 'text-sm'
            }`}>
              Preparing your development environment...
            </p>
          </div>
          <div className="w-48 h-2 bg-muted rounded-full overflow-hidden mx-auto">
            <div className="h-full bg-primary rounded-full shimmer" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <PerformanceMonitor />
      <div className="h-screen flex flex-col bg-background text-foreground gpu-accelerated">
      {/* Enhanced Responsive Toolbar */}
      <div className="ide-toolbar">
        <div className={`flex items-center ${isMobile ? 'justify-between w-full' : 'space-x-6'}`}>
          {/* Project Info */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Folder className="h-5 w-5 text-ide-accent" />
              <h1 className={`font-semibold text-foreground ${
                isMobile ? 'text-base' : 'text-lg'
              }`}>
                {isMobile 
                  ? (currentProject?.name || 'IDE').slice(0, 12) + '...'
                  : currentProject?.name || 'Strategy Hub IDE'
                }
              </h1>
            </div>
            {!isMobile && (
              <Badge variant="outline" className="text-xs bg-primary/10 text-primary border-primary/20">
                v2.0.0
              </Badge>
            )}
          </div>
          
          {/* Mobile Menu Button */}
          {isMobile && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowLeftPanel(!showLeftPanel)}
              className="ide-button-ghost"
            >
              <Command className="h-4 w-4" />
            </Button>
          )}
          
          {/* Desktop Controls */}
          {!isMobile && (
            <>
              {/* Mode Switcher */}
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm" className="ide-button-secondary">
                    {getEditorModeIcon(editorMode)}
                    <span className="ml-2 capitalize">{editorMode.replace('-', ' ')}</span>
                    <ChevronDown className="h-3 w-3 ml-1" />
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-card border-border">
                  <DialogHeader>
                    <DialogTitle className="text-foreground">Switch Editor Mode</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-3">
                    {(['traditional', 'ai-assisted', 'ai-first'] as EditorMode[]).map((mode) => (
                      <Button
                        key={mode}
                        variant={editorMode === mode ? 'default' : 'outline'}
                        className={`w-full justify-start ${
                          editorMode === mode ? 'ide-button-primary' : 'ide-button-secondary'
                        }`}
                        onClick={() => switchMode(mode)}
                      >
                        <div className="flex items-center space-x-3">
                          {getEditorModeIcon(mode)}
                          <div className="text-left">
                            <div className="font-medium capitalize">{mode.replace('-', ' ')}</div>
                            <div className="text-sm opacity-70">
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
              <div className="flex items-center space-x-1 ml-4 overflow-x-auto">
                {openFiles.slice(0, isMobile ? 2 : 6).map((file) => (
                  <div
                    key={file.id}
                    className={`ide-tab whitespace-nowrap ${
                      file.id === activeFile?.id
                        ? 'ide-tab-active'
                        : 'ide-tab-inactive'
                    }`}
                    onClick={() => setActiveFile(file)}
                  >
                    <FileText className="h-3 w-3" />
                    <span className="text-sm max-w-[100px] truncate">
                      {file.name}
                    </span>
                    {file.modified && <div className="w-2 h-2 bg-ide-warning rounded-full" />}
                    <button
                      className="ml-2 opacity-60 hover:opacity-100 transition-opacity"
                      onClick={(e) => {
                        e.stopPropagation()
                        closeFile(file.id)
                      }}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
                {openFiles.length > (isMobile ? 2 : 6) && (
                  <Button variant="ghost" size="sm" className="ide-button-ghost px-2">
                    <MoreHorizontal className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </>
          )}
        </div>
        
        <div className={`flex items-center ${isMobile ? 'space-x-1' : 'space-x-2'}`}>
          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="ide-button-ghost"
            title={mounted ? `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme` : 'Switch theme'}
          >
            {!mounted ? (
              <Monitor className="h-4 w-4" />
            ) : theme === 'dark' ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>
          
          {/* Layout Controls - Hidden on mobile */}
          {!isMobile && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowLeftPanel(!showLeftPanel)}
                className={`ide-button-ghost ${showLeftPanel ? 'text-primary' : ''}`}
                title={showLeftPanel ? 'Hide Explorer' : 'Show Explorer'}
              >
                {showLeftPanel ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAIPanel(!showAIPanel)}
                className={`ide-button-ghost ${showAIPanel ? 'text-primary' : ''}`}
                title={showAIPanel ? 'Hide AI Assistant' : 'Show AI Assistant'}
              >
                {showAIPanel ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowTerminal(!showTerminal)}
                className={`ide-button-ghost ${showTerminal ? 'text-primary' : ''}`}
                title={showTerminal ? 'Hide Terminal' : 'Show Terminal'}
              >
                <Terminal className="h-4 w-4" />
              </Button>
              
              <div className="w-px h-6 bg-ide-border mx-2" />
            </>
          )}
          
          {/* Action Buttons */}
          <Button 
            size="sm" 
            onClick={saveFile} 
            className={`ide-button-secondary ${isMobile ? 'px-2' : ''}`}
            title="Save file"
          >
            <Save className="h-4 w-4" />
            {!isMobile && <span className="ml-2">Save</span>}
          </Button>
          
          <Button 
            size="sm" 
            onClick={runCode} 
            className={`ide-button-primary ${isMobile ? 'px-2' : ''}`}
            title="Run code"
          >
            <Play className="h-4 w-4" />
            {!isMobile && <span className="ml-2">Run</span>}
          </Button>
          
          {/* AI Assistant Toggle - Always visible */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAIPanel(!showAIPanel)}
            className={`ide-button-secondary ${isMobile ? 'px-2' : ''} ${
              showAIPanel ? 'bg-primary/10 text-primary border-primary/20' : ''
            }`}
            title="Toggle AI Assistant"
          >
            <Bot className="h-4 w-4" />
            {!isMobile && <span className="ml-2">AI</span>}
          </Button>
          
          {/* More menu for mobile */}
          {isMobile && (
            <Button variant="ghost" size="sm" className="ide-button-ghost px-2">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
      
      {/* Enhanced Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Mobile overlay for left panel */}
        {isMobile && showLeftPanel && (
          <div 
            className="fixed inset-0 bg-black/50 z-40 md:hidden" 
            onClick={() => setShowLeftPanel(false)}
          />
        )}
        
        {/* Left Panel - Project Explorer */}
        {showLeftPanel && (
          <div className={`${
            isMobile 
              ? 'fixed left-0 top-0 h-full w-80 z-50 transform transition-transform duration-300 ease-in-out'
              : 'relative'
          } ide-sidebar border-r border-border`}
          style={{
            width: isMobile ? '320px' : '280px',
            minWidth: isMobile ? '320px' : '240px',
            maxWidth: isMobile ? '320px' : '400px'
          }}>
            <MemoizedProjectExplorer 
              project={currentProject}
              onFileSelect={handleFileSelect}
              activeFile={activeFile}
            />
          </div>
        )}
        
        {/* Center Panel - Code Editor */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex-1 flex flex-col">
            <div className={`flex-1 ${showTerminal ? 'h-3/4' : 'h-full'}`}>
              <div className="h-full bg-background relative">
                {activeFile ? (
                  <div className="h-full relative">
                    <OptimizedMonacoEditor
                      height="100%"
                      language={activeFile.language}
                      value={activeFile.content}
                      onChange={handleEditorChange}
                      theme={theme === 'dark' ? 'vs-dark' : 'light'}
                        onMount={handleEditorMount}
                      options={editorOptions}
                    />
                    
                    {/* Editor Status Bar */}
                    <div className="ide-status-bar">
                      <div className="flex items-center space-x-4">
                        <span className="flex items-center space-x-1">
                          <span className="text-primary">●</span>
                          <span>{activeFile.language.toUpperCase()}</span>
                        </span>
                        <span>Line {1}, Col {1}</span>
                        <span>UTF-8</span>
                        <span>LF</span>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span>Spaces: 2</span>
                        <span>{activeFile.content.split('\n').length} lines</span>
                        <span>{activeFile.content.length} chars</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-ide-text-muted">
                    <div className="text-center space-y-4 p-8">
                      <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                        <Code className="h-8 w-8 text-primary" />
                      </div>
                      <div>
                        <h3 className={`font-medium text-foreground mb-2 ${
                          isMobile ? 'text-base' : 'text-lg'
                        }`}>
                          Welcome to Strategy Hub IDE
                        </h3>
                        <p className={`text-muted-foreground max-w-md ${
                          isMobile ? 'text-xs' : 'text-sm'
                        }`}>
                          {isMobile 
                            ? 'Tap the menu button to access files and AI tools.'
                            : 'Select a file from the project explorer to start editing, or create a new file to begin your trading strategy development.'
                          }
                        </p>
                      </div>
                      <div className={`flex items-center justify-center ${
                        isMobile ? 'flex-col space-y-2' : 'space-x-2'
                      }`}>
                        <Button size="sm" className="ide-button-primary">
                          <FileText className="h-4 w-4 mr-2" />
                          New File
                        </Button>
                        <Button size="sm" variant="outline" className="ide-button-secondary">
                          <Folder className="h-4 w-4 mr-2" />
                          Open Folder
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            {showTerminal && (
              <div className="h-1/4 min-h-[200px] border-t border-border">
                <MemoizedTerminalPanel onClose={handleCloseTerminal} />
              </div>
            )}
          </div>
        </div>
        
        {/* Mobile overlay for right panel */}
        {isMobile && showAIPanel && (
          <div 
            className="fixed inset-0 bg-black/50 z-40 md:hidden" 
            onClick={() => setShowAIPanel(false)}
          />
        )}
        
        {/* Right Panel - AI Assistant */}
        {showAIPanel && (
          <div className={`${
            isMobile 
              ? 'fixed right-0 top-0 h-full w-80 z-50 transform transition-transform duration-300 ease-in-out'
              : 'relative'
          } ide-sidebar border-l border-border`}
          style={{
            width: isMobile ? '320px' : '320px',
            minWidth: isMobile ? '320px' : '280px',
            maxWidth: isMobile ? '320px' : '400px'
          }}>
            <MemoizedAIAssistantPanel
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
        )}
      </div>
    </div>
    </>
  )
}