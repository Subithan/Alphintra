import { EventEmitter } from 'events';
import { MarketDataManager, MarketDataPoint } from '../data/market-data-client';
import { DataValidator, ValidationResult } from '../data/data-validator';
import { StrategyExecutor } from '../execution/strategy-executor';
import { PerformanceMonitor } from '../monitoring/performance-monitor';
import { AlertSystem } from '../notifications/alert-system';

// Pipeline interfaces
export interface Pipeline {
  id: string;
  name: string;
  description: string;
  status: PipelineStatus;
  stages: PipelineStage[];
  configuration: PipelineConfiguration;
  schedule?: PipelineSchedule;
  metadata: PipelineMetadata;
  createdAt: Date;
  updatedAt: Date;
  lastRun?: Date;
  nextRun?: Date;
}

export type PipelineStatus = 'draft' | 'active' | 'paused' | 'stopped' | 'error' | 'completed';

export interface PipelineStage {
  id: string;
  name: string;
  type: StageType;
  configuration: StageConfiguration;
  dependencies: string[]; // Other stage IDs
  condition?: StageCondition;
  retryPolicy?: RetryPolicy;
  timeout?: number; // milliseconds
  enabled: boolean;
}

export type StageType = 
  | 'data_ingestion'      // Fetch market data
  | 'data_validation'     // Validate data quality
  | 'data_transformation' // Transform/clean data
  | 'strategy_execution'  // Execute trading strategies
  | 'risk_management'     // Apply risk controls
  | 'order_execution'     // Execute trades
  | 'monitoring'          // Monitor performance
  | 'notification'        // Send alerts/notifications
  | 'data_export'         // Export results
  | 'cleanup'             // Clean up resources
  | 'custom';             // Custom processing

export interface StageConfiguration {
  // Data ingestion configuration
  dataSources?: string[];
  symbols?: string[];
  timeframes?: string[];
  
  // Validation configuration
  validationRules?: string[];
  qualityThresholds?: Record<string, number>;
  
  // Strategy execution configuration
  strategies?: string[];
  executionMode?: 'backtest' | 'paper' | 'live';
  
  // Risk management configuration
  riskLimits?: RiskLimits;
  
  // Notification configuration
  notificationChannels?: string[];
  alertThresholds?: Record<string, number>;
  
  // Custom configuration
  customParameters?: Record<string, any>;
  scriptPath?: string;
  command?: string;
  environment?: Record<string, string>;
}

export interface RiskLimits {
  maxPositionSize?: number;
  maxDailyLoss?: number;
  maxDrawdown?: number;
  maxLeverage?: number;
  allowedSymbols?: string[];
  blockedSymbols?: string[];
}

export interface StageCondition {
  type: 'always' | 'success' | 'failure' | 'custom';
  expression?: string; // JavaScript expression for custom conditions
}

export interface RetryPolicy {
  maxRetries: number;
  backoffMs: number;
  maxBackoffMs: number;
  retryOnErrors?: string[]; // Error types to retry on
}

export interface PipelineConfiguration {
  parallelExecution: boolean;
  maxConcurrentStages: number;
  errorHandling: 'stop' | 'continue' | 'retry';
  dataRetention: number; // days
  enableMetrics: boolean;
  enableAlerts: boolean;
}

export interface PipelineSchedule {
  type: 'manual' | 'interval' | 'cron' | 'event';
  intervalMs?: number;
  cronExpression?: string;
  eventTriggers?: EventTrigger[];
  timezone?: string;
  enabled: boolean;
}

export interface EventTrigger {
  source: string;
  event: string;
  condition?: string;
}

export interface PipelineMetadata {
  tags: string[];
  owner: string;
  version: string;
  environment: 'development' | 'staging' | 'production';
  dependencies: string[];
  documentation?: string;
}

// Execution tracking
export interface PipelineExecution {
  id: string;
  pipelineId: string;
  status: ExecutionStatus;
  startTime: Date;
  endTime?: Date;
  duration?: number; // milliseconds
  stages: StageExecution[];
  metrics: ExecutionMetrics;
  logs: ExecutionLog[];
  errors: ExecutionError[];
  triggeredBy: string;
  context: ExecutionContext;
}

export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused';

export interface StageExecution {
  stageId: string;
  status: ExecutionStatus;
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  retryCount: number;
  output?: any;
  error?: string;
  metrics: StageMetrics;
}

