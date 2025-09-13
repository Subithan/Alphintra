'use client'

import React, { memo, useEffect } from 'react'

// Performance optimization utilities
export const optimizeForPerformance = () => {
  // Only run on client side to prevent hydration issues
  if (typeof window === 'undefined') return
  
  // Disable smooth scrolling for better performance
  document.documentElement.style.scrollBehavior = 'auto'
  
  // Add performance hints to critical elements
  const addPerformanceHints = () => {
    const monacoEditor = document.querySelector('.monaco-editor')
    if (monacoEditor) {
      const element = monacoEditor as HTMLElement
      element.style.willChange = 'scroll-position'
      element.style.transform = 'translateZ(0)'
    }

    const scrollAreas = document.querySelectorAll('[data-radix-scroll-area-viewport]')
    scrollAreas.forEach(area => {
      const element = area as HTMLElement
      element.style.willChange = 'scroll-position'
      element.style.transform = 'translateZ(0)'
    })
  }

  // Apply optimizations after DOM is ready
  const timeoutId = setTimeout(addPerformanceHints, 100)
  
  return () => {
    clearTimeout(timeoutId)
  }
}

// Performance monitoring component
export const PerformanceMonitor = memo(() => {
  useEffect(() => {
    if (typeof window === 'undefined') return
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
export const useDebouncedValue = <T,>(value: T, delay: number): T => {
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