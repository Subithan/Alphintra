import { Node, Edge } from 'reactflow';
import { RealTimeExecutionEngine, ExecutionResult, MarketData } from './execution-engine';
import { MultiTimeframeEngine, MultiTimeframeExecutionResult, TimeframeConfig } from './multi-timeframe-engine';
import { AdvancedRiskManager, RiskManagerConfig, PositionSizeCalculation } from './advanced-risk-manager';
import { PortfolioOrchestrator, PortfolioConfig, StrategyConfig } from './portfolio-orchestrator';
import { MLOptimizationEngine, MLOptimizationConfig, OptimizationResult } from './ml-optimization-engine';
import { RealTimeDataEngine, DataProviderConfig, SubscriptionConfig } from './real-time-data-engine';
import { BacktestingEngine, BacktestConfig, BacktestResult } from './backtesting-engine';

export interface OrchestrationConfig {
  orchestration_id: string;
  mode: 'development' | 'testing' | 'paper_trading' | 'live_trading';
  auto_optimization: boolean;
  auto_rebalancing: boolean;
  risk_management_enabled: boolean;
  multi_timeframe_enabled: boolean;
  real_time_data_enabled: boolean;
  performance_monitoring: boolean;
  alert_notifications: boolean;
  backup_strategies: boolean;
}

export interface StrategyInstance {
  instance_id: string;
  strategy_name: string;
  nodes: Node[];
  edges: Edge[];
  config: StrategyInstanceConfig;
  status: 'inactive' | 'initializing' | 'running' | 'paused' | 'error' | 'optimizing';
  engines: {
    execution?: RealTimeExecutionEngine;
    multiTimeframe?: MultiTimeframeEngine;
    backtesting?: BacktestingEngine;
    mlOptimization?: MLOptimizationEngine;
  };
  performance: StrategyPerformance;
  last_execution: Date | null;
  error_message?: string;
}

export interface StrategyInstanceConfig {
  execution_config: any;
  timeframe_config?: TimeframeConfig;
  backtest_config?: BacktestConfig;
  ml_optimization_config?: MLOptimizationConfig;
  symbols: string[];
  enabled: boolean;
  priority: number;
  resource_allocation: number; // 0-1, percentage of system resources
}

export interface StrategyPerformance {
  total_executions: number;
  successful_executions: number;
  error_count: number;
  avg_execution_time_ms: number;
  last_signal_time: Date | null;
  signals_generated: number;
  current_positions: number;
  total_pnl: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

export interface OrchestrationState {
  status: 'stopped' | 'starting' | 'running' | 'pausing' | 'stopped_error';
  active_strategies: number;
  total_strategies: number;
  system_health: SystemHealth;
  resource_usage: ResourceUsage;
  performance_summary: PerformanceSummary;
  alerts: OrchestrationAlert[];
  last_update: Date;
}

export interface SystemHealth {
  overall_status: 'healthy' | 'warning' | 'critical';
  data_connectivity: 'connected' | 'degraded' | 'disconnected';
  execution_engine: 'operational' | 'degraded' | 'failed';
  risk_management: 'active' | 'warning' | 'disabled';
  portfolio_manager: 'operational' | 'warning' | 'error';
  memory_usage: number; // 0-100 percentage
  cpu_usage: number; // 0-100 percentage
  latency_ms: number;
  uptime_seconds: number;
}

export interface ResourceUsage {
  total_memory_mb: number;
  used_memory_mb: number;
  cpu_utilization: number;
  active_connections: number;
  data_throughput_mbps: number;
  execution_queue_size: number;
  strategy_load_distribution: Record<string, number>;
}

export interface PerformanceSummary {
  total_signals: number;
  total_executions: number;
  success_rate: number;
  avg_latency_ms: number;
  portfolio_value: number;
  total_pnl: number;
  daily_pnl: number;
  portfolio_sharpe: number;
  max_portfolio_drawdown: number;
  active_positions: number;
}

export interface OrchestrationAlert {
  alert_id: string;
  timestamp: Date;
  severity: 'info' | 'warning' | 'error' | 'critical';
  category: 'system' | 'strategy' | 'risk' | 'performance' | 'data';
  source: string; // Strategy ID or system component
  message: string;
  details: any;
  acknowledged: boolean;
  auto_resolved: boolean;
  resolution_action?: string;
}

export interface ExecutionPipeline {
  pipeline_id: string;
  steps: PipelineStep[];
  current_step: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  start_time: Date;
  end_time?: Date;
  results: Map<string, any>;
  errors: string[];
}

export interface PipelineStep {
  step_id: string;
  step_type: 'data_fetch' | 'execution' | 'risk_check' | 'optimization' | 'portfolio_update';
  strategy_id?: string;
  dependencies: string[];
  parallel_execution: boolean;
  timeout_ms: number;
  retry_count: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  result?: any;
  error?: string;
  execution_time_ms?: number;
}

export class StrategyOrchestrationEngine {
  private config: OrchestrationConfig;
  private strategies: Map<string, StrategyInstance> = new Map();
  private portfolioOrchestrator: PortfolioOrchestrator;
  private riskManager: AdvancedRiskManager;
  private dataEngine: RealTimeDataEngine;
  private state: OrchestrationState;
  private executionPipelines: Map<string, ExecutionPipeline> = new Map();
  private performanceMonitor: PerformanceMonitor;
  private alertManager: AlertManager;
  private resourceManager: ResourceManager;
  private isRunning = false;
  private mainLoop: NodeJS.Timeout | null = null;

