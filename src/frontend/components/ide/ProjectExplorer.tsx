'use client'

import React, { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { 
  Folder, 
  FolderOpen, 
  File, 
  FileText, 
  Search, 
  Plus, 
  MoreHorizontal,
  ChevronRight,
  ChevronDown,
  Code,
  Database,
  Settings,
  Package,
  GitBranch,
  Filter,
  SortAsc,
  Eye,
  EyeOff,
  FolderPlus,
  FilePlus,
  Trash2,
  Copy,
  Scissors,
  RefreshCw,
  Download,
  Upload
} from 'lucide-react'

interface ProjectFile {
  id: string
  name: string
  path: string
  content: string
  language: string
  modified?: boolean
  isActive?: boolean
}

interface ProjectFolder {
  id: string
  name: string
  path: string
  expanded?: boolean
  files: ProjectFile[]
  folders: ProjectFolder[]
}

interface Project {
  id: string
  name: string
  description: string
  files: ProjectFile[]
  settings?: any
}

interface ProjectExplorerProps {
  project: Project | null
  onFileSelect: (file: ProjectFile) => void
  activeFile: ProjectFile | null
}

export function ProjectExplorer({ project, onFileSelect, activeFile }: ProjectExplorerProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['/']))

  // Transform flat file list into folder structure
  const folderStructure = useMemo(() => {
    if (!project?.files) return { files: [], folders: [] }

    const structure: { files: ProjectFile[], folders: Map<string, ProjectFolder> } = {
      files: [],
      folders: new Map()
    }

    project.files.forEach(file => {
      const pathParts = file.path.split('/')
      const fileName = pathParts[pathParts.length - 1]
      const folderPath = pathParts.slice(0, -1).join('/') || '/'

      if (folderPath === '/' || folderPath === '') {
        // Root level file
        structure.files.push(file)
      } else {
        // File in a folder - create folder structure if needed
        if (!structure.folders.has(folderPath)) {
          structure.folders.set(folderPath, {
            id: folderPath,
            name: pathParts[pathParts.length - 2] || folderPath,
            path: folderPath,
            expanded: expandedFolders.has(folderPath),
            files: [],
            folders: []
          })
        }
        structure.folders.get(folderPath)!.files.push(file)
      }
    })

    return {
      files: structure.files,
      folders: Array.from(structure.folders.values())
    }
  }, [project?.files, expandedFolders])

  // Filter files based on search term
  const filteredFiles = useMemo(() => {
    if (!searchTerm) return folderStructure.files
    return folderStructure.files.filter(file =>
      file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      file.path.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [folderStructure.files, searchTerm])

  const toggleFolder = (folderPath: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev)
      if (newSet.has(folderPath)) {
        newSet.delete(folderPath)
      } else {
        newSet.add(folderPath)
      }
      return newSet
    })
  }

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
      case 'yml':
      case 'yaml':
        return <Settings className="h-4 w-4 file-icon-yaml" />
      case 'css':
      case 'scss':
      case 'sass':
        return <Code className="h-4 w-4 file-icon-css" />
      case 'html':
      case 'htm':
        return <Code className="h-4 w-4 file-icon-html" />
      case 'sql':
        return <Database className="h-4 w-4 file-icon-json" />
      case 'txt':
      case 'log':
        return <FileText className="h-4 w-4 file-icon-default" />
      default:
        return <File className="h-4 w-4 file-icon-default" />
    }
  }

  const createNewFile = () => {
    // In a real implementation, this would open a dialog to create a new file
    console.log('Create new file')
  }

  const ProjectFileItem = ({ file }: { file: ProjectFile }) => (
    <div
      className={`ide-tree-item ${
        activeFile?.id === file.id ? 'ide-tree-item-active' : ''
      }`}
      onClick={() => onFileSelect(file)}
    >
      {getFileIcon(file.name, file.language)}
      <span className="text-sm flex-1 truncate font-medium">{file.name}</span>
      <div className="flex items-center space-x-1">
        {file.modified && (
          <div className="w-2 h-2 bg-ide-warning rounded-full flex-shrink-0" />
        )}
        <Button variant="ghost" size="sm" className="h-5 w-5 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
          <MoreHorizontal className="h-3 w-3" />
        </Button>
      </div>
    </div>
  )

  const ProjectFolderItem = ({ folder }: { folder: ProjectFolder }) => {
    const isExpanded = expandedFolders.has(folder.path)
    
    return (
      <div className="group">
        <div
          className="ide-tree-item"
          onClick={() => toggleFolder(folder.path)}
        >
          {isExpanded ? (
            <ChevronDown className="h-3 w-3 text-ide-text-muted" />
          ) : (
            <ChevronRight className="h-3 w-3 text-ide-text-muted" />
          )}
          {isExpanded ? (
            <FolderOpen className="h-4 w-4 text-ide-accent" />
          ) : (
            <Folder className="h-4 w-4 text-ide-accent" />
          )}
          <span className="text-sm flex-1 font-medium">{folder.name}</span>
          <div className="flex items-center space-x-1">
            <Badge variant="outline" className="text-xs px-1 py-0 h-4 opacity-60">
              {folder.files.length + folder.folders.length}
            </Badge>
            <Button variant="ghost" size="sm" className="h-5 w-5 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
              <MoreHorizontal className="h-3 w-3" />
            </Button>
          </div>
        </div>
        {isExpanded && (
          <div className="ml-4 border-l border-ide-border pl-2 space-y-0.5">
            {folder.folders.map(subFolder => (
              <ProjectFolderItem key={subFolder.id} folder={subFolder} />
            ))}
            {folder.files.map(file => (
              <ProjectFileItem key={file.id} file={file} />
            ))}
          </div>
        )}
      </div>
    )
  }

  if (!project) {
    return (
      <div className="h-full flex items-center justify-center bg-ide-surface">
        <div className="text-center space-y-4 p-8">
          <div className="mx-auto w-16 h-16 rounded-full bg-ide-background flex items-center justify-center">
            <Folder className="h-8 w-8 text-ide-accent" />
          </div>
          <div>
            <h3 className="text-lg font-medium text-ide-text mb-2">No Project Loaded</h3>
            <p className="text-sm text-ide-text-muted max-w-xs">
              Open an existing project or create a new one to start developing your trading strategies.
            </p>
          </div>
          <div className="flex flex-col space-y-2">
            <Button size="sm" className="ide-button-primary">
              <FolderPlus className="h-4 w-4 mr-2" />
              New Project
            </Button>
            <Button size="sm" variant="outline" className="ide-button-secondary">
              <Folder className="h-4 w-4 mr-2" />
              Open Project
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-ide-surface">
      {/* Enhanced Header */}
      <div className="p-4 border-b border-ide-border">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Folder className="h-5 w-5 text-ide-accent" />
            <span className="font-semibold text-ide-text">{project.name}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 ide-button-ghost" title="New File">
              <FilePlus className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 ide-button-ghost" title="New Folder">
              <FolderPlus className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 ide-button-ghost" title="Refresh">
              <RefreshCw className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 ide-button-ghost" title="More Actions">
              <MoreHorizontal className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* Enhanced Search */}
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-3 w-3 text-ide-text-muted" />
          <Input
            placeholder="Search files and folders..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="ide-input pl-8 h-8 text-sm"
          />
          {searchTerm && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="absolute right-1 top-1 h-6 w-6 p-0"
              onClick={() => setSearchTerm('')}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>

      {/* File Tree */}
      <ScrollArea className="flex-1 px-2">
        <div className="py-2 space-y-0.5">
          {searchTerm ? (
            // Enhanced search results
            <div className="space-y-1">
              <div className="text-xs text-ide-text-muted px-2 py-1 font-medium">
                Search Results ({filteredFiles.length})
              </div>
              {filteredFiles.map(file => (
                <ProjectFileItem key={file.id} file={file} />
              ))}
              {filteredFiles.length === 0 && (
                <div className="text-center py-8 text-ide-text-muted">
                  <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No files found</p>
                  <p className="text-xs">Try adjusting your search terms</p>
                </div>
              )}
            </div>
          ) : (
            // Enhanced folder structure
            <div className="space-y-0.5">
              {/* Root level files */}
              {folderStructure.files.map(file => (
                <ProjectFileItem key={file.id} file={file} />
              ))}
              
              {/* Folders */}
              {folderStructure.folders.map(folder => (
                <ProjectFolderItem key={folder.id} folder={folder} />
              ))}
              
              {/* Empty state */}
              {folderStructure.files.length === 0 && folderStructure.folders.length === 0 && (
                <div className="text-center py-8 text-ide-text-muted">
                  <Folder className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No files in project</p>
                  <p className="text-xs">Create your first file to get started</p>
                </div>
              )}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Enhanced Project Info */}
      <div className="p-4 border-t border-ide-border bg-ide-background">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-ide-text-muted">Files:</span>
            <Badge variant="outline" className="text-xs h-5">{project.files.length}</Badge>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-ide-text-muted">Size:</span>
            <span className="text-ide-text-muted">
              {(project.files.reduce((acc, file) => acc + file.content.length, 0) / 1024).toFixed(1)} KB
            </span>
          </div>
          {project.description && (
            <p className="text-xs text-ide-text-muted italic pt-2 border-t border-ide-border">
              {project.description}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}