export interface ExecutionMetrics {
  dataProcessed: number; // bytes
  recordsProcessed: number;
  errorsEncountered: number;
  performanceScore: number; // 0-100
  resourceUsage: {
    cpu: number; // percentage
    memory: number; // bytes
    network: number; // bytes
    storage: number; // bytes
  };
}

export interface StageMetrics {
  executionTime: number;
  throughput: number;
  errorRate: number;
  resourceUsage: ExecutionMetrics['resourceUsage'];
  customMetrics: Record<string, number>;
}

export interface ExecutionLog {
  timestamp: Date;
  level: 'debug' | 'info' | 'warn' | 'error';
  stage?: string;
  message: string;
  data?: any;
}

export interface ExecutionError {
  timestamp: Date;
  stage: string;
  type: string;
  message: string;
  stack?: string;
  recoverable: boolean;
}

export interface ExecutionContext {
  environment: Record<string, string>;
  parameters: Record<string, any>;
  resources: Record<string, any>;
  triggers: EventTrigger[];
}

// Main orchestrator
export class DataPipelineOrchestrator extends EventEmitter {
  private pipelines = new Map<string, Pipeline>();
  private executions = new Map<string, PipelineExecution>();
  private scheduledJobs = new Map<string, NodeJS.Timeout>();
  private isRunning = false;
  
  // Dependencies
  private marketDataManager: MarketDataManager;
  private dataValidator: DataValidator;
  private strategyExecutor: StrategyExecutor;
  private performanceMonitor: PerformanceMonitor;
  private alertSystem: AlertSystem;

  constructor(
    marketDataManager: MarketDataManager,
    dataValidator: DataValidator,
    strategyExecutor: StrategyExecutor,
    performanceMonitor: PerformanceMonitor,
    alertSystem: AlertSystem
  ) {
    super();
    this.marketDataManager = marketDataManager;
    this.dataValidator = dataValidator;
    this.strategyExecutor = strategyExecutor;
    this.performanceMonitor = performanceMonitor;
    this.alertSystem = alertSystem;
    
    this.setupEventListeners();
  }

  /**
   * Start the orchestrator
   */
  start(): void {
    if (this.isRunning) {
      console.warn('Orchestrator is already running');
      return;
    }

    this.isRunning = true;
    console.log('Starting data pipeline orchestrator...');
    
    // Start scheduled pipelines
    this.startScheduledPipelines();
    
    this.emit('started');
  }

  /**
   * Stop the orchestrator
   */
  stop(): void {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;
    console.log('Stopping data pipeline orchestrator...');
    
    // Stop all scheduled jobs
    for (const job of this.scheduledJobs.values()) {
      clearTimeout(job);
    }
    this.scheduledJobs.clear();
    
    // Cancel running executions
    for (const execution of this.executions.values()) {
      if (execution.status === 'running') {
        this.cancelExecution(execution.id);
      }
    }
    
    this.emit('stopped');
  }