  constructor(
    config: OrchestrationConfig,
    portfolioConfig: PortfolioConfig,
    riskConfig: RiskManagerConfig,
    dataProviders: Map<string, DataProviderConfig>
  ) {
    this.config = config;
    
    // Initialize core systems
    this.portfolioOrchestrator = new PortfolioOrchestrator(portfolioConfig);
    this.riskManager = new AdvancedRiskManager(riskConfig, this.portfolioOrchestrator.getPortfolioState());
    this.dataEngine = new RealTimeDataEngine();
    
    // Initialize management systems
    this.performanceMonitor = new PerformanceMonitor();
    this.alertManager = new AlertManager();
    this.resourceManager = new ResourceManager();
    
    // Initialize state
    this.state = this.initializeState();
    
    // Setup data providers
    dataProviders.forEach((providerConfig, providerId) => {
      this.dataEngine.addProvider(providerId, providerConfig);
    });
    
    // Setup event listeners
    this.setupEventListeners();
    
    console.log(`Strategy Orchestration Engine initialized in ${config.mode} mode`);
  }

  private initializeState(): OrchestrationState {
    return {
      status: 'stopped',
      active_strategies: 0,
      total_strategies: 0,
      system_health: {
        overall_status: 'healthy',
        data_connectivity: 'disconnected',
        execution_engine: 'operational',
        risk_management: 'active',
        portfolio_manager: 'operational',
        memory_usage: 0,
        cpu_usage: 0,
        latency_ms: 0,
        uptime_seconds: 0
      },
      resource_usage: {
        total_memory_mb: 0,
        used_memory_mb: 0,
        cpu_utilization: 0,
        active_connections: 0,
        data_throughput_mbps: 0,
        execution_queue_size: 0,
        strategy_load_distribution: {}
      },
      performance_summary: {
        total_signals: 0,
        total_executions: 0,
        success_rate: 0,
        avg_latency_ms: 0,
        portfolio_value: 0,
        total_pnl: 0,
        daily_pnl: 0,
        portfolio_sharpe: 0,
        max_portfolio_drawdown: 0,
        active_positions: 0
      },
      alerts: [],
      last_update: new Date()
    };
  }

  private setupEventListeners(): void {
    // Data engine events
    this.dataEngine.addEventListener('data', (data) => {
      this.handleMarketData(data);
    });

    this.dataEngine.addEventListener('connection', (event) => {
      this.handleConnectionEvent(event);
    });

    this.dataEngine.addEventListener('error', (error) => {
      this.handleDataError(error);
    });

    // Risk manager events
    // Portfolio orchestrator events
    // Performance monitoring events
  }

