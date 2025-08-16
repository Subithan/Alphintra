'use client'

import React, { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
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
  GitBranch
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
        return <Code className="h-4 w-4 text-blue-500" />
      case 'js':
      case 'ts':
        return <Code className="h-4 w-4 text-yellow-500" />
      case 'json':
        return <Database className="h-4 w-4 text-green-500" />
      case 'md':
        return <FileText className="h-4 w-4 text-gray-500" />
      case 'yml':
      case 'yaml':
        return <Settings className="h-4 w-4 text-red-500" />
      default:
        return <File className="h-4 w-4 text-gray-400" />
    }
  }

  const createNewFile = () => {
    // In a real implementation, this would open a dialog to create a new file
    console.log('Create new file')
  }

  const ProjectFileItem = ({ file }: { file: ProjectFile }) => (
    <div
      className={`flex items-center space-x-2 px-2 py-1.5 hover:bg-accent cursor-pointer rounded-sm ${
        activeFile?.id === file.id ? 'bg-accent' : ''
      }`}
      onClick={() => onFileSelect(file)}
    >
      {getFileIcon(file.name, file.language)}
      <span className="text-sm flex-1 truncate">{file.name}</span>
      {file.modified && (
        <div className="w-2 h-2 bg-orange-500 rounded-full flex-shrink-0" />
      )}
    </div>
  )

  const ProjectFolderItem = ({ folder }: { folder: ProjectFolder }) => {
    const isExpanded = expandedFolders.has(folder.path)
    
    return (
      <div>
        <div
          className="flex items-center space-x-2 px-2 py-1.5 hover:bg-accent cursor-pointer rounded-sm"
          onClick={() => toggleFolder(folder.path)}
        >
          {isExpanded ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronRight className="h-3 w-3" />
          )}
          {isExpanded ? (
            <FolderOpen className="h-4 w-4 text-blue-500" />
          ) : (
            <Folder className="h-4 w-4 text-blue-500" />
          )}
          <span className="text-sm flex-1">{folder.name}</span>
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
            <MoreHorizontal className="h-3 w-3" />
          </Button>
        </div>
        {isExpanded && (
          <div className="ml-4 border-l border-border pl-2">
            {folder.files.map(file => (
              <ProjectFileItem key={file.id} file={file} />
            ))}
            {folder.folders.map(subFolder => (
              <ProjectFolderItem key={subFolder.id} folder={subFolder} />
            ))}
          </div>
        )}
      </div>
    )
  }

  if (!project) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground">
        <div className="text-center">
          <Folder className="h-8 w-8 mx-auto mb-2" />
          <p className="text-sm">No project loaded</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2">
            <Folder className="h-4 w-4" />
            <span>{project.name}</span>
          </div>
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={createNewFile}>
            <Plus className="h-3 w-3" />
          </Button>
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col px-3 py-0">
        {/* Search */}
        <div className="mb-3">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-3 w-3 text-muted-foreground" />
            <Input
              placeholder="Search files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-7 h-8 text-xs"
            />
          </div>
        </div>

        {/* File Tree */}
        <ScrollArea className="flex-1">
          <div className="space-y-0.5">
            {searchTerm ? (
              // Show filtered files when searching
              filteredFiles.map(file => (
                <ProjectFileItem key={file.id} file={file} />
              ))
            ) : (
              // Show folder structure when not searching
              <>
                {/* Root level files */}
                {folderStructure.files.map(file => (
                  <ProjectFileItem key={file.id} file={file} />
                ))}
                
                {/* Folders */}
                {folderStructure.folders.map(folder => (
                  <ProjectFolderItem key={folder.id} folder={folder} />
                ))}
              </>
            )}
          </div>
        </ScrollArea>

        {/* Project Info */}
        <div className="mt-3 pt-3 border-t border-border">
          <div className="text-xs text-muted-foreground space-y-1">
            <div className="flex items-center justify-between">
              <span>Files:</span>
              <span>{project.files.length}</span>
            </div>
            {project.description && (
              <p className="text-xs text-muted-foreground italic">
                {project.description}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </div>
  )
}