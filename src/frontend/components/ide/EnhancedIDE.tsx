'use client'

import React, { useState, useEffect, useRef, useCallback, useMemo, startTransition } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import {
  Code,
  FileText,
  Play,
  Save,
  Bot,
  Brain,
  Zap,
  Terminal,
  RefreshCw,
  ChevronDown,
  Sun,
  Moon,
  Monitor,
  MoreHorizontal,
  Command,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Folder,
  X
} from 'lucide-react'
import { useTheme } from 'next-themes'
import { OptimizedMonacoEditor } from './LazyComponents'
import { OptimizedProjectExplorer } from './OptimizedProjectExplorer'
import { OptimizedAIAssistantPanel } from './OptimizedAIAssistantPanel'
import { OptimizedTerminalPanel } from './OptimizedTerminalPanel'
import { useAICodeStore } from '@/lib/stores/ai-code-store'

// Already optimized and memoized components
// No need for additional memo wrapping

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
  const [isMobile, setIsMobile] = useState(false)
  const [isCreatingFile, setIsCreatingFile] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [showMobileMenu, setShowMobileMenu] = useState(false)
  const [notification, setNotification] = useState<{type: 'success' | 'error', message: string} | null>(null)



  // Performance refs
  const resizeTimeoutRef = useRef<NodeJS.Timeout>()
  const changeTimeoutRef = useRef<NodeJS.Timeout>()
  const fileInputRef = useRef<HTMLInputElement>(null)
  

  // Optimized responsive design with improved debouncing
  useEffect(() => {
    const checkScreenSize = () => {
      if (resizeTimeoutRef.current) clearTimeout(resizeTimeoutRef.current)

      resizeTimeoutRef.current = setTimeout(() => {
        const mobile = window.innerWidth < 768

        startTransition(() => {
          setIsMobile(prevMobile => {
            if (prevMobile !== mobile) {
              if (mobile) {
                setShowLeftPanel(false)
                setShowAIPanel(false)
              }
              return mobile
            }
            return prevMobile
          })
        })
      }, 150)
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize, { passive: true })

    return () => {
      window.removeEventListener('resize', checkScreenSize)
      if (resizeTimeoutRef.current) clearTimeout(resizeTimeoutRef.current)
    }
  }, [])
  
  const editorRef = useRef<any>(null) // Monaco editor type
  const {
    generateCode,
    explainCode,
    optimizeCode,
    debugCode,
    isGenerating,
    error: aiError
  } = useAICodeStore()

  // Memoized default project to prevent recreation
  const defaultProject = useMemo((): Project => ({
    id: 'default',
    name: 'Trading Strategy',
    description: 'AI-powered trading strategy development',
    files: [{
      id: 'main',
      name: 'main.py',
      path: '/main.py',
      content: '# AI-powered trading strategy\n# Start typing or use the AI assistant to generate code\n\nimport pandas as pd\nimport numpy as np\nfrom typing import Dict, List\n\nclass TradingStrategy:\n    def __init__(self):\n        self.name = "AI Generated Strategy"\n        \n    def execute(self, data: pd.DataFrame) -> Dict:\n        # Your trading logic here\n        pass\n',
      language: 'python',
      modified: false,
      isActive: true
    }],
    settings: {
      aiEnabled: editorMode !== 'traditional',
      suggestions: true,
      autoComplete: true,
      errorDetection: true,
      testGeneration: true
    }
  }), [editorMode])

  // Initialize project with optimized logic
  useEffect(() => {
    if (projectId) {
      loadProject(projectId)
    } else if (!currentProject) {
      setCurrentProject(defaultProject)
      setActiveFile(defaultProject.files[0])
      setOpenFiles([defaultProject.files[0]])
    }
  }, [projectId, defaultProject, currentProject])

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

  const handleEditorMount = useCallback((editor: any) => { // Monaco editor instance
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

  const updateFileContent = useCallback((updatedFile: File) => {
    if (!currentProject) return

    const updatedFiles = currentProject.files.map(file =>
      file.id === updatedFile.id ? updatedFile : file
    )

    setCurrentProject({
      ...currentProject,
      files: updatedFiles
    })

    setOpenFiles(prev =>
      prev.map(file => file.id === updatedFile.id ? updatedFile : file)
    )
  }, [currentProject])

  const handleEditorChange = useCallback((value: string | undefined) => {
    if (!activeFile || value === undefined || value === activeFile.content) return

    if (changeTimeoutRef.current) clearTimeout(changeTimeoutRef.current)

    changeTimeoutRef.current = setTimeout(() => {
      const updatedFile = {
        ...activeFile,
        content: value,
        modified: true
      }

      startTransition(() => {
        setActiveFile(updatedFile)
        updateFileContent(updatedFile)
      })
    }, 100)
  }, [activeFile])

  const openFile = (file: File) => {
    setActiveFile(file)
    if (!openFiles.find(f => f.id === file.id)) {
      setOpenFiles(prev => [...prev, file])
    }
  }

  const performCloseFile = useCallback((fileId: string) => {
    const newOpenFiles = openFiles.filter(f => f.id !== fileId)

    startTransition(() => {
      setOpenFiles(newOpenFiles)
      if (activeFile?.id === fileId) {
        setActiveFile(newOpenFiles.length > 0 ? newOpenFiles[0] : null)
      }
    })
  }, [openFiles, activeFile?.id])

  const closeFile = useCallback((fileId: string) => {
    const fileToClose = openFiles.find(f => f.id === fileId)

    if (fileToClose?.modified) {
      const shouldSave = window.confirm(
        `${fileToClose.name} has unsaved changes. Do you want to save before closing?`
      )

      if (shouldSave && activeFile?.id === fileId) {
        // We'll handle this with a simpler approach - just close after asking
        performCloseFile(fileId)
        return
      }
    }

    performCloseFile(fileId)
  }, [openFiles, activeFile?.id, performCloseFile])

  const saveFile = useCallback(async () => {
    if (!activeFile || isSaving) return

    setIsSaving(true)
    try {
      if (onSave) {
        await onSave(activeFile)
      }

      const updatedFile = { ...activeFile, modified: false }
      startTransition(() => {
        setActiveFile(updatedFile)
        updateFileContent(updatedFile)
        setNotification({ type: 'success', message: `${activeFile.name} saved successfully` })
      })
    } catch (error) {
      console.error('Failed to save file:', error)
      setNotification({ type: 'error', message: `Failed to save ${activeFile.name}` })
    } finally {
      setIsSaving(false)
      // Clear notification after 3 seconds
      setTimeout(() => setNotification(null), 3000)
    }
  }, [activeFile, onSave, updateFileContent, isSaving])

  const runCode = useCallback(async () => {
    if (!activeFile || isRunning) return

    setIsRunning(true)
    try {
      if (onRun) {
        await onRun(activeFile)
      }
      startTransition(() => {
        setShowTerminal(true)
        setNotification({ type: 'success', message: `Running ${activeFile.name}...` })
      })
    } catch (error) {
      console.error('Failed to run code:', error)
      setNotification({ type: 'error', message: `Failed to run ${activeFile.name}` })
    } finally {
      setIsRunning(false)
      // Clear notification after 3 seconds
      setTimeout(() => setNotification(null), 3000)
    }
  }, [activeFile, onRun, isRunning])

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

  // New File functionality
  const createNewFile = useCallback(() => {
    if (isCreatingFile) return

    setIsCreatingFile(true)
    const fileName = prompt('Enter file name (with extension):', 'untitled.py')

    if (fileName && fileName.trim()) {
      const fileExtension = fileName.split('.').pop()?.toLowerCase() || 'txt'
      const languageMap: Record<string, string> = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'jsx': 'javascript',
        'html': 'html',
        'css': 'css',
        'json': 'json',
        'md': 'markdown',
        'sql': 'sql',
        'txt': 'plaintext'
      }

      const newFile: File = {
        id: `file-${Date.now()}`,
        name: fileName.trim(),
        path: `/${fileName.trim()}`,
        content: getTemplateContent(fileExtension),
        language: languageMap[fileExtension] || 'plaintext',
        modified: false
      }

      if (currentProject) {
        const updatedProject = {
          ...currentProject,
          files: [...currentProject.files, newFile]
        }

        startTransition(() => {
          setCurrentProject(updatedProject)
          setActiveFile(newFile)
          setOpenFiles(prev => [...prev, newFile])
          setNotification({ type: 'success', message: `Created ${fileName}` })
        })
      }
    }

    setIsCreatingFile(false)
    setTimeout(() => setNotification(null), 3000)
  }, [currentProject, isCreatingFile])

  // Get template content based on file extension
  const getTemplateContent = (extension: string): string => {
    const templates: Record<string, string> = {
      'py': '# New Python file\n\ndef main():\n    pass\n\nif __name__ == "__main__":\n    main()\n',
      'js': '// New JavaScript file\n\nfunction main() {\n    // Your code here\n}\n\nmain();\n',
      'ts': '// New TypeScript file\n\nfunction main(): void {\n    // Your code here\n}\n\nmain();\n',
      'html': '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Document</title>\n</head>\n<body>\n    \n</body>\n</html>\n',
      'css': '/* New CSS file */\n\nbody {\n    margin: 0;\n    padding: 0;\n}\n',
      'json': '{\n    "name": "example",\n    "version": "1.0.0"\n}\n',
      'md': '# New Document\n\n## Overview\n\nYour content here...\n'
    }
    return templates[extension] || ''
  }

  // Open Folder functionality
  const openFolder = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileInput = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    const newFiles: File[] = []
    const promises: Promise<void>[] = []

    for (let i = 0; i < Math.min(files.length, 10); i++) { // Limit to 10 files
      const file = files[i]
      const promise = new Promise<void>((resolve) => {
        const reader = new FileReader()
        reader.onload = (e) => {
          const content = e.target?.result as string || ''
          const fileExtension = file.name.split('.').pop()?.toLowerCase() || 'txt'
          const languageMap: Record<string, string> = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'jsx': 'javascript',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'md': 'markdown',
            'sql': 'sql'
          }

          newFiles.push({
            id: `file-${Date.now()}-${i}`,
            name: file.name,
            path: `/${file.name}`,
            content,
            language: languageMap[fileExtension] || 'plaintext',
            modified: false
          })
          resolve()
        }
        reader.readAsText(file)
      })
      promises.push(promise)
    }

    Promise.all(promises).then(() => {
      if (currentProject && newFiles.length > 0) {
        const updatedProject = {
          ...currentProject,
          files: [...currentProject.files, ...newFiles]
        }

        startTransition(() => {
          setCurrentProject(updatedProject)
          setActiveFile(newFiles[0])
          setOpenFiles(prev => [...prev, ...newFiles])
          setNotification({ type: 'success', message: `Opened ${newFiles.length} file(s)` })
        })
      }
    })

    // Clear the input
    event.target.value = ''
    setTimeout(() => setNotification(null), 3000)
  }, [currentProject])

  // Mobile More Menu functionality
  const toggleMobileMenu = useCallback(() => {
    setShowMobileMenu(!showMobileMenu)
  }, [showMobileMenu])

  // File management utilities
  const duplicateFile = useCallback((file: File) => {
    const fileName = prompt('Enter new file name:', `${file.name.split('.')[0]}_copy.${file.name.split('.').pop()}`)

    if (fileName && fileName.trim()) {
      const newFile: File = {
        ...file,
        id: `file-${Date.now()}`,
        name: fileName.trim(),
        path: `/${fileName.trim()}`,
        modified: false
      }

      if (currentProject) {
        const updatedProject = {
          ...currentProject,
          files: [...currentProject.files, newFile]
        }

        startTransition(() => {
          setCurrentProject(updatedProject)
          setActiveFile(newFile)
          setOpenFiles(prev => [...prev, newFile])
          setNotification({ type: 'success', message: `Duplicated as ${fileName}` })
        })
      }
    }
    setTimeout(() => setNotification(null), 3000)
  }, [currentProject])

  const renameFile = useCallback((file: File) => {
    const newName = prompt('Enter new file name:', file.name)

    if (newName && newName.trim() && newName !== file.name) {
      const updatedFile = {
        ...file,
        name: newName.trim(),
        path: `/${newName.trim()}`
      }

      if (currentProject) {
        const updatedFiles = currentProject.files.map(f =>
          f.id === file.id ? updatedFile : f
        )

        const updatedProject = {
          ...currentProject,
          files: updatedFiles
        }

        startTransition(() => {
          setCurrentProject(updatedProject)
          if (activeFile?.id === file.id) {
            setActiveFile(updatedFile)
          }
          setOpenFiles(prev =>
            prev.map(f => f.id === file.id ? updatedFile : f)
          )
          setNotification({ type: 'success', message: `Renamed to ${newName}` })
        })
      }
    }
    setTimeout(() => setNotification(null), 3000)
  }, [currentProject, activeFile?.id])

  // Auto-save functionality
  useEffect(() => {
    if (!activeFile || !activeFile.modified) return

    const autoSaveInterval = setInterval(() => {
      if (activeFile.modified && !isSaving) {
        // Auto-save every 30 seconds for modified files
        saveFile()
      }
    }, 30000) // 30 seconds

    return () => clearInterval(autoSaveInterval)
  }, [activeFile, isSaving, saveFile])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 's':
            event.preventDefault()
            saveFile()
            break
          case 'Enter':
            if (event.shiftKey) {
              event.preventDefault()
              runCode()
            }
            break
          case 'n':
            event.preventDefault()
            createNewFile()
            break
          case 'o':
            event.preventDefault()
            openFolder()
            break
          case '`':
            event.preventDefault()
            setShowTerminal(!showTerminal)
            break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [saveFile, runCode, createNewFile, openFolder, showTerminal])

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

      {/* Hidden file input for folder opening */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".py,.js,.ts,.tsx,.jsx,.html,.css,.json,.md,.txt,.sql"
        className="hidden"
        onChange={handleFileInput}
      />

      {/* Notification System */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 p-3 rounded-md shadow-lg transition-all duration-300 ${
          notification.type === 'success'
            ? 'bg-green-500 text-white'
            : 'bg-red-500 text-white'
        }`}>
          <div className="flex items-center space-x-2">
            {notification.type === 'success' ? (
              <div className="w-2 h-2 bg-white rounded-full"></div>
            ) : (
              <div className="w-2 h-2 bg-white rounded-full"></div>
            )}
            <span className="text-sm font-medium">{notification.message}</span>
          </div>
        </div>
      )}

      {/* Click outside to close mobile menu */}
      {isMobile && showMobileMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowMobileMenu(false)}
        />
      )}

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
                    <div className="flex items-center space-x-1">
                      {/* Right-click context menu for file tabs */}
                      <button
                        className="opacity-60 hover:opacity-100 transition-opacity p-1 rounded"
                        onClick={(e) => {
                          e.stopPropagation()
                          // Simple context menu
                          const action = window.confirm('Choose action:\nOK = Duplicate\nCancel = Rename')
                          if (action) {
                            duplicateFile(file)
                          } else {
                            renameFile(file)
                          }
                        }}
                        title="Right-click options"
                      >
                        <MoreHorizontal className="h-3 w-3" />
                      </button>
                      <button
                        className="opacity-60 hover:opacity-100 transition-opacity"
                        onClick={(e) => {
                          e.stopPropagation()
                          closeFile(file.id)
                        }}
                        title="Close file"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
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
            disabled={!activeFile || isSaving}
            className={`ide-button-secondary ${isMobile ? 'px-2' : ''}`}
            title={`Save file (${isMobile ? '' : 'Ctrl+S'})`}
          >
            {isSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            {!isMobile && <span className="ml-2">{isSaving ? 'Saving...' : 'Save'}</span>}
          </Button>
          
          <Button
            size="sm"
            onClick={runCode}
            disabled={!activeFile || isRunning}
            className={`ide-button-primary ${isMobile ? 'px-2' : ''}`}
            title={`Run code (${isMobile ? '' : 'Ctrl+Shift+Enter'})`}
          >
            {isRunning ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {!isMobile && <span className="ml-2">{isRunning ? 'Running...' : 'Run'}</span>}
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
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleMobileMenu}
                className="ide-button-ghost px-2"
                title="More options"
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>

              {/* Mobile Menu Dropdown */}
              {showMobileMenu && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-card border border-border rounded-md shadow-lg z-50">
                  <div className="py-1">
                    <button
                      className="w-full text-left px-3 py-2 text-sm hover:bg-muted flex items-center space-x-2"
                      onClick={() => {
                        createNewFile()
                        setShowMobileMenu(false)
                      }}
                    >
                      <FileText className="h-4 w-4" />
                      <span>New File</span>
                    </button>
                    <button
                      className="w-full text-left px-3 py-2 text-sm hover:bg-muted flex items-center space-x-2"
                      onClick={() => {
                        openFolder()
                        setShowMobileMenu(false)
                      }}
                    >
                      <Folder className="h-4 w-4" />
                      <span>Open Folder</span>
                    </button>
                    <button
                      className="w-full text-left px-3 py-2 text-sm hover:bg-muted flex items-center space-x-2"
                      onClick={() => {
                        setShowTerminal(!showTerminal)
                        setShowMobileMenu(false)
                      }}
                    >
                      <Terminal className="h-4 w-4" />
                      <span>{showTerminal ? 'Hide Terminal' : 'Show Terminal'}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
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
            <OptimizedProjectExplorer
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
                      options={{
                        ...editorOptions
                      }}
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
                        <Button
                          size="sm"
                          onClick={createNewFile}
                          disabled={isCreatingFile}
                          className="ide-button-primary"
                          title="Create new file (Ctrl+N)"
                        >
                          <FileText className="h-4 w-4 mr-2" />
                          {isCreatingFile ? 'Creating...' : 'New File'}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={openFolder}
                          className="ide-button-secondary"
                          title="Open folder (Ctrl+O)"
                        >
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
                <OptimizedTerminalPanel onClose={handleCloseTerminal} />
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
            <OptimizedAIAssistantPanel
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