  /**
   * Create a new pipeline
   */
  createPipeline(pipeline: Omit<Pipeline, 'id' | 'createdAt' | 'updatedAt'>): string {
    const id = `pipeline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const fullPipeline: Pipeline = {
      id,
      createdAt: new Date(),
      updatedAt: new Date(),
      ...pipeline
    };

    this.pipelines.set(id, fullPipeline);
    
    // Schedule pipeline if needed
    if (fullPipeline.schedule?.enabled && this.isRunning) {
      this.schedulePipeline(fullPipeline);
    }
    
    this.emit('pipelineCreated', fullPipeline);
    return id;
  }

  /**
   * Update pipeline
   */
  updatePipeline(id: string, updates: Partial<Pipeline>): void {
    const pipeline = this.pipelines.get(id);
    if (!pipeline) {
      throw new Error(`Pipeline ${id} not found`);
    }

    // Clear existing schedule
    const existingJob = this.scheduledJobs.get(id);
    if (existingJob) {
      clearTimeout(existingJob);
      this.scheduledJobs.delete(id);
    }

    // Apply updates
    Object.assign(pipeline, updates, { updatedAt: new Date() });
    
    // Reschedule if needed
    if (pipeline.schedule?.enabled && this.isRunning) {
      this.schedulePipeline(pipeline);
    }
    
    this.emit('pipelineUpdated', pipeline);
  }

  /**
   * Delete pipeline
   */
  deletePipeline(id: string): void {
    const pipeline = this.pipelines.get(id);
    if (!pipeline) {
      throw new Error(`Pipeline ${id} not found`);
    }

    // Clear schedule
    const job = this.scheduledJobs.get(id);
    if (job) {
      clearTimeout(job);
      this.scheduledJobs.delete(id);
    }

    // Cancel running executions
    for (const execution of this.executions.values()) {
      if (execution.pipelineId === id && execution.status === 'running') {
        this.cancelExecution(execution.id);
      }
    }

    this.pipelines.delete(id);
    this.emit('pipelineDeleted', id);
  }

  /**
   * Execute pipeline manually
   */
  async executePipeline(
    pipelineId: string, 
    context?: Partial<ExecutionContext>,
    triggeredBy: string = 'manual'
  ): Promise<string> {
    const pipeline = this.pipelines.get(pipelineId);
    if (!pipeline) {
      throw new Error(`Pipeline ${pipelineId} not found`);
    }

    if (pipeline.status !== 'active' && pipeline.status !== 'draft') {
      throw new Error(`Pipeline ${pipelineId} is not in executable state: ${pipeline.status}`);
    }

    const executionId = `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const execution: PipelineExecution = {
      id: executionId,
      pipelineId,
      status: 'pending',
      startTime: new Date(),
      stages: pipeline.stages.map(stage => ({
        stageId: stage.id,
        status: 'pending',
        retryCount: 0,
        metrics: this.getInitialStageMetrics()
      })),
      metrics: this.getInitialExecutionMetrics(),
      logs: [],
      errors: [],
      triggeredBy,
      context: {
        environment: {},
        parameters: {},
        resources: {},
        triggers: [],
        ...context
      }
    };

    this.executions.set(executionId, execution);
    this.emit('executionStarted', execution);

    // Start execution asynchronously
    this.runExecution(execution).catch(error => {
      console.error(`Pipeline execution ${executionId} failed:`, error);
    });

    return executionId;
  }

  /**
   * Cancel pipeline execution
   */
  cancelExecution(executionId: string): void {
    const execution = this.executions.get(executionId);
    if (!execution) {
      throw new Error(`Execution ${executionId} not found`);
    }

    if (execution.status === 'running') {
      execution.status = 'cancelled';
      execution.endTime = new Date();
      execution.duration = execution.endTime.getTime() - execution.startTime.getTime();
      
      this.emit('executionCancelled', execution);
    }
  }

  /**
   * Get pipeline by ID
   */
  getPipeline(id: string): Pipeline | undefined {
    return this.pipelines.get(id);
  }

  /**
   * Get all pipelines
   */
  getPipelines(filter?: {
    status?: PipelineStatus[];
    tags?: string[];
    owner?: string;
  }): Pipeline[] {
    let pipelines = Array.from(this.pipelines.values());

    if (filter?.status) {
      pipelines = pipelines.filter(p => filter.status!.includes(p.status));
    }

    if (filter?.tags) {
      pipelines = pipelines.filter(p => 
        filter.tags!.some(tag => p.metadata.tags.includes(tag))
      );
    }

    if (filter?.owner) {
      pipelines = pipelines.filter(p => p.metadata.owner === filter.owner);
    }

    return pipelines;
  }

  /**
   * Get execution by ID
   */
  getExecution(id: string): PipelineExecution | undefined {
    return this.executions.get(id);
  }

  /**
   * Get executions for a pipeline
   */
  getPipelineExecutions(pipelineId: string, limit?: number): PipelineExecution[] {
    const executions = Array.from(this.executions.values())
      .filter(e => e.pipelineId === pipelineId)
      .sort((a, b) => b.startTime.getTime() - a.startTime.getTime());

    return limit ? executions.slice(0, limit) : executions;
  }

  /**
   * Get pipeline statistics
   */
  getPipelineStats(pipelineId: string): {
    totalExecutions: number;
    successfulExecutions: number;
    failedExecutions: number;
    averageDuration: number;
    lastExecution?: Date;
    successRate: number;
  } {
    const executions = this.getPipelineExecutions(pipelineId);
    const successful = executions.filter(e => e.status === 'completed');
    const failed = executions.filter(e => e.status === 'failed');
    
    const durations = executions
      .filter(e => e.duration)
      .map(e => e.duration!);
    
    const averageDuration = durations.length > 0 
      ? durations.reduce((sum, d) => sum + d, 0) / durations.length 
      : 0;

    return {
      totalExecutions: executions.length,
      successfulExecutions: successful.length,
      failedExecutions: failed.length,
      averageDuration,
      lastExecution: executions[0]?.startTime,
      successRate: executions.length > 0 ? (successful.length / executions.length) * 100 : 0
    };
  }

