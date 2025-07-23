import React, { useState, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/no-code/input';
import { useNoCodeStore } from '@/lib/stores/no-code-store';
import { shallow } from 'zustand/shallow';

interface EditableTitleProps {
  workflowId: string;
  initialTitle: string;
  className?: string;
  readOnly?: boolean;
}

export function EditableTitle({ workflowId, initialTitle, className = '', readOnly = false }: EditableTitleProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(initialTitle);
  const inputRef = useRef<HTMLInputElement>(null);
  
  
  const { currentWorkflow, saveWorkflow } = useNoCodeStore(
    (state) => ({
      currentWorkflow: state.currentWorkflow,
      saveWorkflow: state.saveWorkflow
    }),
    shallow
  );

  // Update local title when initialTitle changes
  useEffect(() => {
    setTitle(initialTitle);
  }, [initialTitle]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleBlur = async () => {
    setIsEditing(false);
    if (title.trim() && title !== initialTitle) {
      try {
        // Use the existing saveWorkflow method
        saveWorkflow(title.trim());
      } catch (error) {
        console.error('Failed to update workflow name:', error);
        setTitle(initialTitle); // Revert on error
      }
    } else {
      setTitle(initialTitle); // Revert if empty or unchanged
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      inputRef.current?.blur();
    } else if (e.key === 'Escape') {
      setTitle(initialTitle);
      setIsEditing(false);
    }
  };

  const handleEdit = () => {
    if (!readOnly) {
      setIsEditing(true);
    }
  };

  const textMeasureRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (textMeasureRef.current) {
      const width = textMeasureRef.current.offsetWidth;
      const padding = 16; // 2 * px-2 (8px each side)
      setMeasuredWidth(width + padding);
    }
  }, [title]);

  const [measuredWidth, setMeasuredWidth] = useState(0);

  return (
    <div className={className}>
      <span
        ref={textMeasureRef}
        className="absolute invisible text-2xl font-medium whitespace-pre"
        aria-hidden="true"
      >
        {title || 'Untitled Model'}
      </span>
      {isEditing ? (
        <Input
          ref={inputRef}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          className="text-2xl font-medium border-2 border-blue-800 focus-visible:ring-0 focus-visible:ring-offset-0 rounded-md shadow-sm h-10 box-border overflow-hidden whitespace-nowrap align-middle"
          style={{ 
            width: `${Math.max(measuredWidth, 160)}px`,
            minWidth: '160px',
            maxWidth: '450px',
            lineHeight: '2.5rem',
            verticalAlign: 'middle'
          }}
        />
      ) : (
        <h1
          className="text-2xl font-medium text-foreground cursor-text border-2 border-transparent hover:border-black/80 focus-visible:ring-0 focus-visible:ring-offset-0 rounded-md shadow-sm h-10 box-border overflow-hidden whitespace-nowrap align-middle transition-all duration-200"
          onClick={handleEdit}
          style={{ 
            cursor: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'16\' height=\'16\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'currentColor\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\'%3E%3Cpath d=\'m18 2 4 4-14 14H4v-4L18 2z\'/\%3E%3C/svg%3E") 0 16, pointer',
            width: `${Math.max(measuredWidth, 160)}px`,
            minWidth: '160px',
            maxWidth: '450px',
            lineHeight: '2.5rem',
            verticalAlign: 'middle'
          }}
        >
          {title}
        </h1>
      )}
    </div>
  );
}