  public async addStrategy(
    strategyId: string,
    strategyName: string,
    nodes: Node[],
    edges: Edge[],
    config: StrategyInstanceConfig
  ): Promise<void> {
    try {
      // Validate strategy
      this.validateStrategy(nodes, edges, config);

      // Create strategy instance
      const instance: StrategyInstance = {
        instance_id: strategyId,
        strategy_name: strategyName,
        nodes,
        edges,
        config,
        status: 'inactive',
        engines: {},
        performance: this.initializeStrategyPerformance(),
        last_execution: null
      };

      // Initialize engines based on configuration
      await this.initializeStrategyEngines(instance);

      // Add to portfolio orchestrator
      const portfolioStrategy: StrategyConfig = {
        strategy_id: strategyId,
        strategy_name: strategyName,
        nodes,
        edges,
        allocation_percentage: 0, // Will be set during optimization
        risk_budget: 0.1, // Default 10% risk budget
        priority: 'medium',
        active: config.enabled,
        constraints: {
          max_position_size: 10000,
          max_daily_trades: 50,
          max_drawdown: 0.2,
          correlation_limit: 0.7,
          sector_exposure_limit: {},
          instrument_limits: {}
        },
        performance_targets: {
          target_sharpe_ratio: 1.5,
          target_annual_return: 15,
          max_acceptable_drawdown: 20,
          min_win_rate: 55,
          rebalancing_frequency: 'daily'
        }
      };

      this.portfolioOrchestrator.addStrategy(portfolioStrategy);

      // Store strategy
      this.strategies.set(strategyId, instance);
      
      // Update state
      this.state.total_strategies = this.strategies.size;
      
      // Subscribe to market data
      if (this.config.real_time_data_enabled) {
        await this.subscribeToMarketData(strategyId, config.symbols);
      }

      this.createAlert({
        severity: 'info',
        category: 'strategy',
        source: strategyId,
        message: `Strategy ${strategyName} added successfully`
      });

      console.log(`Strategy ${strategyId} added to orchestration engine`);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      this.createAlert({
        severity: 'error',
        category: 'strategy',
        source: strategyId,
        message: `Failed to add strategy: ${errorMessage}`
      });
      throw error;
    }
  }

  private validateStrategy(nodes: Node[], edges: Edge[], config: StrategyInstanceConfig): void {
    if (nodes.length === 0) {
      throw new Error('Strategy must have at least one node');
    }

    if (config.symbols.length === 0) {
      throw new Error('Strategy must specify at least one symbol');
    }

    // Check for required node types
    const hasDataSource = nodes.some(n => n.type === 'dataSource');
    const hasAction = nodes.some(n => n.type === 'action');
    
    if (!hasDataSource) {
      throw new Error('Strategy must have at least one data source');
    }
    
    if (!hasAction) {
      throw new Error('Strategy must have at least one action node');
    }

    // Validate resource allocation
    if (config.resource_allocation <= 0 || config.resource_allocation > 1) {
      throw new Error('Resource allocation must be between 0 and 1');
    }
  }

  private async initializeStrategyEngines(instance: StrategyInstance): Promise<void> {
    const { config, nodes, edges } = instance;

    // Initialize execution engine
    instance.engines.execution = new RealTimeExecutionEngine(
      config.execution_config,
      nodes,
      edges
    );

    // Initialize multi-timeframe engine if configured
    if (this.config.multi_timeframe_enabled && config.timeframe_config) {
      instance.engines.multiTimeframe = new MultiTimeframeEngine(
        config.timeframe_config,
        nodes,
        edges
      );
    }

    // Initialize backtesting engine if configured
    if (config.backtest_config) {
      instance.engines.backtesting = new BacktestingEngine(
        config.backtest_config,
        nodes,
        edges
      );
    }

    // Initialize ML optimization engine if configured
    if (this.config.auto_optimization && config.ml_optimization_config) {
      instance.engines.mlOptimization = new MLOptimizationEngine(
        config.ml_optimization_config,
        nodes,
        edges,
        [] // Historical data will be provided later
      );
    }
  }

  private initializeStrategyPerformance(): StrategyPerformance {
    return {
      total_executions: 0,
      successful_executions: 0,
      error_count: 0,
      avg_execution_time_ms: 0,
      last_signal_time: null,
      signals_generated: 0,
      current_positions: 0,
      total_pnl: 0,
      win_rate: 0,
      sharpe_ratio: 0,
      max_drawdown: 0
    };
  }

  private async subscribeToMarketData(strategyId: string, symbols: string[]): Promise<void> {
    const subscriptionConfig: SubscriptionConfig = {
      symbols,
      data_types: ['trades', 'quotes', 'bars'],
      timeframes: ['1m', '5m', '1h'],
      quality_level: 'premium',
      buffer_size: 1000,
      persistence: true
    };

    await this.dataEngine.subscribe(strategyId, subscriptionConfig);
  }