  // Private methods
  private async runExecution(execution: PipelineExecution): Promise<void> {
    const pipeline = this.pipelines.get(execution.pipelineId);
    if (!pipeline) {
      throw new Error(`Pipeline ${execution.pipelineId} not found`);
    }

    execution.status = 'running';
    this.log(execution, 'info', `Starting pipeline execution: ${pipeline.name}`);

    try {
      // Build execution graph
      const sortedStages = this.sortStagesByDependencies(pipeline.stages);
      
      if (pipeline.configuration.parallelExecution) {
        await this.runStagesInParallel(execution, sortedStages, pipeline);
      } else {
        await this.runStagesSequentially(execution, sortedStages, pipeline);
      }

      execution.status = 'completed';
      this.log(execution, 'info', 'Pipeline execution completed successfully');
      
    } catch (error) {
      execution.status = 'failed';
      this.logError(execution, '', 'Pipeline execution failed', error as Error);
      
      if (pipeline.configuration.enableAlerts) {
        await this.alertSystem.alertCritical(
          'Pipeline Execution Failed',
          `Pipeline "${pipeline.name}" execution failed: ${(error as Error).message}`,
          'orchestrator',
          { pipelineId: pipeline.id, executionId: execution.id }
        );
      }
    } finally {
      execution.endTime = new Date();
      execution.duration = execution.endTime.getTime() - execution.startTime.getTime();
      
      // Calculate final metrics
      execution.metrics = this.calculateExecutionMetrics(execution);
      
      this.emit('executionCompleted', execution);
    }
  }

  private async runStagesSequentially(
    execution: PipelineExecution,
    stages: PipelineStage[],
    pipeline: Pipeline
  ): Promise<void> {
    for (const stage of stages) {
      if (execution.status === 'cancelled') {
        break;
      }

      if (!stage.enabled) {
        this.log(execution, 'info', `Skipping disabled stage: ${stage.name}`, stage.id);
        continue;
      }

      // Check stage condition
      if (!this.evaluateStageCondition(stage, execution)) {
        this.log(execution, 'info', `Skipping stage due to condition: ${stage.name}`, stage.id);
        continue;
      }

      await this.runStage(execution, stage, pipeline);

      // Check error handling policy
      const stageExecution = execution.stages.find(s => s.stageId === stage.id);
      if (stageExecution?.status === 'failed') {
        if (pipeline.configuration.errorHandling === 'stop') {
          throw new Error(`Stage ${stage.name} failed, stopping pipeline`);
        } else if (pipeline.configuration.errorHandling === 'retry') {
          // Retry logic is handled in runStage
        }
        // 'continue' - just continue to next stage
      }
    }
  }

  private async runStagesInParallel(
    execution: PipelineExecution,
    stages: PipelineStage[],
    pipeline: Pipeline
  ): Promise<void> {
    const maxConcurrent = pipeline.configuration.maxConcurrentStages;
    const running = new Set<Promise<void>>();
    const completed = new Set<string>();
    
    while (completed.size < stages.length && execution.status !== 'cancelled') {
      // Find stages that can run (dependencies met, not yet completed)
      const runnableStages = stages.filter(stage => 
        !completed.has(stage.id) &&
        stage.enabled &&
        stage.dependencies.every(depId => completed.has(depId)) &&
        this.evaluateStageCondition(stage, execution)
      );

      // Start stages up to concurrent limit
      for (const stage of runnableStages) {
        if (running.size >= maxConcurrent) {
          break;
        }

        const stagePromise = this.runStage(execution, stage, pipeline)
          .then(() => {
            completed.add(stage.id);
            running.delete(stagePromise);
          })
          .catch(error => {
            running.delete(stagePromise);
            if (pipeline.configuration.errorHandling === 'stop') {
              execution.status = 'failed';
              throw error;
            }
          });

        running.add(stagePromise);
      }

      // Wait for at least one stage to complete
      if (running.size > 0) {
        await Promise.race(running);
      } else {
        break; // No more stages to run
      }
    }

    // Wait for all remaining stages to complete
    await Promise.all(running);
  }

