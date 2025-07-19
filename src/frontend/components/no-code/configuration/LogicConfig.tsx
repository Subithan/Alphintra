import { NodeConfigFields, NodeConfigResult } from './types';

export function getLogicConfig(): NodeConfigResult {
  const fields: NodeConfigFields = {
    operation: {
      type: 'select',
      label: 'Logic Operation',
      description: 'Type of logical operation',
      options: [
        { value: 'AND', label: 'AND - All inputs must be true' },
        { value: 'OR', label: 'OR - Any input must be true' },
        { value: 'NOT', label: 'NOT - Invert input signal' },
        { value: 'XOR', label: 'XOR - Exclusive OR' },
      ],
      default: 'AND'
    },

    inputs: {
      type: 'number',
      label: 'Number of Inputs',
      description: 'How many inputs to connect',
      min: 1,
      max: 8,
      default: 2
    }
  };

  return { fields };
}

export function validateLogicConfig(params: Record<string, any>): string[] {
  const errors: string[] = [];

  if (params.inputs < 1 || params.inputs > 8) {
    errors.push('Number of inputs must be between 1 and 8');
  }

  if (params.operation === 'NOT' && params.inputs > 1) {
    errors.push('NOT operation can only have 1 input');
  }

  return errors;
}