  public async start(): Promise<void> {
    if (this.isRunning) {
      throw new Error('Orchestration engine is already running');
    }

    try {
      this.state.status = 'starting';
      
      // Connect to data providers
      if (this.config.real_time_data_enabled) {
        await this.connectToDataProviders();
      }

      // Initialize active strategies
      for (const [strategyId, instance] of this.strategies.entries()) {
        if (instance.config.enabled) {
          await this.startStrategy(strategyId);
        }
      }

      // Start main execution loop
      this.isRunning = true;
      this.state.status = 'running';
      this.startMainLoop();

      // Start performance monitoring
      this.performanceMonitor.start();

      this.createAlert({
        severity: 'info',
        category: 'system',
        source: 'orchestrator',
        message: 'Strategy orchestration engine started successfully'
      });

      console.log('Strategy Orchestration Engine started');

    } catch (error) {
      this.state.status = 'stopped_error';
      const errorMessage = error instanceof Error ? error.message : String(error);
      
      this.createAlert({
        severity: 'critical',
        category: 'system',
        source: 'orchestrator',
        message: `Failed to start orchestration engine: ${errorMessage}`
      });

      throw error;
    }
  }

  private async connectToDataProviders(): Promise<void> {
    // Connect to all configured data providers
    const connectionPromises: Promise<void>[] = [];
    
    for (const providerId of this.dataEngine.getConnectionStatus() as any) {
      connectionPromises.push(this.dataEngine.connectProvider(providerId));
    }

    try {
      await Promise.all(connectionPromises);
      this.state.system_health.data_connectivity = 'connected';
    } catch (error) {
      this.state.system_health.data_connectivity = 'degraded';
      console.error('Some data providers failed to connect:', error);
    }
  }

  private async startStrategy(strategyId: string): Promise<void> {
    const instance = this.strategies.get(strategyId);
    if (!instance) {
      throw new Error(`Strategy ${strategyId} not found`);
    }

    try {
      instance.status = 'initializing';

      // Validate strategy state
      if (!instance.engines.execution) {
        throw new Error('Execution engine not initialized');
      }

      // Pre-execution checks
      if (this.config.risk_management_enabled) {
        // Perform risk checks
        const riskCheck = await this.performRiskChecks(strategyId);
        if (!riskCheck.passed) {
          throw new Error(`Risk check failed: ${riskCheck.reason}`);
        }
      }

      // Mark as running
      instance.status = 'running';
      this.state.active_strategies++;

      this.createAlert({
        severity: 'info',
        category: 'strategy',
        source: strategyId,
        message: `Strategy ${instance.strategy_name} started`
      });

      console.log(`Strategy ${strategyId} started successfully`);

    } catch (error) {
      instance.status = 'error';
      instance.error_message = error instanceof Error ? error.message : String(error);
      
      this.createAlert({
        severity: 'error',
        category: 'strategy',
        source: strategyId,
        message: `Failed to start strategy: ${instance.error_message}`
      });

      throw error;
    }
  }

  private startMainLoop(): void {
    this.mainLoop = setInterval(async () => {
      try {
        await this.executeMainLoop();
      } catch (error) {
        console.error('Error in main execution loop:', error);
        this.handleSystemError(error);
      }
    }, 1000); // Execute every second
  }

  private async executeMainLoop(): Promise<void> {
    const startTime = performance.now();

    // Update system health
    await this.updateSystemHealth();

    // Execute active strategies
    await this.executeActiveStrategies();

    // Process portfolio-level operations
    if (this.config.auto_rebalancing) {
      await this.processPortfolioOperations();
    }

    // Perform risk monitoring
    if (this.config.risk_management_enabled) {
      await this.performRiskMonitoring();
    }

    // Run optimization if scheduled
    if (this.config.auto_optimization) {
      await this.processOptimization();
    }

    // Update performance metrics
    await this.updatePerformanceMetrics();

    // Process alerts
    await this.processAlerts();

    // Update state
    this.state.last_update = new Date();
    const executionTime = performance.now() - startTime;
    this.state.system_health.latency_ms = executionTime;
  }

  private async executeActiveStrategies(): Promise<void> {
    const activeStrategies = Array.from(this.strategies.entries())
      .filter(([_, instance]) => instance.status === 'running');

    if (activeStrategies.length === 0) return;

    // Create execution pipeline
    const pipeline = this.createExecutionPipeline(activeStrategies);
    
    try {
      await this.executePipeline(pipeline);
    } catch (error) {
      console.error('Strategy execution pipeline failed:', error);
    }
  }

