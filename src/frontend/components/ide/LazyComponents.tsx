'use client'

import React, { lazy, Suspense } from 'react'
import { RefreshCw } from 'lucide-react'

// Lazy load heavy components for better performance
const LazyMonacoEditor = lazy(() => import('@monaco-editor/react'))

// Loading fallback component
const EditorLoadingFallback = () => (
  <div className="h-full flex items-center justify-center bg-background">
    <div className="text-center space-y-4">
      <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-primary" />
      </div>
      <div>
        <h3 className="text-sm font-medium text-foreground mb-1">Loading Editor</h3>
        <p className="text-xs text-muted-foreground">Initializing Monaco Editor...</p>
      </div>
    </div>
  </div>
)

// Optimized Monaco Editor wrapper
export const OptimizedMonacoEditor = React.memo(({ 
  height, 
  language, 
  value, 
  onChange, 
  theme, 
  onMount, 
  options 
}: any) => (
  <Suspense fallback={<EditorLoadingFallback />}>
    <LazyMonacoEditor
      height={height}
      language={language}
      value={value}
      onChange={onChange}
      theme={theme}
      onMount={onMount}
      options={options}
      loading={<EditorLoadingFallback />}
    />
  </Suspense>
))

OptimizedMonacoEditor.displayName = 'OptimizedMonacoEditor'