'use client'

import React, { useState, useEffect, useRef, useCallback, useMemo, startTransition } from 'react'
import '@/styles/ide-animations.css'
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
  Plus,
  Edit3,
  Check,
  X
} from 'lucide-react'
import Editor from '@monaco-editor/react'
import { ProjectExplorer } from './ProjectExplorer'
import type { ProjectFile as ExplorerFile, Project as ExplorerProject } from './ProjectExplorer'
import { AIAssistantPanel } from './AIAssistantPanel'
import { TerminalPanel } from './TerminalPanel'
import { useAICodeStore } from '@/lib/stores/ai-code-store'
import type { CodeGenerationResponse } from '@/lib/stores/ai-code-store'
import { useAICodeOperationStates } from '@/lib/stores/ai-code-store'
import { useTheme } from 'next-themes'
import { CommandPalette } from './CommandPalette'
import { StatusBar } from './StatusBar'
import { fileManagementApi, type ProjectInfo as BackendProject, type FileInfo as BackendFile } from '@/lib/api/file-management-api'

export type EditorMode = 'traditional' | 'ai-assisted' | 'ai-first'

type IDEFile = ExplorerFile

type AIChangeOperation = 'generate' | 'optimize' | 'debug' | 'test'

const stripMarkdownCodeFences = (value: string): string => {
  if (!value) return ''
  const trimmed = value.trim()
  if (!trimmed.startsWith('```')) {
    return value
  }

  const lines = trimmed.split('\n')
  // remove opening fence
  lines.shift()
  // remove closing fence(s)
  while (lines.length && lines[lines.length - 1].trim().startsWith('```')) {
    lines.pop()
  }
  return lines.join('\n')
}