  private createExecutionPipeline(strategies: [string, StrategyInstance][]): ExecutionPipeline {
    const pipelineId = `pipeline_${Date.now()}`;
    const steps: PipelineStep[] = [];

    // Data fetch step (parallel for all strategies)
    steps.push({
      step_id: 'data_fetch',
      step_type: 'data_fetch',
      dependencies: [],
      parallel_execution: true,
      timeout_ms: 5000,
      retry_count: 3,
      status: 'pending'
    });

    // Strategy execution steps (parallel)
    strategies.forEach(([strategyId, instance]) => {
      steps.push({
        step_id: `execution_${strategyId}`,
        step_type: 'execution',
        strategy_id: strategyId,
        dependencies: ['data_fetch'],
        parallel_execution: true,
        timeout_ms: 10000,
        retry_count: 2,
        status: 'pending'
      });

      // Risk check step for each strategy
      if (this.config.risk_management_enabled) {
        steps.push({
          step_id: `risk_check_${strategyId}`,
          step_type: 'risk_check',
          strategy_id: strategyId,
          dependencies: [`execution_${strategyId}`],
          parallel_execution: true,
          timeout_ms: 3000,
          retry_count: 1,
          status: 'pending'
        });
      }
    });

    // Portfolio update step (sequential, after all executions)
    const executionSteps = steps.filter(s => s.step_type === 'execution').map(s => s.step_id);
    steps.push({
      step_id: 'portfolio_update',
      step_type: 'portfolio_update',
      dependencies: executionSteps,
      parallel_execution: false,
      timeout_ms: 5000,
      retry_count: 2,
      status: 'pending'
    });

    return {
      pipeline_id: pipelineId,
      steps,
      current_step: 0,
      status: 'pending',
      start_time: new Date(),
      results: new Map(),
      errors: []
    };
  }

  private async executePipeline(pipeline: ExecutionPipeline): Promise<void> {
    pipeline.status = 'running';
    this.executionPipelines.set(pipeline.pipeline_id, pipeline);

    try {
      // Execute steps in dependency order
      const executeStep = async (step: PipelineStep): Promise<void> => {
        // Check dependencies
        const dependenciesCompleted = step.dependencies.every(depId => {
          const depStep = pipeline.steps.find(s => s.step_id === depId);
          return depStep?.status === 'completed';
        });

        if (!dependenciesCompleted) {
          step.status = 'skipped';
          return;
        }

        step.status = 'running';
        const stepStartTime = performance.now();

        try {
          let result: any;

          switch (step.step_type) {
            case 'data_fetch':
              result = await this.executeDataFetchStep();
              break;
            case 'execution':
              result = await this.executeStrategyStep(step.strategy_id!);
              break;
            case 'risk_check':
              result = await this.executeRiskCheckStep(step.strategy_id!);
              break;
            case 'portfolio_update':
              result = await this.executePortfolioUpdateStep();
              break;
            default:
              throw new Error(`Unknown step type: ${step.step_type}`);
          }

          step.result = result;
          step.status = 'completed';
          step.execution_time_ms = performance.now() - stepStartTime;
          pipeline.results.set(step.step_id, result);

        } catch (error) {
          step.error = error instanceof Error ? error.message : String(error);
          step.status = 'failed';
          pipeline.errors.push(`Step ${step.step_id}: ${step.error}`);
        }
      };

      // Group steps by execution order
      const stepGroups: PipelineStep[][] = [];
      const processed = new Set<string>();
      
      while (processed.size < pipeline.steps.length) {
        const currentGroup = pipeline.steps.filter(step => 
          !processed.has(step.step_id) &&
          step.dependencies.every(dep => processed.has(dep))
        );

        if (currentGroup.length === 0) {
          throw new Error('Circular dependency detected in pipeline');
        }

        stepGroups.push(currentGroup);
        currentGroup.forEach(step => processed.add(step.step_id));
      }

      // Execute step groups
      for (const group of stepGroups) {
        const parallelSteps = group.filter(s => s.parallel_execution);
        const sequentialSteps = group.filter(s => !s.parallel_execution);

        // Execute parallel steps
        if (parallelSteps.length > 0) {
          await Promise.all(parallelSteps.map(executeStep));
        }

        // Execute sequential steps
        for (const step of sequentialSteps) {
          await executeStep(step);
        }
      }

      pipeline.status = 'completed';
      pipeline.end_time = new Date();

    } catch (error) {
      pipeline.status = 'failed';
      pipeline.end_time = new Date();
      pipeline.errors.push(error instanceof Error ? error.message : String(error));
    }

    // Cleanup old pipelines
    this.cleanupOldPipelines();
  }

