import { Node, Edge } from 'reactflow';

export interface SystemConfiguration {
  general: GeneralConfig;
  trading: TradingConfig;
  risk: RiskConfig;
  data: DataConfig;
  ui: UIConfig;
  performance: PerformanceConfig;
  notifications: NotificationConfig;
  security: SecurityConfig;
  backup: BackupConfig;
  logging: LoggingConfig;
}

export interface GeneralConfig {
  environment: 'development' | 'testing' | 'staging' | 'production';
  region: string;
  timezone: string;
  currency: string;
  language: string;
  theme: 'light' | 'dark' | 'auto';
  auto_save_interval: number; // seconds
  session_timeout: number; // minutes
  max_concurrent_strategies: number;
  max_portfolio_value: number;
}

export interface TradingConfig {
  default_execution_mode: 'paper' | 'live' | 'backtest';
  order_management: {
    default_order_type: 'market' | 'limit' | 'stop' | 'stop_limit';
    default_time_in_force: 'day' | 'gtc' | 'ioc' | 'fok';
    max_order_size: number;
    min_order_size: number;
    price_precision: number;
    quantity_precision: number;
  };
  execution_timing: {
    max_execution_delay_ms: number;
    order_timeout_seconds: number;
    cancel_timeout_seconds: number;
    retry_attempts: number;
    retry_delay_ms: number;
  };
  market_hours: {
    pre_market_start: string;
    market_open: string;
    market_close: string;
    after_hours_end: string;
    trading_days: string[];
    holidays: string[];
  };
}

export interface RiskConfig {
  portfolio_limits: {
    max_total_exposure: number;
    max_single_position: number;
    max_sector_exposure: number;
    max_geographic_exposure: number;
    max_currency_exposure: number;
    max_correlation: number;
  };
  position_sizing: {
    default_position_size: number;
    max_position_size: number;
    position_sizing_method: 'fixed' | 'percent_equity' | 'volatility_adjusted' | 'kelly';
    volatility_lookback_days: number;
    rebalance_threshold: number;
  };
  stop_loss: {
    default_stop_loss: number;
    max_stop_loss: number;
    trailing_stop_enabled: boolean;
    atr_multiplier: number;
    volatility_adjusted: boolean;
  };
  drawdown_protection: {
    max_portfolio_drawdown: number;
    max_strategy_drawdown: number;
    emergency_stop_enabled: boolean;
    recovery_threshold: number;
    position_reduction_factor: number;
  };
}

export interface DataConfig {
  providers: {
    primary_provider: string;
    backup_providers: string[];
    data_quality_threshold: number;
    latency_threshold_ms: number;
    reconnection_attempts: number;
    reconnection_delay_ms: number;
  };
  storage: {
    historical_data_retention_days: number;
    real_time_buffer_size: number;
    compression_enabled: boolean;
    backup_frequency: 'hourly' | 'daily' | 'weekly';
    local_storage_path: string;
    cloud_storage_enabled: boolean;
  };
  subscriptions: {
    default_timeframes: string[];
    data_types: string[];
    symbols_per_provider: number;
    streaming_buffer_size: number;
    batch_size: number;
  };
}

export interface UIConfig {
  layout: {
    default_layout: 'classic' | 'modern' | 'compact';
    sidebar_width: number;
    panel_heights: Record<string, number>;
    auto_hide_panels: boolean;
    responsive_breakpoints: Record<string, number>;
  };
  charts: {
    default_chart_type: 'candlestick' | 'line' | 'bar';
    default_timeframe: string;
    max_indicators_per_chart: number;
    chart_update_interval_ms: number;
    price_precision: number;
    volume_display: boolean;
  };
  tables: {
    rows_per_page: number;
    auto_refresh_interval: number;
    sort_persistence: boolean;
    filter_persistence: boolean;
    export_formats: string[];
  };
  notifications: {
    position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
    auto_dismiss_time: number;
    max_notifications: number;
    sound_enabled: boolean;
    vibration_enabled: boolean;
  };
}