  private async runStage(
    execution: PipelineExecution,
    stage: PipelineStage,
    pipeline: Pipeline
  ): Promise<void> {
    const stageExecution = execution.stages.find(s => s.stageId === stage.id);
    if (!stageExecution) return;

    stageExecution.status = 'running';
    stageExecution.startTime = new Date();
    
    this.log(execution, 'info', `Starting stage: ${stage.name}`, stage.id);

    try {
      const result = await this.executeStage(execution, stage);
      
      stageExecution.status = 'completed';
      stageExecution.output = result;
      
      this.log(execution, 'info', `Stage completed successfully: ${stage.name}`, stage.id);
      
    } catch (error) {
      stageExecution.error = (error as Error).message;
      
      // Apply retry policy
      if (stage.retryPolicy && stageExecution.retryCount < stage.retryPolicy.maxRetries) {
        stageExecution.retryCount++;
        
        const backoffMs = Math.min(
          stage.retryPolicy.backoffMs * Math.pow(2, stageExecution.retryCount - 1),
          stage.retryPolicy.maxBackoffMs
        );
        
        this.log(execution, 'warn', 
          `Stage failed, retrying in ${backoffMs}ms (attempt ${stageExecution.retryCount}/${stage.retryPolicy.maxRetries}): ${stage.name}`,
          stage.id
        );
        
        await new Promise(resolve => setTimeout(resolve, backoffMs));
        return this.runStage(execution, stage, pipeline); // Recursive retry
      }
      
      stageExecution.status = 'failed';
      this.logError(execution, stage.id, `Stage failed: ${stage.name}`, error as Error);
      
      throw error;
    } finally {
      stageExecution.endTime = new Date();
      stageExecution.duration = stageExecution.endTime.getTime() - (stageExecution.startTime?.getTime() || 0);
      stageExecution.metrics = this.calculateStageMetrics(stageExecution);
    }
  }