  private async executeDataFetchStep(): Promise<Map<string, MarketData[]>> {
    const marketDataMap = new Map<string, MarketData[]>();
    
    // Collect all symbols from active strategies
    const allSymbols = new Set<string>();
    this.strategies.forEach(instance => {
      if (instance.status === 'running') {
        instance.config.symbols.forEach(symbol => allSymbols.add(symbol));
      }
    });

    // Fetch latest data for each symbol
    for (const symbol of allSymbols) {
      try {
        const latestBars = this.dataEngine.getLatestBars(symbol, 100);
        if (latestBars.length > 0) {
          marketDataMap.set(symbol, latestBars);
        }
      } catch (error) {
        console.error(`Failed to fetch data for ${symbol}:`, error);
      }
    }

    return marketDataMap;
  }

  private async executeStrategyStep(strategyId: string): Promise<ExecutionResult> {
    const instance = this.strategies.get(strategyId);
    if (!instance || !instance.engines.execution) {
      throw new Error(`Strategy ${strategyId} not found or not initialized`);
    }

    try {
      // Get market data for this strategy
      const marketDataMap = new Map<string, MarketData[]>();
      instance.config.symbols.forEach(symbol => {
        const data = this.dataEngine.getLatestBars(symbol, 100);
        if (data.length > 0) {
          marketDataMap.set(symbol, data);
        }
      });

      // Execute strategy
      let result: ExecutionResult;
      
      if (instance.engines.multiTimeframe && this.config.multi_timeframe_enabled) {
        // Multi-timeframe execution
        const mtResult = await instance.engines.multiTimeframe.executeMultiTimeframeStrategy();
        result = {
          execution_id: mtResult.execution_id,
          timestamp: mtResult.timestamp,
          signals: mtResult.signals,
          performance_metrics: mtResult.performance_metrics,
          errors: mtResult.errors,
          warnings: mtResult.warnings
        };
      } else {
        // Single timeframe execution
        const primaryData = Array.from(marketDataMap.values())[0] || [];
        result = await instance.engines.execution.executeStrategy(primaryData);
      }

      // Update strategy performance
      this.updateStrategyPerformance(instance, result);

      return result;

    } catch (error) {
      instance.status = 'error';
      instance.error_message = error instanceof Error ? error.message : String(error);
      instance.performance.error_count++;
      throw error;
    }
  }

  private async executeRiskCheckStep(strategyId: string): Promise<{ passed: boolean; reason?: string }> {
    const instance = this.strategies.get(strategyId);
    if (!instance) {
      throw new Error(`Strategy ${strategyId} not found`);
    }

    return this.performRiskChecks(strategyId);
  }

  private async executePortfolioUpdateStep(): Promise<void> {
    // Collect all execution results from the pipeline
    const marketDataMap = new Map<string, MarketData[]>();
    
    // Update portfolio with latest results
    const results = await this.portfolioOrchestrator.executePortfolio(marketDataMap);
    
    // Update risk manager with new portfolio state
    this.riskManager.updatePortfolioState(this.portfolioOrchestrator.getPortfolioState());
  }

  private updateStrategyPerformance(instance: StrategyInstance, result: ExecutionResult): void {
    instance.performance.total_executions++;
    instance.performance.last_signal_time = result.timestamp;
    instance.performance.signals_generated += result.signals.length;
    instance.last_execution = result.timestamp;

    if (result.errors.length === 0) {
      instance.performance.successful_executions++;
    } else {
      instance.performance.error_count++;
    }

    // Update average execution time
    const totalTime = instance.performance.avg_execution_time_ms * (instance.performance.total_executions - 1);
    instance.performance.avg_execution_time_ms = 
      (totalTime + result.performance_metrics.execution_time_ms) / instance.performance.total_executions;
  }

