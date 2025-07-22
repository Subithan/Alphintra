import { useState, useCallback } from 'react';

export interface Toast {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((toast: Toast) => {
    setToasts(prev => [...prev, toast]);
    
    // Auto-remove toast after 5 seconds
    setTimeout(() => {
      setToasts(prev => prev.slice(1));
    }, 5000);
    
    // For now, just log to console
    console.log(`[${toast.variant || 'default'}] ${toast.title}${toast.description ? `: ${toast.description}` : ''}`);
  }, []);

  return { toast, toasts };
}