  private async executeStage(execution: PipelineExecution, stage: PipelineStage): Promise<any> {
    const timeout = stage.timeout || 300000; // 5 minutes default
    
    return Promise.race([
      this.doExecuteStage(execution, stage),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error(`Stage timeout after ${timeout}ms`)), timeout)
      )
    ]);
  }

  private async doExecuteStage(execution: PipelineExecution, stage: PipelineStage): Promise<any> {
    switch (stage.type) {
      case 'data_ingestion':
        return this.executeDataIngestion(execution, stage);
      case 'data_validation':
        return this.executeDataValidation(execution, stage);
      case 'strategy_execution':
        return this.executeStrategyExecution(execution, stage);
      case 'monitoring':
        return this.executeMonitoring(execution, stage);
      case 'notification':
        return this.executeNotification(execution, stage);
      case 'custom':
        return this.executeCustomStage(execution, stage);
      default:
        throw new Error(`Unsupported stage type: ${stage.type}`);
    }
  }

  private async executeDataIngestion(execution: PipelineExecution, stage: PipelineStage): Promise<MarketDataPoint[]> {
    const config = stage.configuration;
    const data: MarketDataPoint[] = [];

    if (config.symbols && config.timeframes) {
      for (const symbol of config.symbols) {
        for (const timeframe of config.timeframes) {
          try {
            await this.marketDataManager.subscribe(symbol, timeframe);
            this.log(execution, 'info', `Subscribed to ${symbol} ${timeframe}`, stage.id);
          } catch (error) {
            this.logError(execution, stage.id, `Failed to subscribe to ${symbol} ${timeframe}`, error as Error);
          }
        }
      }
    }

    return data;
  }

  private async executeDataValidation(execution: PipelineExecution, stage: PipelineStage): Promise<ValidationResult[]> {
    const config = stage.configuration;
    const results: ValidationResult[] = [];

    // Get data from previous stages or context
    const data = execution.context.resources.marketData as MarketDataPoint[] || [];
    
    if (data.length > 0) {
      const validationResult = this.dataValidator.validateBatch(data);
      results.push(validationResult);

      // Check quality thresholds
      if (config.qualityThresholds) {
        for (const [metric, threshold] of Object.entries(config.qualityThresholds)) {
          if (validationResult.score < threshold) {
            throw new Error(`Data quality ${metric} below threshold: ${validationResult.score} < ${threshold}`);
          }
        }
      }
    }

    return results;
  }

  private async executeStrategyExecution(execution: PipelineExecution, stage: PipelineStage): Promise<string[]> {
    const config = stage.configuration;
    const executionIds: string[] = [];

    if (config.strategies) {
      for (const strategyId of config.strategies) {
        try {
          // This would need actual strategy loading logic
          this.log(execution, 'info', `Executing strategy: ${strategyId}`, stage.id);
          // executionIds.push(await this.strategyExecutor.startExecution(...));
        } catch (error) {
          this.logError(execution, stage.id, `Failed to execute strategy ${strategyId}`, error as Error);
        }
      }
    }

    return executionIds;
  }

  private async executeMonitoring(execution: PipelineExecution, stage: PipelineStage): Promise<any> {
    const config = stage.configuration;
    
    // Collect current metrics
    const currentMetrics = this.performanceMonitor.getCurrentMetrics();
    
    // Check thresholds
    if (config.alertThresholds && currentMetrics) {
      for (const [metric, threshold] of Object.entries(config.alertThresholds)) {
        // This would need metric path evaluation logic
        this.log(execution, 'info', `Checking metric ${metric} against threshold ${threshold}`, stage.id);
      }
    }

    return currentMetrics;
  }

  private async executeNotification(execution: PipelineExecution, stage: PipelineStage): Promise<void> {
    const config = stage.configuration;
    
    if (config.notificationChannels) {
      await this.alertSystem.alertInfo(
        'Pipeline Stage Completed',
        `Stage "${stage.name}" completed successfully`,
        'orchestrator',
        { pipelineId: execution.pipelineId, executionId: execution.id, stage: stage.id }
      );
    }
  }

  private async executeCustomStage(execution: PipelineExecution, stage: PipelineStage): Promise<any> {
    const config = stage.configuration;
    
    if (config.command) {
      // Execute custom command/script
      this.log(execution, 'info', `Executing custom command: ${config.command}`, stage.id);
      // This would need actual command execution logic
      return { success: true };
    }

    throw new Error('Custom stage requires command configuration');
  }

  private evaluateStageCondition(stage: PipelineStage, execution: PipelineExecution): boolean {
    if (!stage.condition) return true;

    switch (stage.condition.type) {
      case 'always':
        return true;
      case 'success':
        return execution.stages.every(s => s.status === 'completed' || s.status === 'pending');
      case 'failure':
        return execution.stages.some(s => s.status === 'failed');
      case 'custom':
        if (stage.condition.expression) {
          try {
            const func = new Function('execution', `return ${stage.condition.expression}`);
            return Boolean(func(execution));
          } catch (error) {
            console.error(`Error evaluating stage condition: ${error}`);
            return false;
          }
        }
        return true;
      default:
        return true;
    }
  }

  private sortStagesByDependencies(stages: PipelineStage[]): PipelineStage[] {
    const sorted: PipelineStage[] = [];
    const visited = new Set<string>();
    const visiting = new Set<string>();

    const visit = (stage: PipelineStage) => {
      if (visiting.has(stage.id)) {
        throw new Error(`Circular dependency detected: ${stage.id}`);
      }

      if (visited.has(stage.id)) {
        return;
      }

      visiting.add(stage.id);

      for (const depId of stage.dependencies) {
        const dep = stages.find(s => s.id === depId);
        if (dep) {
          visit(dep);
        }
      }

      visiting.delete(stage.id);
      visited.add(stage.id);
      sorted.push(stage);
    };

    for (const stage of stages) {
      if (!visited.has(stage.id)) {
        visit(stage);
      }
    }

    return sorted;
  }

  private schedulePipeline(pipeline: Pipeline): void {
    if (!pipeline.schedule) return;

    const schedule = pipeline.schedule;
    let nextRun: Date;

    switch (schedule.type) {
      case 'interval':
        if (schedule.intervalMs) {
          const job = setInterval(() => {
            this.executePipeline(pipeline.id, {}, 'scheduled').catch(error => {
              console.error(`Scheduled pipeline execution failed: ${error}`);
            });
          }, schedule.intervalMs);
          
          this.scheduledJobs.set(pipeline.id, job as any);
          nextRun = new Date(Date.now() + schedule.intervalMs);
        }
        break;

      case 'cron':
        // Cron scheduling would require a cron library
        console.log(`Cron scheduling not implemented: ${schedule.cronExpression}`);
        break;

      case 'event':
        // Event-based scheduling
        if (schedule.eventTriggers) {
          for (const trigger of schedule.eventTriggers) {
            this.setupEventTrigger(pipeline, trigger);
          }
        }
        break;
    }

    if (nextRun!) {
      pipeline.nextRun = nextRun;
    }
  }

  private setupEventTrigger(pipeline: Pipeline, trigger: EventTrigger): void {
    // Set up event listener based on trigger configuration
    const listener = (data: any) => {
      if (trigger.condition) {
        try {
          const func = new Function('data', `return ${trigger.condition}`);
          if (!func(data)) return;
        } catch (error) {
          console.error(`Error evaluating event trigger condition: ${error}`);
          return;
        }
      }

      this.executePipeline(pipeline.id, { triggers: [trigger] }, 'event').catch(error => {
        console.error(`Event-triggered pipeline execution failed: ${error}`);
      });
    };

    // This would need proper event source integration
    this.on(trigger.event, listener);
  }

  private startScheduledPipelines(): void {
    for (const pipeline of this.pipelines.values()) {
      if (pipeline.schedule?.enabled && pipeline.status === 'active') {
        this.schedulePipeline(pipeline);
      }
    }
  }

  private setupEventListeners(): void {
    // Listen for relevant events from other systems
    this.marketDataManager.on('marketData', (data: MarketDataPoint) => {
      this.emit('marketDataReceived', data);
    });

    this.strategyExecutor.on('executionCompleted', (execution: any) => {
      this.emit('strategyExecutionCompleted', execution);
    });

    this.performanceMonitor.on('alert', (alert: any) => {
      this.emit('performanceAlert', alert);
    });
  }

  private log(execution: PipelineExecution, level: ExecutionLog['level'], message: string, stage?: string): void {
    const log: ExecutionLog = {
      timestamp: new Date(),
      level,
      stage,
      message
    };

    execution.logs.push(log);
    console.log(`[${level.toUpperCase()}] ${stage || 'Pipeline'}: ${message}`);
  }

  private logError(execution: PipelineExecution, stage: string, message: string, error: Error): void {
    const executionError: ExecutionError = {
      timestamp: new Date(),
      stage,
      type: error.constructor.name,
      message: error.message,
      stack: error.stack,
      recoverable: true
    };

    execution.errors.push(executionError);
    this.log(execution, 'error', message, stage);
  }

  private getInitialExecutionMetrics(): ExecutionMetrics {
    return {
      dataProcessed: 0,
      recordsProcessed: 0,
      errorsEncountered: 0,
      performanceScore: 100,
      resourceUsage: {
        cpu: 0,
        memory: 0,
        network: 0,
        storage: 0
      }
    };
  }

  private getInitialStageMetrics(): StageMetrics {
    return {
      executionTime: 0,
      throughput: 0,
      errorRate: 0,
      resourceUsage: {
        cpu: 0,
        memory: 0,
        network: 0,
        storage: 0
      },
      customMetrics: {}
    };
  }

  private calculateExecutionMetrics(execution: PipelineExecution): ExecutionMetrics {
    // Aggregate metrics from all stages
    const metrics = this.getInitialExecutionMetrics();
    
    for (const stage of execution.stages) {
      metrics.dataProcessed += stage.metrics.resourceUsage.storage;
      metrics.recordsProcessed += stage.metrics.customMetrics.recordsProcessed || 0;
      metrics.errorsEncountered += stage.error ? 1 : 0;
    }

    metrics.performanceScore = Math.max(0, 100 - (metrics.errorsEncountered * 10));
    
    return metrics;
  }

  private calculateStageMetrics(stageExecution: StageExecution): StageMetrics {
    return {
      executionTime: stageExecution.duration || 0,
      throughput: 0, // Would be calculated based on actual throughput
      errorRate: stageExecution.error ? 100 : 0,
      resourceUsage: {
        cpu: Math.random() * 100, // Mock values
        memory: Math.random() * 1024 * 1024 * 1024,
        network: Math.random() * 1024 * 1024,
        storage: Math.random() * 1024 * 1024
      },
      customMetrics: {}
    };
  }
}