interface PendingChange {
  id: string
  fileId: string
  fileName: string
  operation: AIChangeOperation
  prevContent: string
  newContent: string
  metadata?: {
    prompt?: string
    notes?: string
    rawCode?: string
    explanation?: string
  }
  timestamp: number
}

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
  const [isMobile, setIsMobile] = useState(false)
  const [notification, setNotification] = useState<{type: 'success' | 'error', message: string} | null>(null)
  const [isEditingProjectName, setIsEditingProjectName] = useState(false)
  const [editingProjectName, setEditingProjectName] = useState('')
  const [pendingChange, setPendingChange] = useState<PendingChange | null>(null)

  const editorRef = useRef<any>(null)
  const resizeTimeoutRef = useRef<NodeJS.Timeout>()
  const changeTimeoutRef = useRef<NodeJS.Timeout>()
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

  // Mobile detection with optimized debouncing
  useEffect(() => {
    const checkScreenSize = () => {
      if (resizeTimeoutRef.current) clearTimeout(resizeTimeoutRef.current)

      resizeTimeoutRef.current = setTimeout(() => {
        const mobile = window.innerWidth < 768

        startTransition(() => {
          setIsMobile(prevMobile => {
            if (prevMobile !== mobile) {
              if (mobile) {
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

  // Initialize project
  useEffect(() => {
    if (projectId) {
      loadProject(projectId)
    } else {
      // Create or load default project from backend
      createOrLoadDefaultProject()
    }
  }, [projectId, editorMode])

  const createOrLoadDefaultProject = async () => {
    try {
      setIsLoading(true)
      
      // Try to get existing projects first
      const existingProjects = await fileManagementApi.listProjects()
      
      if (existingProjects.length > 0) {
        // Load the first existing project
        const firstProject = existingProjects[0]
        await loadProject(firstProject.id)
      } else {
        // Create a new default project
        const newProject = await fileManagementApi.createProjectFromTemplate(
          'Trading Strategy',
          'trading',
          'AI-powered trading strategy development'
        )
        await loadProject(newProject.id)
      }
    } catch (error) {
      console.error('Failed to create or load default project:', error)
      
      // Fall back to client-side default project if backend fails
      const defaultProject: Project = {
        id: 'default',
        name: 'Trading Strategy (Offline)',
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
      
      setNotification({ 
        type: 'error', 
        message: 'Failed to connect to backend. Working offline.' 
      })
      setTimeout(() => setNotification(null), 5000)
    } finally {
      setIsLoading(false)
    }
  }

  const loadProject = async (id: string) => {
    try {
      setIsLoading(true)
      // Load project from backend API
      const backendProject = await fileManagementApi.loadProject(id, true)
      
      // Convert backend format to frontend format
      const project: Project = {
        id: backendProject.id,
        name: backendProject.name,
        description: backendProject.description || 'AI-powered trading strategy development',
        files: backendProject.files.map((file): IDEFile => ({
          id: file.id,
          name: file.name,
          path: file.path,
          content: file.content || '',
          language: file.language,
          modified: false,
          isActive: false
        })),
        settings: {
          aiEnabled: backendProject.settings.aiEnabled ?? true,
          suggestions: backendProject.settings.suggestions ?? true,
          autoComplete: backendProject.settings.autoComplete ?? true,
          errorDetection: backendProject.settings.errorDetection ?? true,
          testGeneration: backendProject.settings.testGeneration ?? true
        }
      }
      
      setCurrentProject(project)
      if (project.files.length > 0) {
        const mainFile = project.files.find(f => f.name === 'main.py') || project.files[0]
        setActiveFile({ ...mainFile, isActive: true })
        setOpenFiles([{ ...mainFile, isActive: true }])
      }
      
      setNotification({ type: 'success', message: `Loaded project: ${project.name}` })
      
    } catch (error) {
      console.error('Failed to load project:', error)
      setNotification({ type: 'error', message: `Failed to load project: ${error instanceof Error ? error.message : 'Unknown error'}` })
    } finally {
      setIsLoading(false)
      setTimeout(() => setNotification(null), 3000)
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

  const handleEditorChange = useCallback((value: string | undefined) => {
    if (!activeFile || value === undefined || value === activeFile.content) return

    if (changeTimeoutRef.current) clearTimeout(changeTimeoutRef.current)

    changeTimeoutRef.current = setTimeout(() => {
      const updatedFile: IDEFile = {
        ...activeFile,
        content: value,
        modified: activeFile.content !== value
      }

      startTransition(() => {
        setActiveFile(updatedFile)
        updateFileContent(updatedFile)
      })
    }, 100)
  }, [activeFile])

  const openFile = useCallback((file: ExplorerFile) => {
    // Check if file is already open to avoid duplicates
    const existingFile = openFiles.find(f => f.id === file.id)

    if (existingFile) {
      // Use existing file object to maintain React key consistency
      setActiveFile(existingFile)
    } else {
      // Convert ProjectFile to IDEFile, ensuring modified is always boolean
      const normalized: IDEFile = { ...file, modified: !!file.modified }

      startTransition(() => {
        setActiveFile(normalized)
        setOpenFiles(prev => [...prev, normalized])
      })
    }

    if (isMobile) setShowAIPanel(false)
  }, [isMobile, openFiles])

  const closeFile = useCallback((fileId: string) => {
    const fileToClose = openFiles.find(f => f.id === fileId)

    if (fileToClose?.modified) {
      const shouldSave = window.confirm(
        `${fileToClose.name} has unsaved changes. Do you want to save before closing?`
      )

      if (shouldSave && activeFile?.id === fileId) {
        saveFile().then(() => {
          performCloseFile(fileId)
        })
        return
      }
    }

    performCloseFile(fileId)
  }, [openFiles, activeFile?.id])

  const performCloseFile = useCallback((fileId: string) => {
    const newOpenFiles = openFiles.filter(f => f.id !== fileId)

    startTransition(() => {
      setOpenFiles(newOpenFiles)
      if (activeFile?.id === fileId) {
        setActiveFile(newOpenFiles.length > 0 ? newOpenFiles[0] : null)
      }
    })
  }, [openFiles, activeFile?.id])

  const saveFile = useCallback(async () => {
    if (!activeFile || !currentProject) return

    try {
      // Save file using backend API
      const savedFile = await fileManagementApi.saveFile(
        currentProject.id,
        activeFile.name,
        activeFile.content,
        activeFile.language
      )

      const updatedFile: IDEFile = { 
        ...activeFile, 
        modified: false,
        // Update with backend response data
        content: savedFile.content || activeFile.content
      }

      // Call onSave callback if provided
      if (onSave) {
        await onSave(updatedFile)
      }

      startTransition(() => {
        setActiveFile(updatedFile)
        updateFileContent(updatedFile)
        setNotification({ type: 'success', message: `${activeFile.name} saved successfully` })
      })
    } catch (error) {
      console.error('Failed to save file:', error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      setNotification({ type: 'error', message: `Failed to save ${activeFile.name}: ${errorMessage}` })
    } finally {
      // Clear notification after 3 seconds
      setTimeout(() => setNotification(null), 3000)
    }
  }, [activeFile, currentProject, onSave])

  const runCode = useCallback(async () => {
    if (!activeFile) return

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
      // Clear notification after 3 seconds
      setTimeout(() => setNotification(null), 3000)
    }
  }, [activeFile, onRun])

  const handleAIGenerate = async (prompt: string): Promise<CodeGenerationResponse | void> => {
    if (!activeFile) return
    
    const currentContent = editorRef.current?.getValue?.() ?? activeFile.content ?? ''
    const combinedPrompt = [
      prompt.trim(),
      '',
      `Current contents of ${activeFile.name}:`,
      '```' + (activeFile.language || ''),
      currentContent,
      '```',
      '',
      `Please return the full updated contents of ${activeFile.name} as plain code (no markdown fences).`
    ].join('\n')

    try {
      const result = await generateCode({
        prompt: combinedPrompt,
        context: currentContent,
        language: activeFile.language,
        complexity_level: 'intermediate',
        include_comments: true
      })
      
      if (result.code) {
        applyAIChange({
          newContent: result.code,
          prevContent: currentContent,
          operation: 'generate',
          metadata: { 
            prompt,
            rawCode: result.code,
            explanation: result.explanation
          }
        })
      }

      return result
    } catch (error) {
      console.error('AI generation failed:', error)
      setNotification({ type: 'error', message: 'AI generation failed' })
      setTimeout(() => setNotification(null), 3000)
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
        const currentContent = editorRef.current?.getValue?.() || activeFile.content || ''
        applyAIChange({
          newContent: result.optimized_code,
          prevContent: currentContent,
          operation: 'optimize',
          metadata: { notes: 'Performance optimization', rawCode: result.optimized_code }
        })
      }
    } catch (error) {
      console.error('AI optimization failed:', error)
      setNotification({ type: 'error', message: 'AI optimization failed' })
      setTimeout(() => setNotification(null), 3000)
    }
  }

  // Sync Monaco theme with app theme (black-gold accent preserved)
  useEffect(() => {
    setEditorTheme(resolvedTheme === 'dark' ? 'alphintra-dark' : 'alphintra-light')
  }, [resolvedTheme])

  // New file creation
  const createNewFile = useCallback(async () => {
    if (!currentProject) {
      setNotification({ type: 'error', message: 'No project selected' })
      setTimeout(() => setNotification(null), 3000)
      return
    }

    const fileName = prompt('Enter file name (with extension):', 'untitled.py')

    if (fileName && fileName.trim()) {
      try {
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

        // Create file using backend API
        const createdFile = await fileManagementApi.createFile(currentProject.id, {
          name: fileName.trim(),
          content: getTemplateContent(fileExtension),
          language: languageMap[fileExtension] || 'plaintext'
        })

        const newFile: IDEFile = {
          id: createdFile.id,
          name: createdFile.name,
          path: createdFile.path,
          content: createdFile.content || '',
          language: createdFile.language,
          modified: false
        }

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
      } catch (error) {
        console.error('Failed to create file:', error)
        const errorMessage = error instanceof Error ? error.message : 'Unknown error'
        setNotification({ type: 'error', message: `Failed to create ${fileName}: ${errorMessage}` })
      }
    }

    setTimeout(() => setNotification(null), 3000)
  }, [currentProject])

  const applyAIChange = useCallback((
    change: {
      newContent: string
      prevContent: string
      operation: AIChangeOperation
      metadata?: PendingChange['metadata']
    }
  ) => {
    if (!activeFile) return

    const editorInstance = editorRef.current
    const sanitizedContent = stripMarkdownCodeFences(change.newContent)

    if (sanitizedContent === change.prevContent) {
      setNotification({
        type: 'error',
        message: 'AI did not provide any changes to apply.'
      })
      setTimeout(() => setNotification(null), 3000)
      return
    }

    if (editorInstance?.setValue) {
      editorInstance.setValue(sanitizedContent)
    }

    handleEditorChange(sanitizedContent)

    setPendingChange({
      id: `${Date.now()}`,
      fileId: activeFile.id,
      fileName: activeFile.name,
      operation: change.operation,
      prevContent: change.prevContent,
      newContent: sanitizedContent,
      metadata: change.metadata,
      timestamp: Date.now()
    })

    setNotification({
      type: 'success',
      message: `AI ${change.operation} applied to ${activeFile.name}`
    })
    setTimeout(() => setNotification(null), 3000)
  }, [activeFile, handleEditorChange])

  // Global keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase()
      if ((e.metaKey || e.ctrlKey) && key === 's') {
        e.preventDefault()
        saveFile()
      } else if ((e.metaKey || e.ctrlKey) && key === 'n') {
        e.preventDefault()
        createNewFile()
      } else if ((e.metaKey || e.ctrlKey) && key === 'enter') {
        e.preventDefault()
        runCode()
      } else if ((e.metaKey || e.ctrlKey) && e.shiftKey && key === 'p') {
        e.preventDefault()
        setShowCommandPalette(true)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [saveFile, createNewFile, runCode])

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

  // Project name editing
  const startEditingProjectName = useCallback(() => {
    setEditingProjectName(currentProject?.name || '')
    setIsEditingProjectName(true)
  }, [currentProject?.name])

  const saveProjectName = useCallback(() => {
    if (!currentProject || !editingProjectName.trim()) {
      setIsEditingProjectName(false)
      return
    }

    const updatedProject = {
      ...currentProject,
      name: editingProjectName.trim()
    }

    startTransition(() => {
      setCurrentProject(updatedProject)
      setIsEditingProjectName(false)
      setNotification({ type: 'success', message: 'Project name updated' })
    })

    setTimeout(() => setNotification(null), 3000)
  }, [currentProject, editingProjectName])

  const cancelEditingProjectName = useCallback(() => {
    setIsEditingProjectName(false)
    setEditingProjectName('')
  }, [])

  // Command palette commands
  // Auto-save functionality
  useEffect(() => {
    if (!activeFile || !activeFile.modified) return

    const autoSaveInterval = setInterval(() => {
      if (activeFile.modified) {
        // Auto-save every 30 seconds for modified files
        saveFile()
      }
    }, 30000) // 30 seconds

    return () => clearInterval(autoSaveInterval)
  }, [activeFile, saveFile])

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (resizeTimeoutRef.current) clearTimeout(resizeTimeoutRef.current)
      if (changeTimeoutRef.current) clearTimeout(changeTimeoutRef.current)
    }
  }, [])

  // Enhanced editor options with mobile optimization
  const editorOptions = useMemo(() => ({
    minimap: {
      enabled: minimapEnabled && !isMobile,
      size: 'proportional' as const,
      maxColumn: 120,
      renderCharacters: !isMobile,
      showSlider: 'mouseover' as const
    },
    fontSize: isMobile ? 12 : 14,
    lineNumbers: 'on' as const,
    roundedSelection: false,
    scrollBeyondLastLine: false,
    automaticLayout: true,
    suggestOnTriggerCharacters: currentProject?.settings.suggestions,
    quickSuggestions: currentProject?.settings.autoComplete,
    wordWrap: (wordWrapEnabled ? 'on' : 'off') as 'on' | 'off',
    folding: true,
    bracketMatching: 'always' as const,
    // Performance optimizations
    wordBasedSuggestions: 'off' as const,
    parameterHints: { enabled: true },
    codeLens: false,
    colorDecorators: false,
    renderWhitespace: 'none' as const,
    smoothScrolling: false,
    cursorSmoothCaretAnimation: 'off' as const,
    mouseWheelZoom: false,
    scrollbar: {
      useShadows: !isMobile,
      verticalHasArrows: false,
      horizontalHasArrows: false,
      verticalScrollbarSize: isMobile ? 6 : 8,
      horizontalScrollbarSize: isMobile ? 6 : 8
    }
  }), [minimapEnabled, isMobile, currentProject?.settings.suggestions, currentProject?.settings.autoComplete, wordWrapEnabled])

  const commands = useMemo(() => {
    const list = [
      { id: 'save', title: 'File: Save', shortcut: 'Ctrl/Cmd+S', action: saveFile },
      { id: 'new-file', title: 'File: New File', shortcut: 'Ctrl/Cmd+N', action: createNewFile },
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
  }, [showAIPanel, showTerminal, wordWrapEnabled, minimapEnabled, editorMode, activeFile, saveFile, createNewFile, runCode, formatDocument])

  const handleAIDebug = async (errorMessage?: string) => {
    if (!activeFile) return
    
    try {
      const result = await debugCode({
        code: activeFile.content,
        error_message: errorMessage || '',
        context: 'Trading strategy debugging'
      })
      
      if (result.corrected_code) {
        const currentContent = editorRef.current?.getValue?.() || activeFile.content || ''
        applyAIChange({
          newContent: result.corrected_code,
          prevContent: currentContent,
          operation: 'debug',
          metadata: { notes: errorMessage, rawCode: result.corrected_code }
        })
      }
    } catch (error) {
      console.error('AI debugging failed:', error)
      setNotification({ type: 'error', message: 'AI debugging failed' })
      setTimeout(() => setNotification(null), 3000)
    }
  }

  const undoPendingAIChange = useCallback(() => {
    if (!pendingChange) return

    const previous = pendingChange.prevContent
    if (editorRef.current?.setValue) {
      editorRef.current.setValue(previous)
    }

    handleEditorChange(previous)
    setPendingChange(null)
    setNotification({ type: 'success', message: 'AI changes undone' })
    setTimeout(() => setNotification(null), 3000)
  }, [pendingChange, handleEditorChange])

  const keepPendingAIChange = useCallback(() => {
    if (!pendingChange) return

    setPendingChange(null)
    setNotification({ type: 'success', message: 'AI changes kept' })
    setTimeout(() => setNotification(null), 3000)
  }, [pendingChange])

  useEffect(() => {
    if (!pendingChange || !activeFile) return
    if (pendingChange.fileId !== activeFile.id) return

    const editorContent = editorRef.current?.getValue?.() ?? activeFile.content ?? ''
    if (editorContent === pendingChange.prevContent) {
      setPendingChange(null)
    }
  }, [pendingChange, activeFile])

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
      {/* Notification System */}
      {notification && (
        <div className={`ide-notification fixed top-4 right-4 z-50 p-3 rounded-md shadow-lg transition-all duration-300 ${
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

      {pendingChange && activeFile && pendingChange.fileId === activeFile.id && (
        <div className="fixed bottom-6 right-6 z-50 max-w-sm">
          <Card className="border border-primary/40 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center space-x-2">
                <Bot className="h-4 w-4" />
                <span>AI updated {pendingChange.fileName}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-xs text-muted-foreground">
                Changes from the AI {pendingChange.operation} were applied automatically. Keep them or undo to restore the previous version.
              </p>
              <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={undoPendingAIChange}>
                  Undo
                </Button>
                <Button size="sm" onClick={keepPendingAIChange}>
                  Keep
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Mobile overlays */}
      {isMobile && showAIPanel && (
        <div className="fixed inset-0 z-40 bg-background">
          <div className="h-full flex flex-col">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <h2 className="text-lg font-semibold">AI Assistant</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAIPanel(false)}
              >
                Close
              </Button>
            </div>
            <div className="flex-1">
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
          </div>
        </div>
      )}

      {/* Top Toolbar */}
      <div className="ide-toolbar border-b border-border p-2 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Editable Project Name */}
          <div className="flex items-center space-x-2">
            {isEditingProjectName ? (
              <div className="ide-project-name-edit flex items-center space-x-2">
                <input
                  type="text"
                  value={editingProjectName}
                  onChange={(e) => setEditingProjectName(e.target.value)}
                  onBlur={saveProjectName}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') saveProjectName()
                    if (e.key === 'Escape') cancelEditingProjectName()
                  }}
                  className="bg-transparent border-none outline-none font-semibold text-lg px-2 py-1 rounded"
                  autoFocus
                />
                <Button size="sm" variant="ghost" onClick={saveProjectName}>
                  <Check className="h-3 w-3" />
                </Button>
                <Button size="sm" variant="ghost" onClick={cancelEditingProjectName}>
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ) : (
              <h1
                className={`ide-project-name font-semibold cursor-pointer px-2 py-1 rounded transition-all duration-300 hover:bg-muted ${isMobile ? 'text-base' : 'text-lg'}`}
                onClick={startEditingProjectName}
                title="Click to edit project name"
              >
                {isMobile
                  ? (currentProject?.name || 'IDE').slice(0, 12) + '...'
                  : currentProject?.name || 'Enhanced IDE'
                }
              </h1>
            )}
          </div>

          {/* New File Button */}
          <Button
            size="sm"
            variant="outline"
            onClick={createNewFile}
            className="ide-button-gold"
            title="Create new file (Ctrl/Cmd+N)"
          >
            <Plus className="h-4 w-4" />
            {!isMobile && <span className="ml-1">New File</span>}
          </Button>
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
          
          {/* File tabs with mobile optimization */}
          {!isMobile && (
            <div className="flex items-center space-x-1 overflow-x-auto">
              {openFiles.map((file: IDEFile, index: number) => (
                <div
                  key={file.id || index}
                  className={`ide-file-tab flex items-center space-x-2 px-3 py-1 rounded-t-md border-b-2 cursor-pointer whitespace-nowrap ${
                    file.id === activeFile?.id
                      ? 'bg-background border-primary active'
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
          )}
        </div>
        
        <div className={`flex items-center ${isMobile ? 'space-x-1' : 'space-x-2'}`}>
          {(isGenerating || isExplaining || isOptimizing || isDebugging) && (
            <div className="hidden sm:flex items-center text-xs text-muted-foreground mr-2 ide-loading">
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary mr-2"></div>
              AI active
            </div>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={saveFile}
            className="ide-button-gold"
            title="Save file (Ctrl/Cmd+S)"
          >
            <Save className="h-4 w-4" />
            {!isMobile && <span className="ml-1">Save</span>}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={runCode}
            className="ide-button-gold"
            title="Run code (Ctrl/Cmd+Enter)"
          >
            <Play className="h-4 w-4" />
            {!isMobile && <span className="ml-1">Run</span>}
          </Button>
          {!isMobile && (
            <Button
              variant="outline"
              size="sm"
              onClick={formatDocument}
              className="ide-button-gold"
              title="Format document"
            >
              <Code className="h-4 w-4 mr-1" />
              Format
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAIPanel(!showAIPanel)}
            className="ide-button-gold"
            title="Toggle AI Assistant"
          >
            <Bot className="h-4 w-4" />
            {!isMobile && <span className="ml-1">AI Assistant</span>}
          </Button>
          {!isMobile && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCommandPalette(true)}
              className="ide-button-gold"
              title="Open command palette (Ctrl/Cmd+Shift+P)"
            >
              <Search className="h-4 w-4 mr-1" />
              Commands
            </Button>
          )}
        </div>
      </div>
      
      {/* Main Content */}
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* Left Panel - Project Explorer */}
        {!isMobile && (
          <>
            <ResizablePanel defaultSize={20} minSize={15}>
              <div className="h-full border-r border-border ide-panel-left">
                <ProjectExplorer
                  project={currentProject}
                  onFileSelect={openFile}
                  activeFile={activeFile}
                />
              </div>
            </ResizablePanel>

            <ResizableHandle />
          </>
        )}

        {/* Center Panel - Code Editor */}
        <ResizablePanel defaultSize={isMobile ? 100 : (showAIPanel ? 55 : 75)}>
          <ResizablePanelGroup direction="vertical">
            <ResizablePanel defaultSize={showTerminal ? 70 : 100}>
              <div className="h-full ide-editor-container">
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
                    options={editorOptions}
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
                  <div className="ide-terminal">
                    <TerminalPanel onClose={() => setShowTerminal(false)} />
                  </div>
                </ResizablePanel>
              </>
            )}
          </ResizablePanelGroup>
        </ResizablePanel>
        
        {/* Right Panel - AI Assistant */}
        {showAIPanel && !isMobile && (
          <>
            <ResizableHandle />
            <ResizablePanel defaultSize={25} minSize={20}>
              <div className="h-full border-l border-border ide-panel-right ide-ai-panel">
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
      <div className="border-t border-border ide-status-bar">
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
