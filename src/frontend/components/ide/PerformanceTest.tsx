'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, Zap, Clock, MemoryStick } from 'lucide-react'

interface PerformanceMetrics {
  renderTime: number
  memoryUsage: number
  componentCount: number
  rerenderCount: number
}

export function PerformanceTest() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderTime: 0,
    memoryUsage: 0,
    componentCount: 0,
    rerenderCount: 0
  })
  const [isRunning, setIsRunning] = useState(false)

  const runPerformanceTest = async () => {
    if (typeof window === 'undefined') return
    
    setIsRunning(true)
    const startTime = performance.now()
    
    try {
      // Simulate heavy operations
      const componentCount = document.querySelectorAll('*').length
      const memoryInfo = (performance as any).memory
      
      // Measure render time
      await new Promise(resolve => {
        requestAnimationFrame(() => {
          const endTime = performance.now()
          setMetrics({
            renderTime: endTime - startTime,
            memoryUsage: memoryInfo ? Math.round(memoryInfo.usedJSHeapSize / 1024 / 1024) : 0,
            componentCount,
            rerenderCount: metrics.rerenderCount + 1
          })
          resolve(void 0)
        })
      })
    } catch (error) {
      console.error('Performance test failed:', error)
    } finally {
      setIsRunning(false)
    }
  }

  const getPerformanceStatus = (renderTime: number) => {
    if (renderTime < 16) return { status: 'Excellent', color: 'text-green-600', bg: 'bg-green-500/10' }
    if (renderTime < 32) return { status: 'Good', color: 'text-blue-600', bg: 'bg-blue-500/10' }
    if (renderTime < 50) return { status: 'Fair', color: 'text-orange-500', bg: 'bg-orange-500/10' }
    return { status: 'Poor', color: 'text-red-600', bg: 'bg-red-500/10' }
  }

  const performanceStatus = getPerformanceStatus(metrics.renderTime)

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-primary" />
          <span>Performance Monitor</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary">{metrics.renderTime.toFixed(1)}ms</div>
            <div className="text-xs text-muted-foreground">Render Time</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{metrics.memoryUsage}MB</div>
            <div className="text-xs text-muted-foreground">Memory Usage</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{metrics.componentCount}</div>
            <div className="text-xs text-muted-foreground">DOM Elements</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-500">{metrics.rerenderCount}</div>
            <div className="text-xs text-muted-foreground">Test Runs</div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm">Performance Status:</span>
          <Badge className={`${performanceStatus.bg} ${performanceStatus.color} border-0`}>
            {performanceStatus.status}
          </Badge>
        </div>

        <Button 
          onClick={runPerformanceTest} 
          disabled={isRunning}
          className="w-full"
        >
          <Zap className="h-4 w-4 mr-2" />
          {isRunning ? 'Testing...' : 'Run Performance Test'}
        </Button>

        <div className="text-xs text-muted-foreground space-y-1">
          <div>• Target: &lt;16ms for 60fps</div>
          <div>• Good: &lt;32ms for smooth UX</div>
          <div>• Memory optimized for &lt;100MB</div>
        </div>
      </CardContent>
    </Card>
  )
}