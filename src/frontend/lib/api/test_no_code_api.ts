// Integration test for the no-code API client
// This tests the API client structure and type definitions

import {
  NoCodeApiClient,
  type Workflow,
  type WorkflowCreate,
  type ExecutionConfig,
  type Component,
  type Template
} from './no-code-api';
import { buildGatewayUrl } from '../config/gateway';

// Mock fetch for testing
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('NoCodeApiClient', () => {
  let client: NoCodeApiClient;

  beforeEach(() => {
    client = new NoCodeApiClient();
    mockFetch.mockClear();
  });

  describe('Workflow Management', () => {
    it('should create workflow with correct payload', async () => {
      const mockWorkflow: Workflow = {
        id: 1,
        uuid: 'test-uuid',
        name: 'Test Workflow',
        description: 'Test Description',
        category: 'custom',
        tags: ['test'],
        workflow_data: { nodes: [], edges: [] },
        generated_code: '',
        generated_code_language: 'python',
        generated_requirements: [],
        compilation_status: 'pending',
        compilation_errors: [],
        validation_status: 'pending',
        validation_errors: [],
        deployment_status: 'draft',
        execution_mode: 'backtest',
        version: 1,
        is_template: false,
        is_public: false,
        total_executions: 0,
        successful_executions: 0,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkflow,
      });

      const workflowCreate: WorkflowCreate = {
        name: 'Test Workflow',
        description: 'Test Description',
        category: 'custom',
        workflow_data: { nodes: [], edges: [] },
      };

      const result = await client.createWorkflow(workflowCreate);

      expect(mockFetch).toHaveBeenCalledWith(
        buildGatewayUrl('/api/workflows'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(workflowCreate),
        })
      );

      expect(result).toEqual(mockWorkflow);
    });

    it('should get workflows with filters', async () => {
      const mockWorkflows: Workflow[] = [];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkflows,
      });

      const filters = { category: 'custom', limit: 10 };
      await client.getWorkflows(filters);

      expect(mockFetch).toHaveBeenCalledWith(
        buildGatewayUrl('/api/workflows?category=custom&limit=10'),
        expect.any(Object)
      );
    });
  });

  describe('Compilation', () => {
    it('should compile workflow', async () => {
      const mockCompilationResult = {
        workflow_id: 'test-uuid',
        generated_code: 'def test(): pass',
        requirements: ['pandas'],
        status: 'compiled',
        errors: [],
        created_at: '2024-01-01T00:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCompilationResult,
      });

      const result = await client.compileWorkflow('test-uuid');

      expect(mockFetch).toHaveBeenCalledWith(
        buildGatewayUrl('/api/workflows/test-uuid/compile'),
        expect.objectContaining({
          method: 'POST',
        })
      );

      expect(result).toEqual(mockCompilationResult);
    });
  });

  describe('Execution', () => {
    it('should execute workflow with config', async () => {
      const mockExecution = {
        id: 1,
        uuid: 'execution-uuid',
        workflow_id: 1,
        execution_type: 'backtest',
        symbols: ['BTCUSDT'],
        timeframe: '1h',
        initial_capital: 10000,
        status: 'pending',
        progress: 0,
        total_trades: 0,
        winning_trades: 0,
        trades_data: [],
        performance_metrics: {},
        execution_logs: [],
        error_logs: [],
        started_at: '2024-01-01T00:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockExecution,
      });

      const config: ExecutionConfig = {
        execution_type: 'backtest',
        symbols: ['BTCUSDT'],
        timeframe: '1h',
        initial_capital: 10000,
      };

      const result = await client.executeWorkflow('test-uuid', config);

      expect(mockFetch).toHaveBeenCalledWith(
        buildGatewayUrl('/api/workflows/test-uuid/execute'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(config),
        })
      );

      expect(result).toEqual(mockExecution);
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ message: 'Workflow not found' }),
      });

      await expect(client.getWorkflow('nonexistent')).rejects.toThrow(
        'API Error: 404 Not Found'
      );
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(client.getWorkflows()).rejects.toThrow('Network error');
    });
  });

  describe('Health Check', () => {
    it('should perform health check', async () => {
      const mockHealth = {
        status: 'healthy',
        service: 'no-code-service',
        version: '2.0.0',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealth,
      });

      const result = await client.healthCheck();

      expect(mockFetch).toHaveBeenCalledWith(
        buildGatewayUrl('/health'),
        expect.any(Object)
      );

      expect(result).toEqual(mockHealth);
    });
  });
});

// Type Tests - These will fail at compile time if types are incorrect
describe('Type Definitions', () => {
  it('should have correct Workflow type', () => {
    const workflow: Workflow = {
      id: 1,
      uuid: 'test-uuid',
      name: 'Test',
      description: 'Test',
      category: 'custom',
      tags: [],
      workflow_data: { nodes: [], edges: [] },
      generated_code: '',
      generated_code_language: 'python',
      generated_requirements: [],
      compilation_status: 'pending',
      compilation_errors: [],
      validation_status: 'pending',
      validation_errors: [],
      deployment_status: 'draft',
      execution_mode: 'backtest',
      version: 1,
      is_template: false,
      is_public: false,
      total_executions: 0,
      successful_executions: 0,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    expect(workflow.compilation_status).toBe('pending');
  });

  it('should have correct ExecutionConfig type', () => {
    const config: ExecutionConfig = {
      execution_type: 'backtest',
      symbols: ['BTCUSDT'],
      timeframe: '1h',
      initial_capital: 10000,
    };

    expect(config.execution_type).toBe('backtest');
  });
});

// Export a simple test runner for manual verification
export function runBasicTests(): Promise<boolean> {
  return new Promise((resolve) => {
    console.log('🔍 Testing No-Code API Client Structure...');
    
    try {
      // Test client instantiation
      const client = new NoCodeApiClient();
      console.log('✅ NoCodeApiClient instantiated successfully');
      
      // Test method existence
      const requiredMethods = [
        'createWorkflow',
        'getWorkflows', 
        'getWorkflow',
        'updateWorkflow',
        'deleteWorkflow',
        'compileWorkflow',
        'executeWorkflow',
        'getExecution',
        'getComponents',
        'getTemplates',
        'healthCheck'
      ];
      
      for (const method of requiredMethods) {
        if (typeof client[method] !== 'function') {
          throw new Error(`Missing method: ${method}`);
        }
      }
      console.log('✅ All required methods present');
      
      // Test type exports (compilation test)
      const workflowCreate: WorkflowCreate = {
        name: 'Test',
        workflow_data: { nodes: [], edges: [] }
      };
      console.log('✅ Type definitions compile correctly');
      
      console.log('🎉 All basic tests passed!');
      resolve(true);
      
    } catch (error) {
      console.error('❌ Test failed:', error);
      resolve(false);
    }
  });
}