export interface PerformanceConfig {
  monitoring: {
    metrics_collection_enabled: boolean;
    metrics_retention_days: number;
    performance_alerts_enabled: boolean;
    cpu_threshold: number;
    memory_threshold: number;
    latency_threshold_ms: number;
  };
  optimization: {
    auto_optimization_enabled: boolean;
    optimization_frequency: 'daily' | 'weekly' | 'monthly';
    optimization_algorithms: string[];
    max_optimization_time_minutes: number;
    parallel_optimizations: number;
  };
  caching: {
    indicator_cache_enabled: boolean;
    indicator_cache_size: number;
    result_cache_ttl_seconds: number;
    memory_cache_limit_mb: number;
    disk_cache_enabled: boolean;
  };
}

export interface NotificationConfig {
  channels: {
    email_enabled: boolean;
    sms_enabled: boolean;
    push_enabled: boolean;
    webhook_enabled: boolean;
    in_app_enabled: boolean;
  };
  triggers: {
    trade_execution: boolean;
    risk_alerts: boolean;
    system_errors: boolean;
    performance_milestones: boolean;
    market_events: boolean;
  };
  filtering: {
    min_severity: 'info' | 'warning' | 'error' | 'critical';
    rate_limiting_enabled: boolean;
    max_notifications_per_hour: number;
    duplicate_suppression_minutes: number;
  };
  contacts: {
    primary_email: string;
    backup_emails: string[];
    phone_numbers: string[];
    webhook_urls: string[];
  };
}

export interface SecurityConfig {
  authentication: {
    session_duration_hours: number;
    require_2fa: boolean;
    password_policy: {
      min_length: number;
      require_uppercase: boolean;
      require_lowercase: boolean;
      require_numbers: boolean;
      require_symbols: boolean;
      expiry_days: number;
    };
    login_attempts: {
      max_attempts: number;
      lockout_duration_minutes: number;
      reset_duration_minutes: number;
    };
  };
  api_security: {
    rate_limiting: {
      requests_per_minute: number;
      burst_limit: number;
      whitelist_ips: string[];
    };
    encryption: {
      in_transit: boolean;
      at_rest: boolean;
      key_rotation_days: number;
    };
  };
  audit: {
    log_all_actions: boolean;
    log_retention_days: number;
    real_time_monitoring: boolean;
    suspicious_activity_detection: boolean;
  };
}

export interface BackupConfig {
  strategy: {
    backup_frequency: 'real_time' | 'hourly' | 'daily' | 'weekly';
    retention_policy: {
      daily_backups: number;
      weekly_backups: number;
      monthly_backups: number;
      yearly_backups: number;
    };
    compression_enabled: boolean;
    encryption_enabled: boolean;
  };
  storage: {
    local_backup_path: string;
    cloud_backup_enabled: boolean;
    cloud_provider: 'aws' | 'gcp' | 'azure' | 'custom';
    redundancy_level: number;
    cross_region_replication: boolean;
  };
  recovery: {
    auto_recovery_enabled: boolean;
    recovery_point_objective_minutes: number;
    recovery_time_objective_minutes: number;
    disaster_recovery_site: string;
  };
}

export interface LoggingConfig {
  levels: {
    application_level: 'debug' | 'info' | 'warn' | 'error';
    trading_level: 'debug' | 'info' | 'warn' | 'error';
    system_level: 'debug' | 'info' | 'warn' | 'error';
    audit_level: 'debug' | 'info' | 'warn' | 'error';
  };
  output: {
    console_enabled: boolean;
    file_enabled: boolean;
    database_enabled: boolean;
    remote_enabled: boolean;
    structured_logging: boolean;
  };
  rotation: {
    max_file_size_mb: number;
    max_files: number;
    compression_enabled: boolean;
    retention_days: number;
  };
  filtering: {
    exclude_patterns: string[];
    include_patterns: string[];
    sensitive_data_masking: boolean;
    ip_anonymization: boolean;
  };
}

export interface ConfigurationTemplate {
  template_id: string;
  name: string;
  description: string;
  category: 'trading_style' | 'risk_profile' | 'market_type' | 'custom';
  configuration: Partial<SystemConfiguration>;
  compatible_strategies: string[];
  recommended_for: string[];
  created_by: string;
  created_at: Date;
  version: string;
}

