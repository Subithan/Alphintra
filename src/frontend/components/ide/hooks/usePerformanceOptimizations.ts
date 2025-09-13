'use client'

import { useEffect, useRef, useCallback } from 'react'

// Custom hook for performance optimizations
export const usePerformanceOptimizations = () => {
  const rafRef = useRef<number>()

  // Throttled callback using requestAnimationFrame
  const useRAFThrottle = useCallback(<T extends (...args: any[]) => void>(
    callback: T,
    dependencies: any[]
  ): T => {
    const lastArgs = useRef<Parameters<T>>()

    return useCallback(
      ((...args: Parameters<T>) => {
        lastArgs.current = args

        if (!rafRef.current) {
          rafRef.current = requestAnimationFrame(() => {
            rafRef.current = undefined
            if (lastArgs.current) {
              callback(...lastArgs.current)
            }
          })
        }
      }) as T,
      dependencies
    )
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [])

  return { useRAFThrottle }
}

// Debounced value hook with cleanup
export const useOptimizedDebounce = <T>(value: T, delay: number): T => {
  const timeoutRef = useRef<NodeJS.Timeout>()
  const valueRef = useRef<T>(value)

  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      valueRef.current = value
    }, delay)

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [value, delay])

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return valueRef.current
}

// Intersection observer hook for virtualization
export const useIntersectionObserver = (
  callback: IntersectionObserverCallback,
  options?: IntersectionObserverInit
) => {
  const observerRef = useRef<IntersectionObserver>()

  const observe = useCallback((element: Element) => {
    if (observerRef.current) {
      observerRef.current.observe(element)
    }
  }, [])

  const unobserve = useCallback((element: Element) => {
    if (observerRef.current) {
      observerRef.current.unobserve(element)
    }
  }, [])

  useEffect(() => {
    observerRef.current = new IntersectionObserver(callback, options)

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [callback, options])

  return { observe, unobserve }
}