'use client'

import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { VisuallyHidden } from '@radix-ui/react-visually-hidden'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Search } from 'lucide-react'

type CommandItemType = {
  id: string
  title: string
  shortcut?: string
  action: () => void
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  commands: CommandItemType[]
}

export function CommandPalette({ isOpen, onClose, commands }: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const listRef = useRef<HTMLDivElement>(null)

  const filtered = useMemo(() => {
    if (!query.trim()) return commands
    const q = query.toLowerCase()
    return commands.filter(c => c.title.toLowerCase().includes(q))
  }, [commands, query])

  useEffect(() => {
    if (!isOpen) {
      setQuery('')
      setActiveIndex(0)
    }
  }, [isOpen])

  const runActive = () => {
    const cmd = filtered[activeIndex]
    if (cmd) {
      cmd.action()
      onClose()
    }
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    } else if (e.key === 'Enter') {
      e.preventDefault()
      runActive()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i: number) => Math.min(i + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i: number) => Math.max(i - 1, 0))
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="p-0 overflow-hidden max-w-xl ide-command-palette">
        <VisuallyHidden>
          <DialogTitle>Command Palette</DialogTitle>
        </VisuallyHidden>
        <div className="border-b border-border px-3 py-2 flex items-center bg-background">
          <Search className="h-4 w-4 text-muted-foreground mr-2" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Type a command or search..."
            className="w-full bg-transparent outline-none text-sm placeholder:text-muted-foreground"
          />
        </div>
        <ScrollArea className="max-h-[50vh]">
          <div ref={listRef} className="py-1">
            {filtered.length === 0 && (
              <div className="px-3 py-6 text-sm text-muted-foreground">No commands found</div>
            )}
            {filtered.map((cmd: CommandItemType, idx: number) => (
              <button
                key={cmd.id}
                onClick={() => { cmd.action(); onClose() }}
                className={`w-full text-left px-3 py-2 text-sm flex items-center justify-between hover:bg-accent ${idx === activeIndex ? 'bg-accent' : ''}`}
              >
                <span>{cmd.title}</span>
                {cmd.shortcut && (
                  <span className="text-xs text-muted-foreground">{cmd.shortcut}</span>
                )}
              </button>
            ))}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}