export interface ConfigurationValidationResult {
  valid: boolean;
  errors: ConfigurationError[];
  warnings: ConfigurationWarning[];
  suggestions: ConfigurationSuggestion[];
}

export interface ConfigurationError {
  field: string;
  message: string;
  severity: 'error' | 'warning';
  suggested_fix?: string;
}

export interface ConfigurationWarning {
  field: string;
  message: string;
  impact: 'performance' | 'risk' | 'functionality';
  recommendation: string;
}

export interface ConfigurationSuggestion {
  field: string;
  current_value: any;
  suggested_value: any;
  reason: string;
  impact: string;
}

export interface ConfigurationChangeLog {
  change_id: string;
  timestamp: Date;
  user_id: string;
  action: 'create' | 'update' | 'delete' | 'restore';
  field_path: string;
  old_value: any;
  new_value: any;
  reason: string;
  approved_by?: string;
}

export class ConfigurationManager {
  private config: SystemConfiguration;
  private templates: Map<string, ConfigurationTemplate> = new Map();
  private changeLog: ConfigurationChangeLog[] = [];
  private validators: Map<string, (value: any) => ConfigurationValidationResult> = new Map();
  private subscribers: Map<string, Function[]> = new Map();
  private autoSaveEnabled = true;
  private pendingChanges: Map<string, any> = new Map();

  constructor() {
    this.config = this.getDefaultConfiguration();
    this.setupValidators();
    this.loadSavedConfiguration();
    this.loadTemplates();
  }

