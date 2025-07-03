// Workflow Builder Toolbar
// Main toolbar with save, compile, execute, and view controls

import React from 'react';
import { NoCodeWorkflow } from '../../lib/stores/no-code-store';

interface WorkflowToolbarProps {
  workflow: NoCodeWorkflow | null;
  onSave: () => void;
  onCompile: () => void;
  onExecute: () => void;
  isSaving: boolean;
  isCompiling: boolean;
  saveStatus: 'idle' | 'saving' | 'saved' | 'error';
  readOnly: boolean;
  onTogglePalette: () => void;
  onToggleProperties: () => void;
}

export const WorkflowToolbar: React.FC<WorkflowToolbarProps> = ({
  workflow,
  onSave,
  onCompile,
  onExecute,
  isSaving,
  isCompiling,
  saveStatus,
  readOnly,
  onTogglePalette,
  onToggleProperties,
}) => {
  const getSaveButtonText = () => {
    switch (saveStatus) {
      case 'saving':
        return 'Saving...';
      case 'saved':
        return 'Saved!';
      case 'error':
        return 'Save Failed';
      default:
        return workflow?.id === 'default' ? 'Save As...' : 'Save';
    }
  };

  const getSaveButtonStyle = () => {
    switch (saveStatus) {
      case 'saving':
        return 'bg-blue-400 cursor-not-allowed';
      case 'saved':
        return 'bg-green-500 hover:bg-green-600';
      case 'error':
        return 'bg-red-500 hover:bg-red-600';
      default:
        return 'bg-blue-600 hover:bg-blue-700';
    }
  };

  return (
    <div className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4">
      {/* Left Section - Workflow Info */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">
              {workflow?.name || 'Untitled Workflow'}
            </h1>
            {workflow?.description && (
              <p className="text-sm text-gray-500">{workflow.description}</p>
            )}
          </div>
        </div>
      </div>

      {/* Center Section - Actions */}
      <div className="flex items-center space-x-3">
        {!readOnly && (
          <>
            {/* Save Button */}
            <button
              onClick={onSave}
              disabled={isSaving}
              className={`px-4 py-2 text-white text-sm font-medium rounded-lg transition-colors ${getSaveButtonStyle()}`}
            >
              {getSaveButtonText()}
            </button>

            {/* Compile Button */}
            <button
              onClick={onCompile}
              disabled={isCompiling || !workflow}
              className={`px-4 py-2 text-sm font-medium rounded-lg border transition-colors ${
                isCompiling
                  ? 'bg-yellow-400 text-yellow-900 border-yellow-500 cursor-not-allowed'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {isCompiling ? 'Compiling...' : 'Compile'}
            </button>
          </>
        )}

        {/* Execute Button */}
        <button
          onClick={onExecute}
          disabled={!workflow}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          Execute
        </button>

        {/* Divider */}
        <div className="w-px h-6 bg-gray-300"></div>

        {/* View Controls */}
        <div className="flex items-center space-x-1">
          <button
            onClick={onTogglePalette}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Toggle Component Palette"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
          </button>
          
          <button
            onClick={onToggleProperties}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Toggle Properties Panel"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
            </svg>
          </button>
        </div>
      </div>

      {/* Right Section - Status */}
      <div className="flex items-center space-x-4">
        {/* Workflow Status */}
        <div className="flex items-center space-x-2 text-sm">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-gray-600">Connected</span>
          </div>
          
          {workflow && (
            <div className="text-gray-400">
              • Last saved {new Date(workflow.updatedAt || workflow.createdAt).toLocaleTimeString()}
            </div>
          )}
        </div>

        {/* Help Button */}
        <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default WorkflowToolbar;