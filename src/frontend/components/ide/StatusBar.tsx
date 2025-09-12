'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { WrapText, PanelRight, Type } from 'lucide-react'

interface StatusBarProps {
  line: number
  column: number
  language: string
  wordWrapEnabled: boolean
  minimapEnabled: boolean
  themeName: string
  onToggleWrap: () => void
  onToggleMinimap: () => void
  onFormat: () => void
}

export function StatusBar({ line, column, language, wordWrapEnabled, minimapEnabled, onToggleWrap, onToggleMinimap, onFormat, themeName }: StatusBarProps) {
  return (
    <div className="w-full h-8 px-3 flex items-center justify-between bg-muted/40 text-xs">
      <div className="flex items-center gap-3">
        <span>Ln {line}, Col {column}</span>
        <span className="hidden sm:inline-flex items-center gap-1">
          <Type className="h-3 w-3" /> {language}
        </span>
        <span className="hidden md:inline text-muted-foreground">{themeName}</span>
      </div>
      <div className="flex items-center gap-1">
        <Button size="sm" variant="ghost" className="h-6 px-2" onClick={onFormat}>Format</Button>
        <Button size="sm" variant="ghost" className="h-6 px-2" onClick={onToggleWrap}>
          <WrapText className="h-3 w-3 mr-1" /> {wordWrapEnabled ? 'Wrap On' : 'Wrap Off'}
        </Button>
        <Button size="sm" variant="ghost" className="h-6 px-2" onClick={onToggleMinimap}>
          <PanelRight className="h-3 w-3 mr-1" /> {minimapEnabled ? 'Minimap On' : 'Minimap Off'}
        </Button>
      </div>
    </div>
  )
}