  private getDefaultConfiguration(): SystemConfiguration {
    return {
      general: {
        environment: 'development',
        region: 'US',
        timezone: 'America/New_York',
        currency: 'USD',
        language: 'en',
        theme: 'auto',
        auto_save_interval: 30,
        session_timeout: 480,
        max_concurrent_strategies: 50,
        max_portfolio_value: 10000000
      },
      trading: {
        default_execution_mode: 'paper',
        order_management: {
          default_order_type: 'limit',
          default_time_in_force: 'day',
          max_order_size: 1000000,
          min_order_size: 1,
          price_precision: 2,
          quantity_precision: 0
        },
        execution_timing: {
          max_execution_delay_ms: 5000,
          order_timeout_seconds: 30,
          cancel_timeout_seconds: 10,
          retry_attempts: 3,
          retry_delay_ms: 1000
        },
        market_hours: {
          pre_market_start: '04:00',
          market_open: '09:30',
          market_close: '16:00',
          after_hours_end: '20:00',
          trading_days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
          holidays: []
        }
      },
      risk: {
        portfolio_limits: {
          max_total_exposure: 100,
          max_single_position: 10,
          max_sector_exposure: 25,
          max_geographic_exposure: 50,
          max_currency_exposure: 80,
          max_correlation: 0.7
        },
        position_sizing: {
          default_position_size: 2,
          max_position_size: 10,
          position_sizing_method: 'percent_equity',
          volatility_lookback_days: 20,
          rebalance_threshold: 5
        },
        stop_loss: {
          default_stop_loss: 5,
          max_stop_loss: 20,
          trailing_stop_enabled: true,
          atr_multiplier: 2.0,
          volatility_adjusted: true
        },
        drawdown_protection: {
          max_portfolio_drawdown: 20,
          max_strategy_drawdown: 15,
          emergency_stop_enabled: true,
          recovery_threshold: 10,
          position_reduction_factor: 0.5
        }
      },
      data: {
        providers: {
          primary_provider: 'polygon',
          backup_providers: ['alpaca', 'yahoo'],
          data_quality_threshold: 0.95,
          latency_threshold_ms: 1000,
          reconnection_attempts: 5,
          reconnection_delay_ms: 5000
        },
        storage: {
          historical_data_retention_days: 365,
          real_time_buffer_size: 10000,
          compression_enabled: true,
          backup_frequency: 'daily',
          local_storage_path: './data',
          cloud_storage_enabled: false
        },
        subscriptions: {
          default_timeframes: ['1m', '5m', '1h', '1d'],
          data_types: ['trades', 'quotes', 'bars'],
          symbols_per_provider: 100,
          streaming_buffer_size: 1000,
          batch_size: 100
        }
      },
      ui: {
        layout: {
          default_layout: 'modern',
          sidebar_width: 250,
          panel_heights: { chart: 400, table: 300, alerts: 200 },
          auto_hide_panels: false,
          responsive_breakpoints: { mobile: 768, tablet: 1024, desktop: 1200 }
        },
        charts: {
          default_chart_type: 'candlestick',
          default_timeframe: '1h',
          max_indicators_per_chart: 10,
          chart_update_interval_ms: 1000,
          price_precision: 2,
          volume_display: true
        },
        tables: {
          rows_per_page: 50,
          auto_refresh_interval: 5000,
          sort_persistence: true,
          filter_persistence: true,
          export_formats: ['csv', 'xlsx', 'json']
        },
        notifications: {
          position: 'top-right',
          auto_dismiss_time: 5000,
          max_notifications: 10,
          sound_enabled: true,
          vibration_enabled: false
        }
      },
      performance: {
        monitoring: {
          metrics_collection_enabled: true,
          metrics_retention_days: 90,
          performance_alerts_enabled: true,
          cpu_threshold: 80,
          memory_threshold: 80,
          latency_threshold_ms: 1000
        },
        optimization: {
          auto_optimization_enabled: false,
          optimization_frequency: 'weekly',
          optimization_algorithms: ['genetic', 'bayesian'],
          max_optimization_time_minutes: 60,
          parallel_optimizations: 2
        },
        caching: {
          indicator_cache_enabled: true,
          indicator_cache_size: 1000,
          result_cache_ttl_seconds: 300,
          memory_cache_limit_mb: 512,
          disk_cache_enabled: true
        }
      },
      notifications: {
        channels: {
          email_enabled: true,
          sms_enabled: false,
          push_enabled: true,
          webhook_enabled: false,
          in_app_enabled: true
        },
        triggers: {
          trade_execution: true,
          risk_alerts: true,
          system_errors: true,
          performance_milestones: true,
          market_events: false
        },
        filtering: {
          min_severity: 'warning',
          rate_limiting_enabled: true,
          max_notifications_per_hour: 50,
          duplicate_suppression_minutes: 5
        },
        contacts: {
          primary_email: '',
          backup_emails: [],
          phone_numbers: [],
          webhook_urls: []
        }
      },
      security: {
        authentication: {
          session_duration_hours: 8,
          require_2fa: false,
          password_policy: {
            min_length: 8,
            require_uppercase: true,
            require_lowercase: true,
            require_numbers: true,
            require_symbols: false,
            expiry_days: 90
          },
          login_attempts: {
            max_attempts: 5,
            lockout_duration_minutes: 15,
            reset_duration_minutes: 60
          }
        },
        api_security: {
          rate_limiting: {
            requests_per_minute: 1000,
            burst_limit: 100,
            whitelist_ips: []
          },
          encryption: {
            in_transit: true,
            at_rest: true,
            key_rotation_days: 30
          }
        },
        audit: {
          log_all_actions: true,
          log_retention_days: 365,
          real_time_monitoring: true,
          suspicious_activity_detection: true
        }
      },
      backup: {
        strategy: {
          backup_frequency: 'hourly',
          retention_policy: {
            daily_backups: 7,
            weekly_backups: 4,
            monthly_backups: 12,
            yearly_backups: 3
          },
          compression_enabled: true,
          encryption_enabled: true
        },
        storage: {
          local_backup_path: './backups',
          cloud_backup_enabled: false,
          cloud_provider: 'aws',
          redundancy_level: 2,
          cross_region_replication: false
        },
        recovery: {
          auto_recovery_enabled: true,
          recovery_point_objective_minutes: 15,
          recovery_time_objective_minutes: 30,
          disaster_recovery_site: ''
        }
      },
      logging: {
        levels: {
          application_level: 'info',
          trading_level: 'info',
          system_level: 'warn',
          audit_level: 'info'
        },
        output: {
          console_enabled: true,
          file_enabled: true,
          database_enabled: false,
          remote_enabled: false,
          structured_logging: true
        },
        rotation: {
          max_file_size_mb: 100,
          max_files: 10,
          compression_enabled: true,
          retention_days: 30
        },
        filtering: {
          exclude_patterns: ['debug.*', 'trace.*'],
          include_patterns: ['error.*', 'warn.*'],
          sensitive_data_masking: true,
          ip_anonymization: true
        }
      }
    };
  }