  private async performRiskChecks(strategyId: string): Promise<{ passed: boolean; reason?: string }> {
    // Implementation would check various risk metrics
    return { passed: true };
  }

  private async processPortfolioOperations(): Promise<void> {
    // Portfolio rebalancing and optimization
  }

  private async performRiskMonitoring(): Promise<void> {
    // Generate risk alerts and take automated actions
    const alerts = this.riskManager.generateRiskAlerts();
    alerts.forEach(alert => {
      this.createAlert({
        severity: alert.severity === 'low' ? 'info' : 
                 alert.severity === 'medium' ? 'warning' : 
                 alert.severity === 'high' ? 'error' : 'critical',
        category: 'risk',
        source: 'risk_manager',
        message: alert.message,
        details: alert
      });
    });
  }

  private async processOptimization(): Promise<void> {
    // ML optimization processing
  }

  private async updateSystemHealth(): Promise<void> {
    // Update various health metrics
    this.state.system_health.uptime_seconds = Math.floor((Date.now() - this.state.last_update.getTime()) / 1000);
    this.state.system_health.memory_usage = this.resourceManager.getMemoryUsage();
    this.state.system_health.cpu_usage = this.resourceManager.getCpuUsage();
  }

  private async updatePerformanceMetrics(): Promise<void> {
    // Aggregate performance across all strategies
    let totalSignals = 0;
    let totalExecutions = 0;
    let successfulExecutions = 0;

    this.strategies.forEach(instance => {
      totalSignals += instance.performance.signals_generated;
      totalExecutions += instance.performance.total_executions;
      successfulExecutions += instance.performance.successful_executions;
    });

    this.state.performance_summary.total_signals = totalSignals;
    this.state.performance_summary.total_executions = totalExecutions;
    this.state.performance_summary.success_rate = totalExecutions > 0 ? (successfulExecutions / totalExecutions) * 100 : 0;

    // Portfolio metrics
    const portfolioState = this.portfolioOrchestrator.getPortfolioState();
    this.state.performance_summary.portfolio_value = portfolioState.total_equity;
    this.state.performance_summary.total_pnl = portfolioState.realized_pnl + portfolioState.unrealized_pnl;
    this.state.performance_summary.active_positions = portfolioState.positions.length;
  }

  private async processAlerts(): Promise<void> {
    // Process and manage alerts
    this.alertManager.processAlerts(this.state.alerts);
  }

  private handleMarketData(data: any): void {
    // Process incoming market data
    this.performanceMonitor.recordDataPoint('market_data_received');
  }

  private handleConnectionEvent(event: any): void {
    // Handle data connection events
    if (event.status === 'connected') {
      this.state.system_health.data_connectivity = 'connected';
    } else if (event.status === 'disconnected') {
      this.state.system_health.data_connectivity = 'disconnected';
    }
  }

  private handleDataError(error: any): void {
    // Handle data errors
    this.createAlert({
      severity: 'error',
      category: 'data',
      source: 'data_engine',
      message: `Data error: ${error.message || error}`,
      details: error
    });
  }

  private handleSystemError(error: any): void {
    // Handle system-level errors
    this.createAlert({
      severity: 'critical',
      category: 'system',
      source: 'orchestrator',
      message: `System error: ${error instanceof Error ? error.message : String(error)}`,
      details: error
    });
  }

  private createAlert(params: {
    severity: OrchestrationAlert['severity'];
    category: OrchestrationAlert['category'];
    source: string;
    message: string;
    details?: any;
  }): void {
    const alert: OrchestrationAlert = {
      alert_id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      severity: params.severity,
      category: params.category,
      source: params.source,
      message: params.message,
      details: params.details,
      acknowledged: false,
      auto_resolved: false
    };

    this.state.alerts.push(alert);
    
    // Keep only recent alerts
    if (this.state.alerts.length > 1000) {
      this.state.alerts = this.state.alerts.slice(-1000);
    }
  }

  private cleanupOldPipelines(): void {
    const now = Date.now();
    const maxAge = 24 * 60 * 60 * 1000; // 24 hours

    for (const [pipelineId, pipeline] of this.executionPipelines.entries()) {
      if (now - pipeline.start_time.getTime() > maxAge) {
        this.executionPipelines.delete(pipelineId);
      }
    }
  }

