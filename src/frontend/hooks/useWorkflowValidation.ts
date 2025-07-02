import { useState, useEffect, useMemo } from 'react';
import { Node, Edge } from 'reactflow';
import { validateWorkflow, ValidationResult, ValidationError } from '@/lib/workflow-validation';

export interface UseWorkflowValidationResult {
  validation: ValidationResult;
  isValidating: boolean;
  criticalErrors: ValidationError[];
  warnings: ValidationError[];
  validateNow: () => void;
  getNodeErrors: (nodeId: string) => ValidationError[];
  getEdgeErrors: (edgeId: string) => ValidationError[];
  hasErrors: boolean;
  hasWarnings: boolean;
}

export function useWorkflowValidation(
  nodes: Node[],
  edges: Edge[],
  options: {
    autoValidate?: boolean;
    debounceMs?: number;
    enableRealTime?: boolean;
  } = {}
): UseWorkflowValidationResult {
  const {
    autoValidate = true,
    debounceMs = 500,
    enableRealTime = true
  } = options;

  const [validation, setValidation] = useState<ValidationResult>({
    isValid: true,
    errors: [],
    warnings: [],
    performance: {
      estimatedComplexity: 0,
      estimatedExecutionTime: 0,
      memoryUsage: 0
    }
  });
  
  const [isValidating, setIsValidating] = useState(false);
  const [validationTimeoutId, setValidationTimeoutId] = useState<NodeJS.Timeout | null>(null);

  // Memoized validation function
  const performValidation = useMemo(
    () => async (): Promise<ValidationResult> => {
      setIsValidating(true);
      
      try {
        // Add a small delay to simulate processing and prevent excessive calls
        await new Promise(resolve => setTimeout(resolve, 50));
        
        const result = validateWorkflow(nodes, edges);
        return result;
      } finally {
        setIsValidating(false);
      }
    },
    [nodes, edges]
  );

  // Manual validation trigger
  const validateNow = () => {
    if (validationTimeoutId) {
      clearTimeout(validationTimeoutId);
    }
    
    performValidation().then(setValidation);
  };

  // Auto-validation with debouncing
  useEffect(() => {
    if (!autoValidate || !enableRealTime) return;

    if (validationTimeoutId) {
      clearTimeout(validationTimeoutId);
    }

    const timeoutId = setTimeout(() => {
      performValidation().then(setValidation);
    }, debounceMs);

    setValidationTimeoutId(timeoutId);

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [nodes, edges, autoValidate, enableRealTime, debounceMs, performValidation]);

  // Helper functions for component use
  const getNodeErrors = (nodeId: string): ValidationError[] => {
    return [...validation.errors, ...validation.warnings].filter(
      error => error.nodeId === nodeId
    );
  };

  const getEdgeErrors = (edgeId: string): ValidationError[] => {
    return [...validation.errors, ...validation.warnings].filter(
      error => error.edgeId === edgeId
    );
  };

  const criticalErrors = validation.errors.filter(
    error => error.severity === 'critical'
  );

  const warnings = validation.warnings;
  const hasErrors = validation.errors.length > 0;
  const hasWarnings = validation.warnings.length > 0;

  return {
    validation,
    isValidating,
    criticalErrors,
    warnings,
    validateNow,
    getNodeErrors,
    getEdgeErrors,
    hasErrors,
    hasWarnings
  };
}