  private setupValidators(): void {
    // General validators
    this.validators.set('general.max_concurrent_strategies', (value: number) => {
      const errors: ConfigurationError[] = [];
      if (value < 1 || value > 1000) {
        errors.push({
          field: 'general.max_concurrent_strategies',
          message: 'Must be between 1 and 1000',
          severity: 'error'
        });
      }
      return { valid: errors.length === 0, errors, warnings: [], suggestions: [] };
    });

    // Risk validators
    this.validators.set('risk.portfolio_limits.max_total_exposure', (value: number) => {
      const errors: ConfigurationError[] = [];
      const warnings: ConfigurationWarning[] = [];
      
      if (value < 0 || value > 200) {
        errors.push({
          field: 'risk.portfolio_limits.max_total_exposure',
          message: 'Must be between 0 and 200',
          severity: 'error'
        });
      }
      
      if (value > 100) {
        warnings.push({
          field: 'risk.portfolio_limits.max_total_exposure',
          message: 'Exposure above 100% uses leverage',
          impact: 'risk',
          recommendation: 'Consider reducing exposure for safer trading'
        });
      }
      
      return { valid: errors.length === 0, errors, warnings, suggestions: [] };
    });

    // Performance validators
    this.validators.set('performance.monitoring.cpu_threshold', (value: number) => {
      const errors: ConfigurationError[] = [];
      if (value < 10 || value > 100) {
        errors.push({
          field: 'performance.monitoring.cpu_threshold',
          message: 'Must be between 10 and 100',
          severity: 'error'
        });
      }
      return { valid: errors.length === 0, errors, warnings: [], suggestions: [] };
    });
  }

  private loadSavedConfiguration(): void {
    try {
      const saved = localStorage.getItem('alphintra_configuration');
      if (saved) {
        const parsedConfig = JSON.parse(saved);
        this.config = { ...this.config, ...parsedConfig };
      }
    } catch (error) {
      console.error('Error loading saved configuration:', error);
    }
  }

  private saveConfiguration(): void {
    try {
      localStorage.setItem('alphintra_configuration', JSON.stringify(this.config));
    } catch (error) {
      console.error('Error saving configuration:', error);
    }
  }

  private loadTemplates(): void {
    // Load predefined templates
    const defaultTemplates: ConfigurationTemplate[] = [
      {
        template_id: 'conservative_trader',
        name: 'Conservative Trader',
        description: 'Low-risk configuration for conservative trading',
        category: 'risk_profile',
        configuration: {
          risk: {
            portfolio_limits: {
              max_total_exposure: 50,
              max_single_position: 5,
              max_sector_exposure: 15,
              max_geographic_exposure: 30,
              max_currency_exposure: 60,
              max_correlation: 0.5
            },
            position_sizing: {
              default_position_size: 1,
              max_position_size: 3,
              position_sizing_method: 'volatility_adjusted',
              volatility_lookback_days: 30,
              rebalance_threshold: 3
            }
          }
        },
        compatible_strategies: ['value', 'dividend', 'bonds'],
        recommended_for: ['beginners', 'retirement_accounts'],
        created_by: 'system',
        created_at: new Date(),
        version: '1.0'
      },
      {
        template_id: 'aggressive_trader',
        name: 'Aggressive Trader',
        description: 'High-risk, high-reward configuration',
        category: 'risk_profile',
        configuration: {
          risk: {
            portfolio_limits: {
              max_total_exposure: 150,
              max_single_position: 20,
              max_sector_exposure: 40,
              max_geographic_exposure: 80,
              max_currency_exposure: 100,
              max_correlation: 0.8
            },
            position_sizing: {
              default_position_size: 5,
              max_position_size: 15,
              position_sizing_method: 'kelly',
              volatility_lookback_days: 10,
              rebalance_threshold: 10
            }
          }
        },
        compatible_strategies: ['growth', 'momentum', 'crypto'],
        recommended_for: ['experienced_traders', 'speculation_accounts'],
        created_by: 'system',
        created_at: new Date(),
        version: '1.0'
      },
      {
        template_id: 'day_trader',
        name: 'Day Trader',
        description: 'Configuration optimized for day trading',
        category: 'trading_style',
        configuration: {
          trading: {
            execution_timing: {
              max_execution_delay_ms: 100,
              order_timeout_seconds: 5,
              cancel_timeout_seconds: 2,
              retry_attempts: 5,
              retry_delay_ms: 200
            }
          },
          data: {
            subscriptions: {
              default_timeframes: ['1s', '1m', '5m'],
              streaming_buffer_size: 5000,
              batch_size: 10
            }
          },
          ui: {
            charts: {
              chart_update_interval_ms: 100,
              default_timeframe: '1m'
            }
          }
        },
        compatible_strategies: ['scalping', 'momentum', 'arbitrage'],
        recommended_for: ['professional_traders', 'high_frequency'],
        created_by: 'system',
        created_at: new Date(),
        version: '1.0'
      }
    ];

    defaultTemplates.forEach(template => {
      this.templates.set(template.template_id, template);
    });
  }