  // Public API methods
  public async stop(): Promise<void> {
    if (!this.isRunning) return;

    this.state.status = 'pausing';
    
    // Stop main loop
    if (this.mainLoop) {
      clearInterval(this.mainLoop);
      this.mainLoop = null;
    }

    // Stop all strategies
    for (const [strategyId, instance] of this.strategies.entries()) {
      if (instance.status === 'running') {
        instance.status = 'paused';
        this.state.active_strategies--;
      }
    }

    // Disconnect from data providers
    await this.dataEngine.disconnectAll();

    // Stop performance monitoring
    this.performanceMonitor.stop();

    this.isRunning = false;
    this.state.status = 'stopped';

    this.createAlert({
      severity: 'info',
      category: 'system',
      source: 'orchestrator',
      message: 'Strategy orchestration engine stopped'
    });

    console.log('Strategy Orchestration Engine stopped');
  }

  public getState(): OrchestrationState {
    return { ...this.state };
  }

  public getStrategies(): StrategyInstance[] {
    return Array.from(this.strategies.values());
  }

  public getStrategy(strategyId: string): StrategyInstance | undefined {
    return this.strategies.get(strategyId);
  }

  public async pauseStrategy(strategyId: string): Promise<void> {
    const instance = this.strategies.get(strategyId);
    if (!instance) {
      throw new Error(`Strategy ${strategyId} not found`);
    }

    if (instance.status === 'running') {
      instance.status = 'paused';
      this.state.active_strategies--;
    }
  }

  public async resumeStrategy(strategyId: string): Promise<void> {
    const instance = this.strategies.get(strategyId);
    if (!instance) {
      throw new Error(`Strategy ${strategyId} not found`);
    }

    if (instance.status === 'paused') {
      await this.startStrategy(strategyId);
    }
  }

  public async removeStrategy(strategyId: string): Promise<void> {
    const instance = this.strategies.get(strategyId);
    if (!instance) return;

    // Stop strategy if running
    if (instance.status === 'running') {
      await this.pauseStrategy(strategyId);
    }

    // Remove from portfolio orchestrator
    this.portfolioOrchestrator.removeStrategy(strategyId);

    // Unsubscribe from market data
    await this.dataEngine.unsubscribe(strategyId);

    // Remove from strategies map
    this.strategies.delete(strategyId);
    this.state.total_strategies = this.strategies.size;

    this.createAlert({
      severity: 'info',
      category: 'strategy',
      source: strategyId,
      message: `Strategy ${instance.strategy_name} removed`
    });
  }
}

// Helper classes
class PerformanceMonitor {
  private dataPoints: Map<string, number[]> = new Map();
  private isRunning = false;

  public start(): void {
    this.isRunning = true;
  }

  public stop(): void {
    this.isRunning = false;
  }

  public recordDataPoint(metric: string, value: number = 1): void {
    if (!this.dataPoints.has(metric)) {
      this.dataPoints.set(metric, []);
    }
    
    const points = this.dataPoints.get(metric)!;
    points.push(value);
    
    // Keep only recent data points
    if (points.length > 1000) {
      this.dataPoints.set(metric, points.slice(-1000));
    }
  }

  public getMetric(metric: string): number[] {
    return this.dataPoints.get(metric) || [];
  }
}

class AlertManager {
  public processAlerts(alerts: OrchestrationAlert[]): void {
    // Process and manage alerts
    alerts.forEach(alert => {
      if (!alert.acknowledged && alert.severity === 'critical') {
        // Handle critical alerts
        this.handleCriticalAlert(alert);
      }
    });
  }

  private handleCriticalAlert(alert: OrchestrationAlert): void {
    // Implementation for critical alert handling
    console.error(`CRITICAL ALERT: ${alert.message}`);
  }
}

class ResourceManager {
  public getMemoryUsage(): number {
    // Simplified memory usage calculation
    return Math.floor(Math.random() * 100);
  }

  public getCpuUsage(): number {
    // Simplified CPU usage calculation
    return Math.floor(Math.random() * 100);
  }
}

// Export function for creating orchestration engine
export const createStrategyOrchestrationEngine = (
  config: OrchestrationConfig,
  portfolioConfig: PortfolioConfig,
  riskConfig: RiskManagerConfig,
  dataProviders: Map<string, DataProviderConfig>
): StrategyOrchestrationEngine => {
  return new StrategyOrchestrationEngine(config, portfolioConfig, riskConfig, dataProviders);
};