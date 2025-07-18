"use client"

import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"

interface SearchBarProps {
  placeholder?: string
  className?: string
}

export function SearchBar({ placeholder = "Search...", className = "" }: SearchBarProps) {
  return (
    <div className={`flex-1 max-w-md ${className}`}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input 
          placeholder={placeholder}
          className="pl-10  border focus-visible:ring-1"
        />
      </div>
    </div>
  )
}
