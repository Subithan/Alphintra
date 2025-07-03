// Workflow Execution Monitoring Dashboard
// Real-time monitoring of workflow executions with performance metrics

import React, { useState, useEffect } from 'react';
import { useExecution, useExecuteWorkflow } from '../../lib/hooks/use-no-code';
import { type ExecutionConfig } from '../../lib/api/no-code-api';

interface ExecutionDashboardProps {
  workflowId?: string;
  executionId?: string;
  onClose?: () => void;
}

interface ExecutionFormData {
  execution_type: 'backtest' | 'paper_trade' | 'live_trade';
  symbols: string[];
  timeframe: '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d';
  start_date?: string;
  end_date?: string;
  initial_capital: number;
}

export const ExecutionDashboard: React.FC<ExecutionDashboardProps> = ({
  workflowId,
  executionId,
  onClose,
}) => {
  const [showExecutionForm, setShowExecutionForm] = useState(!executionId);
  const [formData, setFormData] = useState<ExecutionFormData>({
    execution_type: 'backtest',
    symbols: ['BTCUSDT'],
    timeframe: '1h',
    initial_capital: 10000,
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days ago
    end_date: new Date().toISOString().split('T')[0], // today
  });

  const executeWorkflowMutation = useExecuteWorkflow();
  const { 
    data: execution, 
    isLoading: isExecutionLoading,
    error: executionError 
  } = useExecution(executionId || '');

  // Handle form submission
  const handleExecute = async () => {
    if (!workflowId) return;

    try {
      const config: ExecutionConfig = {
        ...formData,
        start_date: formData.execution_type === 'backtest' ? formData.start_date : undefined,
        end_date: formData.execution_type === 'backtest' ? formData.end_date : undefined,
      };

      const newExecution = await executeWorkflowMutation.mutateAsync({
        workflowId,
        config,
      });

      // Switch to monitoring the new execution
      window.history.pushState(
        {},
        '',
        `?execution=${newExecution.uuid}`
      );
      setShowExecutionForm(false);
    } catch (error) {
      console.error('Failed to execute workflow:', error);
    }
  };

  // Format currency values
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  // Format percentage
  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (showExecutionForm) {
    return (
      <div className="bg-white rounded-lg shadow-lg max-w-2xl mx-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Execute Workflow</h2>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Form */}
        <div className="p-6 space-y-6">
          {/* Execution Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Execution Type
            </label>
            <select
              value={formData.execution_type}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                execution_type: e.target.value as any 
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="backtest">Backtest (Historical)</option>
              <option value="paper_trade">Paper Trading (Live)</option>
              <option value="live_trade">Live Trading</option>
            </select>
          </div>

          {/* Trading Pairs */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Trading Pairs
            </label>
            <input
              type="text"
              value={formData.symbols.join(', ')}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                symbols: e.target.value.split(',').map(s => s.trim()) 
              }))}
              placeholder="BTCUSDT, ETHUSDT, ADAUSDT"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Timeframe */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Timeframe
            </label>
            <select
              value={formData.timeframe}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                timeframe: e.target.value as any 
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="1m">1 Minute</option>
              <option value="5m">5 Minutes</option>
              <option value="15m">15 Minutes</option>
              <option value="30m">30 Minutes</option>
              <option value="1h">1 Hour</option>
              <option value="4h">4 Hours</option>
              <option value="1d">1 Day</option>
            </select>
          </div>

          {/* Date Range (for backtest) */}
          {formData.execution_type === 'backtest' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          )}

          {/* Initial Capital */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Initial Capital ($)
            </label>
            <input
              type="number"
              value={formData.initial_capital}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                initial_capital: parseFloat(e.target.value) || 0 
              }))}
              min="100"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            {onClose && (
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleExecute}
              disabled={executeWorkflowMutation.isPending}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed"
            >
              {executeWorkflowMutation.isPending ? 'Starting...' : 'Start Execution'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isExecutionLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-4xl mx-auto">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading execution details...</span>
        </div>
      </div>
    );
  }

  if (executionError || !execution) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-4xl mx-auto">
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-red-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Execution Not Found</h3>
          <p className="text-gray-600">The requested execution could not be loaded.</p>
          {onClose && (
            <button
              onClick={onClose}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Go Back
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg max-w-6xl mx-auto">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Execution Monitor</h2>
          <p className="text-sm text-gray-500">Execution ID: {execution.uuid}</p>
        </div>
        <div className="flex items-center space-x-3">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(execution.status)}`}>
            {execution.status.charAt(0).toUpperCase() + execution.status.slice(1)}
          </span>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        {/* Progress Bar */}
        {execution.status === 'running' && (
          <div className="mb-6">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>{execution.current_step || 'Processing...'}</span>
              <span>{execution.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${execution.progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-blue-600">Initial Capital</div>
            <div className="text-2xl font-bold text-blue-900">
              {formatCurrency(execution.initial_capital)}
            </div>
          </div>
          
          {execution.final_capital && (
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-green-600">Final Capital</div>
              <div className="text-2xl font-bold text-green-900">
                {formatCurrency(execution.final_capital)}
              </div>
            </div>
          )}
          
          {execution.total_return_percent !== undefined && (
            <div className={`p-4 rounded-lg ${execution.total_return_percent >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
              <div className={`text-sm font-medium ${execution.total_return_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                Total Return
              </div>
              <div className={`text-2xl font-bold ${execution.total_return_percent >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                {formatPercentage(execution.total_return_percent)}
              </div>
            </div>
          )}
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-gray-600">Total Trades</div>
            <div className="text-2xl font-bold text-gray-900">{execution.total_trades}</div>
            {execution.winning_trades > 0 && (
              <div className="text-sm text-gray-500">
                {execution.winning_trades} winning ({((execution.winning_trades / execution.total_trades) * 100).toFixed(1)}%)
              </div>
            )}
          </div>
        </div>

        {/* Performance Metrics */}
        {execution.performance_metrics && Object.keys(execution.performance_metrics).length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(execution.performance_metrics).map(([key, value]) => (
                <div key={key} className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-sm font-medium text-gray-600">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                  <div className="text-lg font-bold text-gray-900">
                    {typeof value === 'number' ? value.toFixed(2) : String(value)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Execution Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Configuration */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Type:</span>
                <span className="font-medium">{execution.execution_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Symbols:</span>
                <span className="font-medium">{execution.symbols.join(', ')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Timeframe:</span>
                <span className="font-medium">{execution.timeframe}</span>
              </div>
              {execution.start_date && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Period:</span>
                  <span className="font-medium">
                    {new Date(execution.start_date).toLocaleDateString()} - {' '}
                    {execution.end_date ? new Date(execution.end_date).toLocaleDateString() : 'Now'}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Timeline */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Timeline</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Started:</span>
                <span className="font-medium">
                  {new Date(execution.started_at).toLocaleString()}
                </span>
              </div>
              {execution.completed_at && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Completed:</span>
                  <span className="font-medium">
                    {new Date(execution.completed_at).toLocaleString()}
                  </span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Duration:</span>
                <span className="font-medium">
                  {execution.completed_at 
                    ? `${Math.round((new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()) / 1000)}s`
                    : 'In progress'
                  }
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Error Logs */}
        {execution.error_logs && execution.error_logs.length > 0 && (
          <div className="mt-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Error Logs</h3>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              {execution.error_logs.map((log, index) => (
                <div key={index} className="text-red-800 text-sm">
                  {typeof log === 'string' ? log : JSON.stringify(log)}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="mt-8 flex justify-between items-center pt-6 border-t border-gray-200">
          <div className="text-sm text-gray-500">
            Last updated: {new Date().toLocaleTimeString()}
          </div>
          <div className="space-x-3">
            <button className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
              Download Report
            </button>
            <button 
              onClick={() => setShowExecutionForm(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Run Again
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExecutionDashboard;