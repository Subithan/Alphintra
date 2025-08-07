'use client';

import { useEffect, useState } from 'react';
import { X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  title?: string;
  message: string;
  type: ToastType;
  duration?: number;
}

interface ToasterContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

let toasterContext: ToasterContextType | null = null;

export const toast = {
  success: (message: string, title?: string) => {
    toasterContext?.addToast({ message, title, type: 'success' });
  },
  error: (message: string, title?: string) => {
    toasterContext?.addToast({ message, title, type: 'error' });
  },
  warning: (message: string, title?: string) => {
    toasterContext?.addToast({ message, title, type: 'warning' });
  },
  info: (message: string, title?: string) => {
    toasterContext?.addToast({ message, title, type: 'info' });
  },
};

interface ToastItemProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  useEffect(() => {
    const duration = toast.duration || 5000;
    const timer = setTimeout(() => {
      onRemove(toast.id);
    }, duration);

    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onRemove]);

  const getToastStyles = (type: ToastType) => {
    switch (type) {
      case 'success':
        return 'bg-profit border-profit/20 text-white';
      case 'error':
        return 'bg-loss border-loss/20 text-white';
      case 'warning':
        return 'bg-yellow-500 border-yellow-500/20 text-white';
      case 'info':
        return 'bg-primary border-primary/20 text-primary-foreground';
      default:
        return 'bg-card border-border text-card-foreground';
    }
  };

  return (
    <div
      className={`
        relative p-4 rounded-lg border shadow-lg min-w-[300px] max-w-[400px]
        transform transition-all duration-300 ease-in-out
        animate-in slide-in-from-right-full
        ${getToastStyles(toast.type)}
      `}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          {toast.title && (
            <div className="font-semibold text-sm mb-1">
              {toast.title}
            </div>
          )}
          <div className="text-sm">
            {toast.message}
          </div>
        </div>
        <button
          onClick={() => onRemove(toast.id)}
          className="p-1 rounded-md hover:bg-black/10 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (toastData: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast: Toast = { ...toastData, id };
    
    setToasts((prevToasts) => [...prevToasts, newToast]);
  };

  const removeToast = (id: string) => {
    setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id));
  };

  // Set up global toaster context
  useEffect(() => {
    toasterContext = { toasts, addToast, removeToast };
    
    return () => {
      toasterContext = null;
    };
  }, [toasts]);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onRemove={removeToast}
        />
      ))}
    </div>
  );
}