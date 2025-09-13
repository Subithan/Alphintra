'use client'

import React, { useState, useMemo, useCallback, memo, startTransition } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import {
  Folder,
  FolderOpen,
  FileText,
  Search,
  Plus,
  ChevronRight,
  ChevronDown,
  Code,
  Settings,
  Package,
  Filter,
  X
} from 'lucide-react'

// Simplified types for performance
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
  files: ProjectFile[]
  folders: ProjectFolder[]
  isExpanded?: boolean
}

interface Project {
  id: string
  name: string
  files: ProjectFile[]
  folders?: ProjectFolder[]
}

interface ProjectExplorerProps {
  project: Project | null
  onFileSelect: (file: ProjectFile) => void
  activeFile: ProjectFile | null
}

// Memoized file icon component
const FileIcon = memo(({ fileName, language }: { fileName: string, language: string }) => {
  const getIcon = useMemo(() => {
    const ext = fileName.split('.').pop()?.toLowerCase()

    const iconMap: Record<string, JSX.Element> = {
      'py': <Code className="h-4 w-4 text-blue-500" />,
      'js': <Code className="h-4 w-4 text-yellow-500" />,
      'ts': <Code className="h-4 w-4 text-blue-600" />,
      'tsx': <Code className="h-4 w-4 text-blue-600" />,
      'jsx': <Code className="h-4 w-4 text-yellow-500" />,
      'html': <Code className="h-4 w-4 text-orange-500" />,
      'css': <Code className="h-4 w-4 text-blue-400" />,
      'json': <Settings className="h-4 w-4 text-green-500" />,
      'md': <FileText className="h-4 w-4 text-gray-500" />,
      'txt': <FileText className="h-4 w-4 text-gray-400" />
    }

    return iconMap[ext || ''] || <FileText className="h-4 w-4 text-gray-500" />
  }, [fileName])

  return getIcon
})

FileIcon.displayName = 'FileIcon'

// Memoized file item component
const FileItem = memo(({
  file,
  isActive,
  onSelect
}: {
  file: ProjectFile
  isActive: boolean
  onSelect: (file: ProjectFile) => void
}) => {
  const handleClick = useCallback(() => {
    onSelect(file)
  }, [file, onSelect])

  return (
    <div
      className={`group flex items-center space-x-2 px-3 py-2 rounded-md cursor-pointer transition-colors ${
        isActive
          ? 'bg-primary text-primary-foreground'
          : 'hover:bg-muted/50'
      }`}
      onClick={handleClick}
    >
      <FileIcon fileName={file.name} language={file.language} />
      <span className="text-sm flex-1 min-w-0 truncate">{file.name}</span>
      {file.modified && (
        <div className="w-2 h-2 bg-orange-500 rounded-full flex-shrink-0" />
      )}
    </div>
  )
})

FileItem.displayName = 'FileItem'

// Virtualized file list for performance
const VirtualizedFileList = memo(({
  files,
  activeFile,
  onFileSelect,
  searchTerm
}: {
  files: ProjectFile[]
  activeFile: ProjectFile | null
  onFileSelect: (file: ProjectFile) => void
  searchTerm: string
}) => {
  // Filter files based on search term
  const filteredFiles = useMemo(() => {
    if (!searchTerm) return files

    return files.filter(file =>
      file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      file.path.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [files, searchTerm])

  // Only render visible files for performance
  const visibleFiles = useMemo(() => {
    // Limit to first 100 files for performance
    return filteredFiles.slice(0, 100)
  }, [filteredFiles])

  return (
    <div className="space-y-1">
      {visibleFiles.map((file) => (
        <FileItem
          key={file.id}
          file={file}
          isActive={activeFile?.id === file.id}
          onSelect={onFileSelect}
        />
      ))}
      {filteredFiles.length > 100 && (
        <div className="px-3 py-2 text-xs text-muted-foreground">
          Showing 100 of {filteredFiles.length} files
        </div>
      )}
    </div>
  )
})

VirtualizedFileList.displayName = 'VirtualizedFileList'

// Main component
export const OptimizedProjectExplorer = memo(({
  project,
  onFileSelect,
  activeFile
}: ProjectExplorerProps) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [showSearch, setShowSearch] = useState(false)

  // Memoized file statistics
  const fileStats = useMemo(() => {
    if (!project?.files) return { total: 0, modified: 0 }

    return {
      total: project.files.length,
      modified: project.files.filter(f => f.modified).length
    }
  }, [project?.files])

  // Optimized search handlers
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    startTransition(() => {
      setSearchTerm(value)
    })
  }, [])

  const clearSearch = useCallback(() => {
    startTransition(() => {
      setSearchTerm('')
      setShowSearch(false)
    })
  }, [])

  const toggleSearch = useCallback(() => {
    setShowSearch(prev => !prev)
    if (showSearch) {
      setSearchTerm('')
    }
  }, [showSearch])

  if (!project) {
    return (
      <div className="h-full flex flex-col bg-card">
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-semibold text-muted-foreground">No Project</h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-2">
            <Package className="h-12 w-12 mx-auto text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No project loaded</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-card">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold truncate">{project.name}</h2>
          <div className="flex items-center space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleSearch}
              className="h-8 w-8 p-0"
            >
              {showSearch ? <X className="h-4 w-4" /> : <Search className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        {/* File Stats */}
        <div className="flex items-center space-x-4 text-xs text-muted-foreground">
          <span>{fileStats.total} files</span>
          {fileStats.modified > 0 && (
            <Badge variant="secondary" className="h-5 text-xs">
              {fileStats.modified} modified
            </Badge>
          )}
        </div>

        {/* Search Input */}
        {showSearch && (
          <div className="mt-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={searchTerm}
                onChange={handleSearchChange}
                placeholder="Search files..."
                className="pl-9 pr-9 h-8"
                autoFocus
              />
              {searchTerm && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearSearch}
                  className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* File List */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {project.files && project.files.length > 0 ? (
            <VirtualizedFileList
              files={project.files}
              activeFile={activeFile}
              onFileSelect={onFileSelect}
              searchTerm={searchTerm}
            />
          ) : (
            <div className="flex items-center justify-center py-8">
              <div className="text-center space-y-2">
                <FileText className="h-8 w-8 mx-auto text-muted-foreground" />
                <p className="text-sm text-muted-foreground">No files in project</p>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Quick Actions */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" className="flex-1">
            <Plus className="h-4 w-4 mr-2" />
            New File
          </Button>
          <Button variant="outline" size="sm" className="flex-1">
            <Folder className="h-4 w-4 mr-2" />
            New Folder
          </Button>
        </div>
      </div>
    </div>
  )
})

OptimizedProjectExplorer.displayName = 'OptimizedProjectExplorer'