  public getConfiguration(): SystemConfiguration {
    return JSON.parse(JSON.stringify(this.config));
  }

  public getConfigurationSection<T extends keyof SystemConfiguration>(section: T): SystemConfiguration[T] {
    return JSON.parse(JSON.stringify(this.config[section]));
  }

  public updateConfiguration(updates: Partial<SystemConfiguration>): ConfigurationValidationResult {
    const validationResult = this.validateConfiguration(updates);
    
    if (validationResult.valid) {
      const oldConfig = JSON.parse(JSON.stringify(this.config));
      this.config = this.mergeConfigurations(this.config, updates);
      
      // Log changes
      this.logConfigurationChanges(oldConfig, this.config, 'update');
      
      // Auto-save if enabled
      if (this.autoSaveEnabled) {
        this.saveConfiguration();
      }
      
      // Notify subscribers
      this.notifySubscribers('configuration_updated', this.config);
    }
    
    return validationResult;
  }

  public updateConfigurationField(fieldPath: string, value: any): ConfigurationValidationResult {
    const validator = this.validators.get(fieldPath);
    let validationResult: ConfigurationValidationResult = { valid: true, errors: [], warnings: [], suggestions: [] };
    
    if (validator) {
      validationResult = validator(value);
    }
    
    if (validationResult.valid) {
      const oldValue = this.getFieldValue(fieldPath);
      this.setFieldValue(fieldPath, value);
      
      // Log change
      this.changeLog.push({
        change_id: `change_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
        user_id: 'current_user', // Would be actual user ID
        action: 'update',
        field_path: fieldPath,
        old_value: oldValue,
        new_value: value,
        reason: 'User update'
      });
      
      if (this.autoSaveEnabled) {
        this.saveConfiguration();
      }
      
      this.notifySubscribers(`field_updated:${fieldPath}`, value);
    }
    
    return validationResult;
  }

  private getFieldValue(fieldPath: string): any {
    const parts = fieldPath.split('.');
    let current: any = this.config;
    
    for (const part of parts) {
      if (current && typeof current === 'object' && part in current) {
        current = current[part];
      } else {
        return undefined;
      }
    }
    
    return current;
  }

  private setFieldValue(fieldPath: string, value: any): void {
    const parts = fieldPath.split('.');
    const lastPart = parts.pop()!;
    let current: any = this.config;
    
    for (const part of parts) {
      if (!(part in current)) {
        current[part] = {};
      }
      current = current[part];
    }
    
    current[lastPart] = value;
  }

  public validateConfiguration(config: Partial<SystemConfiguration>): ConfigurationValidationResult {
    const result: ConfigurationValidationResult = {
      valid: true,
      errors: [],
      warnings: [],
      suggestions: []
    };
    
    // Run all validators
    this.validators.forEach((validator, fieldPath) => {
      const fieldValue = this.getFieldValue(fieldPath);
      if (fieldValue !== undefined) {
        const fieldResult = validator(fieldValue);
        result.errors.push(...fieldResult.errors);
        result.warnings.push(...fieldResult.warnings);
        result.suggestions.push(...fieldResult.suggestions);
      }
    });
    
    // Cross-field validations
    this.performCrossFieldValidation(config, result);
    
    result.valid = result.errors.length === 0;
    return result;
  }

  private performCrossFieldValidation(config: Partial<SystemConfiguration>, result: ConfigurationValidationResult): void {
    // Example: Check if max_single_position doesn't exceed max_total_exposure
    const maxSingle = config.risk?.portfolio_limits?.max_single_position || this.config.risk.portfolio_limits.max_single_position;
    const maxTotal = config.risk?.portfolio_limits?.max_total_exposure || this.config.risk.portfolio_limits.max_total_exposure;
    
    if (maxSingle > maxTotal) {
      result.errors.push({
        field: 'risk.portfolio_limits',
        message: 'Max single position cannot exceed max total exposure',
        severity: 'error',
        suggested_fix: `Reduce max_single_position to ${maxTotal} or increase max_total_exposure`
      });
    }
    
    // Check if session timeout is reasonable for trading environment
    const sessionTimeout = config.general?.session_timeout || this.config.general.session_timeout;
    const environment = config.general?.environment || this.config.general.environment;
    
    if (environment === 'production' && sessionTimeout > 480) {
      result.warnings.push({
        field: 'general.session_timeout',
        message: 'Long session timeout in production environment',
        impact: 'security',
        recommendation: 'Consider shorter session timeout for production'
      });
    }
  }

  private mergeConfigurations(base: SystemConfiguration, updates: Partial<SystemConfiguration>): SystemConfiguration {
    return this.deepMerge(base, updates) as SystemConfiguration;
  }

  private deepMerge(target: any, source: any): any {
    const result = { ...target };
    
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = this.deepMerge(target[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
    
    return result;
  }

  private logConfigurationChanges(oldConfig: SystemConfiguration, newConfig: SystemConfiguration, action: string): void {
    const changes = this.findChanges(oldConfig, newConfig);
    
    changes.forEach(change => {
      this.changeLog.push({
        change_id: `change_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
        user_id: 'current_user',
        action: action as any,
        field_path: change.path,
        old_value: change.oldValue,
        new_value: change.newValue,
        reason: 'Configuration update'
      });
    });
    
