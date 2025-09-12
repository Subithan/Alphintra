'use client'

import React, { memo, useEffect } from 'react'

// Performance optimization utilities
export const optimizeForPerformance = () => {
  // Disable smooth scrolling for better performance
  if (typeof window !== 'undefined') {
    document.documentElement.style.scrollBehavior = 'auto'
    
    // Add performance hints to critical elements
    const addPerformanceHints = () => {
      const monacoEditor = document.querySelector('.monaco-editor')
      if (monacoEditor) {
        (monacoEditor as HTMLElement).style.willChange = 'scroll-position'
        (monacoEditor as HTMLElement).style.transform = 'translateZ(0)'
      }

      const scrollAreas = document.querySelectorAll('[data-radix-scroll-area-viewport]')
      scrollAreas.forEach(area => {
        (area as HTMLElement).style.willChange = 'scroll-position'
        (area as HTMLElement).style.transform = 'translateZ(0)'
      })
    }

    // Apply optimizations after DOM is ready
    setTimeout(addPerformanceHints, 100)
    
    // Debounce resize events globally
    let resizeTimeout: NodeJS.Timeout
    const originalAddEventListener = window.addEventListener
    window.addEventListener = function(type: string, listener: any, options?: any) {
      if (type === 'resize' && typeof listener === 'function') {
        const debouncedListener = (...args: any[]) => {
          clearTimeout(resizeTimeout)
          resizeTimeout = setTimeout(() => listener(...args), 100)
        }
        return originalAddEventListener.call(this, type, debouncedListener, options)
      }
      return originalAddEventListener.call(this, type, listener, options)
    }
  }
}

// Performance monitoring component
export const PerformanceMonitor = memo(() => {
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      // Monitor performance in development
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach((entry) => {
          if (entry.entryType === 'measure' && entry.duration > 16) {
            console.warn(`Slow operation detected: ${entry.name} took ${entry.duration.toFixed(2)}ms`)
          }
        })
      })
      
      try {
        observer.observe({ entryTypes: ['measure', 'navigation', 'paint'] })
      } catch (e) {
        // Performance Observer not supported
      }
      
      return () => observer.disconnect()
    }
  }, [])

  return null
})

PerformanceMonitor.displayName = 'PerformanceMonitor'

// Virtual scrolling hook for large lists
export const useVirtualScrolling = (items: any[], containerHeight: number, itemHeight: number) => {
  const [scrollTop, setScrollTop] = React.useState(0)
  
  const visibleStart = Math.floor(scrollTop / itemHeight)
  const visibleEnd = Math.min(visibleStart + Math.ceil(containerHeight / itemHeight) + 1, items.length)
  
  const visibleItems = items.slice(visibleStart, visibleEnd).map((item, index) => ({
    ...item,
    index: visibleStart + index
  }))
  
  const totalHeight = items.length * itemHeight
  const offsetY = visibleStart * itemHeight
  
  return {
    visibleItems,
    totalHeight,
    offsetY,
    onScroll: (e: React.UIEvent<HTMLDivElement>) => {
      setScrollTop(e.currentTarget.scrollTop)
    }
  }
}

// Debounced input hook
export const useDebouncedValue = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = React.useState<T>(value)

  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

// Throttled callback hook
export const useThrottledCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T => {
  const lastRun = React.useRef(Date.now())

  return React.useCallback(
    ((...args) => {
      if (Date.now() - lastRun.current >= delay) {
        callback(...args)
        lastRun.current = Date.now()
      }
    }) as T,
    [callback, delay]
  )
}