    // Keep only recent changes
    if (this.changeLog.length > 1000) {
      this.changeLog = this.changeLog.slice(-1000);
    }
  }

  private findChanges(oldObj: any, newObj: any, path = ''): Array<{path: string; oldValue: any; newValue: any}> {
    const changes: Array<{path: string; oldValue: any; newValue: any}> = [];
    
    const allKeys = new Set([...Object.keys(oldObj || {}), ...Object.keys(newObj || {})]);
    
    for (const key of allKeys) {
      const currentPath = path ? `${path}.${key}` : key;
      const oldValue = oldObj?.[key];
      const newValue = newObj?.[key];
      
      if (oldValue !== newValue) {
        if (typeof oldValue === 'object' && typeof newValue === 'object' && 
            oldValue !== null && newValue !== null && 
            !Array.isArray(oldValue) && !Array.isArray(newValue)) {
          changes.push(...this.findChanges(oldValue, newValue, currentPath));
        } else {
          changes.push({ path: currentPath, oldValue, newValue });
        }
      }
    }
    
    return changes;
  }

  public applyTemplate(templateId: string): ConfigurationValidationResult {
    const template = this.templates.get(templateId);
    if (!template) {
      return {
        valid: false,
        errors: [{ field: 'template', message: `Template ${templateId} not found`, severity: 'error' }],
        warnings: [],
        suggestions: []
      };
    }
    
    return this.updateConfiguration(template.configuration);
  }

  public createTemplate(template: Omit<ConfigurationTemplate, 'template_id' | 'created_at'>): string {
    const templateId = `template_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const newTemplate: ConfigurationTemplate = {
      ...template,
      template_id: templateId,
      created_at: new Date()
    };
    
    this.templates.set(templateId, newTemplate);
    return templateId;
  }

  public getTemplates(category?: ConfigurationTemplate['category']): ConfigurationTemplate[] {
    const templates = Array.from(this.templates.values());
    
    if (category) {
      return templates.filter(t => t.category === category);
    }
    
    return templates;
  }

  public getTemplate(templateId: string): ConfigurationTemplate | undefined {
    return this.templates.get(templateId);
  }

  public deleteTemplate(templateId: string): boolean {
    return this.templates.delete(templateId);
  }

  public exportConfiguration(): string {
    return JSON.stringify({
      configuration: this.config,
      templates: Array.from(this.templates.values()),
      metadata: {
        exported_at: new Date(),
        version: '1.0'
      }
    }, null, 2);
  }

  public importConfiguration(configurationData: string): ConfigurationValidationResult {
    try {
      const data = JSON.parse(configurationData);
      
      if (data.configuration) {
        const validationResult = this.validateConfiguration(data.configuration);
        
        if (validationResult.valid) {
          this.config = data.configuration;
          
          if (data.templates) {
            data.templates.forEach((template: ConfigurationTemplate) => {
              this.templates.set(template.template_id, template);
            });
          }
          
          if (this.autoSaveEnabled) {
            this.saveConfiguration();
          }
          
          this.notifySubscribers('configuration_imported', this.config);
        }
        
        return validationResult;
      }
      
      return {
        valid: false,
        errors: [{ field: 'import', message: 'Invalid configuration format', severity: 'error' }],
        warnings: [],
        suggestions: []
      };
      
    } catch (error) {
      return {
        valid: false,
        errors: [{ field: 'import', message: `Import error: ${error}`, severity: 'error' }],
        warnings: [],
        suggestions: []
      };
    }
  }

  public resetToDefaults(): void {
    const oldConfig = JSON.parse(JSON.stringify(this.config));
    this.config = this.getDefaultConfiguration();
    
    this.logConfigurationChanges(oldConfig, this.config, 'reset');
    
    if (this.autoSaveEnabled) {
      this.saveConfiguration();
    }
    
    this.notifySubscribers('configuration_reset', this.config);
  }

  public getChangeLog(limit = 100): ConfigurationChangeLog[] {
    return this.changeLog.slice(-limit);
  }

  public subscribe(event: string, callback: Function): () => void {
    if (!this.subscribers.has(event)) {
      this.subscribers.set(event, []);
    }
    
    this.subscribers.get(event)!.push(callback);
    
    // Return unsubscribe function
    return () => {
      const callbacks = this.subscribers.get(event);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  private notifySubscribers(event: string, data: any): void {
    const callbacks = this.subscribers.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in configuration subscriber for ${event}:`, error);
        }
      });
    }
  }

  public setAutoSave(enabled: boolean): void {
    this.autoSaveEnabled = enabled;
  }

  public saveNow(): void {
    this.saveConfiguration();
  }

  public getPendingChanges(): Map<string, any> {
    return new Map(this.pendingChanges);
  }

  public commitPendingChanges(): ConfigurationValidationResult {
    if (this.pendingChanges.size === 0) {
      return { valid: true, errors: [], warnings: [], suggestions: [] };
    }
    
    const updates: any = {};
    for (const [fieldPath, value] of this.pendingChanges) {
      this.setNestedValue(updates, fieldPath, value);
    }
    
    const result = this.updateConfiguration(updates);
    
    if (result.valid) {
      this.pendingChanges.clear();
    }
    
    return result;
  }

  public discardPendingChanges(): void {
    this.pendingChanges.clear();
  }

  private setNestedValue(obj: any, path: string, value: any): void {
    const parts = path.split('.');
    const lastPart = parts.pop()!;
    let current = obj;
    
    for (const part of parts) {
      if (!(part in current)) {
        current[part] = {};
      }
      current = current[part];
    }
    
    current[lastPart] = value;
  }
}

// Export singleton instance
export const configurationManager = new ConfigurationManager();