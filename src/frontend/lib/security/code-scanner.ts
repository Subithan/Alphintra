import { GeneratedCode } from '../code-generator';

// Security risk levels
export enum SecurityRiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// Security issue categories
export enum SecurityCategory {
  CODE_INJECTION = 'code_injection',
  FILE_SYSTEM = 'file_system',
  NETWORK_ACCESS = 'network_access',
  PROCESS_EXECUTION = 'process_execution',
  IMPORT_SECURITY = 'import_security',
  DATA_EXPOSURE = 'data_exposure',
  RESOURCE_EXHAUSTION = 'resource_exhaustion',
  AUTHENTICATION = 'authentication',
  ENCRYPTION = 'encryption',
  LOGGING_SECURITY = 'logging_security'
}

// Security scan result
export interface SecurityIssue {
  id: string;
  category: SecurityCategory;
  riskLevel: SecurityRiskLevel;
  title: string;
  description: string;
  location: {
    line: number;
    column?: number;
    function?: string;
    context: string;
  };
  recommendation: string;
  cweId?: string; // Common Weakness Enumeration ID
  severity: number; // 1-10 scale
  confidence: number; // 1-10 scale
}

export interface SecurityScanResult {
  isSecure: boolean;
  overallRiskScore: number; // 1-100 scale
  issues: SecurityIssue[];
  summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    total: number;
  };
  recommendations: string[];
  scanDuration: number;
  scanTimestamp: Date;
  scannerVersion: string;
}

// Dangerous patterns and their risk levels
const DANGEROUS_PATTERNS = [
  // Code injection risks
  {
    pattern: /eval\s*\(/gi,
    category: SecurityCategory.CODE_INJECTION,
    riskLevel: SecurityRiskLevel.CRITICAL,
    title: 'Dangerous eval() usage',
    description: 'eval() can execute arbitrary code and is a major security risk',
    recommendation: 'Remove eval() and use safer alternatives like ast.literal_eval() for data parsing',
    cweId: 'CWE-94',
    severity: 9
  },
  {
    pattern: /exec\s*\(/gi,
    category: SecurityCategory.CODE_INJECTION,
    riskLevel: SecurityRiskLevel.CRITICAL,
    title: 'Dangerous exec() usage',
    description: 'exec() can execute arbitrary code strings',
    recommendation: 'Remove exec() and restructure code to avoid dynamic execution',
    cweId: 'CWE-94',
    severity: 9
  },
  {
    pattern: /compile\s*\(/gi,
    category: SecurityCategory.CODE_INJECTION,
    riskLevel: SecurityRiskLevel.HIGH,
    title: 'Code compilation detected',
    description: 'compile() can be used to create executable code objects',
    recommendation: 'Review compile() usage and ensure input validation',
    cweId: 'CWE-94',
    severity: 7
  },

  // File system access
  {
    pattern: /open\s*\(/gi,
    category: SecurityCategory.FILE_SYSTEM,
    riskLevel: SecurityRiskLevel.MEDIUM,
    title: 'File system access',
    description: 'File operations can be risky if paths are not validated',
    recommendation: 'Validate file paths and use safe file operations',
    cweId: 'CWE-22',
    severity: 5
  },
  {
    pattern: /os\.system\s*\(/gi,
    category: SecurityCategory.PROCESS_EXECUTION,
    riskLevel: SecurityRiskLevel.CRITICAL,
    title: 'System command execution',
    description: 'os.system() can execute arbitrary system commands',
    recommendation: 'Use subprocess with shell=False instead of os.system()',
    cweId: 'CWE-78',
    severity: 9
  },
  {
    pattern: /subprocess\.(call|run|Popen).*shell\s*=\s*True/gi,
    category: SecurityCategory.PROCESS_EXECUTION,
    riskLevel: SecurityRiskLevel.HIGH,
    title: 'Shell injection risk',
    description: 'subprocess with shell=True can lead to command injection',
    recommendation: 'Use subprocess with shell=False and pass arguments as a list',
    cweId: 'CWE-78',
    severity: 8
  },

  // Network access
  {
    pattern: /urllib\.request\./gi,
    category: SecurityCategory.NETWORK_ACCESS,
    riskLevel: SecurityRiskLevel.MEDIUM,
    title: 'Network request detected',
    description: 'Network requests can introduce security risks',
    recommendation: 'Validate URLs and use HTTPS when possible',
    cweId: 'CWE-295',
    severity: 4
  },
  {
    pattern: /requests\.(get|post|put|delete)/gi,
    category: SecurityCategory.NETWORK_ACCESS,
    riskLevel: SecurityRiskLevel.MEDIUM,
    title: 'HTTP request detected',
    description: 'HTTP requests should use secure protocols and validate inputs',
    recommendation: 'Use HTTPS, validate URLs, and implement proper error handling',
    cweId: 'CWE-295',
    severity: 4
  },

  // Import security
  {
    pattern: /__import__\s*\(/gi,
    category: SecurityCategory.IMPORT_SECURITY,
    riskLevel: SecurityRiskLevel.HIGH,
    title: 'Dynamic import detected',
    description: '__import__() allows dynamic module loading which can be risky',
    recommendation: 'Use static imports or importlib with proper validation',
    cweId: 'CWE-94',
    severity: 7
  },
  {
    pattern: /importlib\.import_module/gi,
    category: SecurityCategory.IMPORT_SECURITY,
    riskLevel: SecurityRiskLevel.MEDIUM,
    title: 'Dynamic module import',
    description: 'Dynamic module imports should validate module names',
    recommendation: 'Validate module names against a whitelist',
    cweId: 'CWE-94',
    severity: 5
  },

  // Data exposure
  {
    pattern: /print\s*\(.*(?:password|secret|key|token)/gi,
    category: SecurityCategory.DATA_EXPOSURE,
    riskLevel: SecurityRiskLevel.HIGH,
    title: 'Potential credential exposure',
    description: 'Printing sensitive information can expose credentials',
    recommendation: 'Remove debug prints containing sensitive data',
    cweId: 'CWE-532',
    severity: 7
  },
  {
    pattern: /logging\..*(?:password|secret|key|token)/gi,
    category: SecurityCategory.LOGGING_SECURITY,
    riskLevel: SecurityRiskLevel.MEDIUM,
    title: 'Potential credential logging',
    description: 'Logging sensitive information can expose credentials',
    recommendation: 'Sanitize log messages to remove sensitive data',
    cweId: 'CWE-532',
    severity: 6
  },

  // Resource exhaustion
  {
    pattern: /while\s+True\s*:/gi,
    category: SecurityCategory.RESOURCE_EXHAUSTION,
    riskLevel: SecurityRiskLevel.MEDIUM,
    title: 'Infinite loop detected',
    description: 'Infinite loops can cause resource exhaustion',
    recommendation: 'Add proper exit conditions and timeouts',
    cweId: 'CWE-835',
    severity: 5
  },
  {
    pattern: /range\s*\(\s*\d{6,}\s*\)/gi,
    category: SecurityCategory.RESOURCE_EXHAUSTION,
    riskLevel: SecurityRiskLevel.MEDIUM,
    title: 'Large range operation',
    description: 'Very large ranges can consume excessive memory',
    recommendation: 'Use iterators or break large operations into chunks',
    cweId: 'CWE-770',
    severity: 4
  }
];

// Allowed imports for trading strategies
const ALLOWED_IMPORTS = new Set([
  'pandas', 'numpy', 'talib', 'scipy', 'sklearn', 'matplotlib', 'plotly',
  'datetime', 'time', 'math', 'statistics', 'collections', 'itertools',
  'typing', 'dataclasses', 'enum', 'logging', 'json', 'csv', 're',
  'backtrader', 'zipline', 'quantlib', 'pyfolio', 'empyrical',
  'yfinance', 'alpha_vantage', 'quandl', 'fredapi',
  'asyncio', 'concurrent', 'threading', 'multiprocessing'
]);

// Forbidden imports
const FORBIDDEN_IMPORTS = new Set([
  'os', 'sys', 'subprocess', 'socket', 'urllib', 'http', 'ftplib',
  'smtplib', 'poplib', 'imaplib', 'telnetlib', 'ssl', 'hashlib',
  'hmac', 'secrets', 'crypt', 'pwd', 'grp', 'spwd', 'getpass',
  'ctypes', 'mmap', 'marshal', 'pickle', 'shelve', 'dbm'
]);

export class CodeSecurityScanner {
  private scanStartTime: Date;
  private issues: SecurityIssue[] = [];
  private scannerVersion = '1.0.0';

  constructor() {
    this.scanStartTime = new Date();
  }

  /**
   * Scan generated code for security issues
   */
  scanCode(generatedCode: GeneratedCode): SecurityScanResult {
    this.scanStartTime = new Date();
    this.issues = [];

    // Scan main strategy code
    this.scanCodeContent(generatedCode.strategy, 'strategy');

    // Scan test code
    if (generatedCode.tests) {
      this.scanCodeContent(generatedCode.tests, 'tests');
    }

    // Scan imports
    this.scanImports(generatedCode.imports);

    // Scan requirements
    this.scanRequirements(generatedCode.requirements);

    // Calculate overall risk score
    const overallRiskScore = this.calculateRiskScore();

    // Generate summary
    const summary = this.generateSummary();

    // Generate recommendations
    const recommendations = this.generateRecommendations();

    const scanDuration = Date.now() - this.scanStartTime.getTime();

    return {
      isSecure: overallRiskScore < 30 && summary.critical === 0,
      overallRiskScore,
      issues: this.issues,
      summary,
      recommendations,
      scanDuration,
      scanTimestamp: new Date(),
      scannerVersion: this.scannerVersion
    };
  }

  private scanCodeContent(code: string, context: string): void {
    const lines = code.split('\n');

    lines.forEach((line, lineNumber) => {
      DANGEROUS_PATTERNS.forEach(pattern => {
        const matches = line.match(pattern.pattern);
        if (matches) {
          matches.forEach(match => {
            this.addIssue({
              category: pattern.category,
              riskLevel: pattern.riskLevel,
              title: pattern.title,
              description: pattern.description,
              location: {
                line: lineNumber + 1,
                context: context,
                function: this.extractFunctionName(lines, lineNumber)
              },
              recommendation: pattern.recommendation,
              cweId: pattern.cweId,
              severity: pattern.severity,
              confidence: 8
            });
          });
        }
      });

      // Check for hardcoded credentials
      this.checkHardcodedCredentials(line, lineNumber + 1, context);

      // Check for SQL injection patterns
      this.checkSqlInjection(line, lineNumber + 1, context);

      // Check for unsafe deserialization
      this.checkUnsafeDeserialization(line, lineNumber + 1, context);
    });
  }

  private scanImports(imports: string[]): void {
    imports.forEach((importStatement, index) => {
      const moduleName = this.extractModuleName(importStatement);
      
      if (FORBIDDEN_IMPORTS.has(moduleName)) {
        this.addIssue({
          category: SecurityCategory.IMPORT_SECURITY,
          riskLevel: SecurityRiskLevel.HIGH,
          title: 'Forbidden module import',
          description: `Import of '${moduleName}' is not allowed for security reasons`,
          location: {
            line: index + 1,
            context: 'imports'
          },
          recommendation: 'Remove this import and use allowed alternatives',
          cweId: 'CWE-94',
          severity: 8,
          confidence: 10
        });
      } else if (!ALLOWED_IMPORTS.has(moduleName) && !moduleName.startsWith('.')) {
        this.addIssue({
          category: SecurityCategory.IMPORT_SECURITY,
          riskLevel: SecurityRiskLevel.MEDIUM,
          title: 'Unknown module import',
          description: `Import of '${moduleName}' is not in the allowed list`,
          location: {
            line: index + 1,
            context: 'imports'
          },
          recommendation: 'Verify that this module is safe and add to allowed list if needed',
          cweId: 'CWE-94',
          severity: 5,
          confidence: 7
        });
      }
    });
  }

  private scanRequirements(requirements: string[]): void {
    const suspiciousPackages = [
      'requests', 'urllib3', 'httpx', 'aiohttp', // Network libraries
      'psutil', 'py-cpuinfo', // System info
      'cryptography', 'pycrypto', // Crypto libraries
      'paramiko', 'fabric', 'invoke' // SSH/remote execution
    ];

    requirements.forEach((requirement, index) => {
      const packageName = requirement.split('>=')[0].split('==')[0].trim();
      
      if (suspiciousPackages.includes(packageName)) {
        this.addIssue({
          category: SecurityCategory.IMPORT_SECURITY,
          riskLevel: SecurityRiskLevel.MEDIUM,
          title: 'Potentially risky dependency',
          description: `Package '${packageName}' may introduce security risks`,
          location: {
            line: index + 1,
            context: 'requirements'
          },
          recommendation: 'Review if this dependency is necessary for trading strategy',
          severity: 4,
          confidence: 6
        });
      }
    });
  }

  private checkHardcodedCredentials(line: string, lineNumber: number, context: string): void {
    const credentialPatterns = [
      /(?:password|pwd|pass)\s*=\s*["'][^"']+["']/gi,
      /(?:api_key|apikey|token)\s*=\s*["'][^"']+["']/gi,
      /(?:secret|private_key)\s*=\s*["'][^"']+["']/gi
    ];

    credentialPatterns.forEach(pattern => {
      if (pattern.test(line)) {
        this.addIssue({
          category: SecurityCategory.DATA_EXPOSURE,
          riskLevel: SecurityRiskLevel.CRITICAL,
          title: 'Hardcoded credentials detected',
          description: 'Credentials should not be hardcoded in source code',
          location: {
            line: lineNumber,
            context
          },
          recommendation: 'Use environment variables or secure credential storage',
          cweId: 'CWE-798',
          severity: 9,
          confidence: 9
        });
      }
    });
  }

  private checkSqlInjection(line: string, lineNumber: number, context: string): void {
    const sqlPatterns = [
      /["'].*\+.*["'].*(?:SELECT|INSERT|UPDATE|DELETE)/gi,
      /f["'].*\{.*\}.*(?:SELECT|INSERT|UPDATE|DELETE)/gi,
      /\.format\(.*\).*(?:SELECT|INSERT|UPDATE|DELETE)/gi
    ];

    sqlPatterns.forEach(pattern => {
      if (pattern.test(line)) {
        this.addIssue({
          category: SecurityCategory.CODE_INJECTION,
          riskLevel: SecurityRiskLevel.HIGH,
          title: 'Potential SQL injection',
          description: 'SQL queries should use parameterized queries',
          location: {
            line: lineNumber,
            context
          },
          recommendation: 'Use parameterized queries or ORM methods',
          cweId: 'CWE-89',
          severity: 8,
          confidence: 7
        });
      }
    });
  }

  private checkUnsafeDeserialization(line: string, lineNumber: number, context: string): void {
    const deserializationPatterns = [
      /pickle\.loads?\s*\(/gi,
      /marshal\.loads?\s*\(/gi,
      /yaml\.load\s*\(/gi
    ];

    deserializationPatterns.forEach(pattern => {
      if (pattern.test(line)) {
        this.addIssue({
          category: SecurityCategory.CODE_INJECTION,
          riskLevel: SecurityRiskLevel.HIGH,
          title: 'Unsafe deserialization',
          description: 'Deserializing untrusted data can lead to code execution',
          location: {
            line: lineNumber,
            context
          },
          recommendation: 'Use safe serialization formats like JSON or validate data before deserializing',
          cweId: 'CWE-502',
          severity: 8,
          confidence: 8
        });
      }
    });
  }

  private extractModuleName(importStatement: string): string {
    const match = importStatement.match(/(?:from\s+)?([a-zA-Z_][a-zA-Z0-9_]*)/);
    return match ? match[1] : '';
  }

  private extractFunctionName(lines: string[], currentLine: number): string | undefined {
    // Look backwards to find the function definition
    for (let i = currentLine; i >= 0; i--) {
      const match = lines[i].match(/def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/);
      if (match) {
        return match[1];
      }
    }
    return undefined;
  }

  private addIssue(issue: Omit<SecurityIssue, 'id'>): void {
    this.issues.push({
      id: `sec_${this.issues.length + 1}_${Date.now()}`,
      ...issue
    });
  }

  private calculateRiskScore(): number {
    let totalScore = 0;
    let maxPossibleScore = 0;

    this.issues.forEach(issue => {
      const weight = this.getRiskWeight(issue.riskLevel);
      totalScore += issue.severity * weight * (issue.confidence / 10);
      maxPossibleScore += 10 * weight;
    });

    return maxPossibleScore > 0 ? Math.round((totalScore / maxPossibleScore) * 100) : 0;
  }

  private getRiskWeight(riskLevel: SecurityRiskLevel): number {
    switch (riskLevel) {
      case SecurityRiskLevel.CRITICAL: return 4;
      case SecurityRiskLevel.HIGH: return 3;
      case SecurityRiskLevel.MEDIUM: return 2;
      case SecurityRiskLevel.LOW: return 1;
      default: return 1;
    }
  }

  private generateSummary(): SecurityScanResult['summary'] {
    const summary = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      total: this.issues.length
    };

    this.issues.forEach(issue => {
      switch (issue.riskLevel) {
        case SecurityRiskLevel.CRITICAL:
          summary.critical++;
          break;
        case SecurityRiskLevel.HIGH:
          summary.high++;
          break;
        case SecurityRiskLevel.MEDIUM:
          summary.medium++;
          break;
        case SecurityRiskLevel.LOW:
          summary.low++;
          break;
      }
    });

    return summary;
  }

  private generateRecommendations(): string[] {
    const recommendations: string[] = [];

    if (this.issues.some(i => i.category === SecurityCategory.CODE_INJECTION)) {
      recommendations.push('Remove all code injection vulnerabilities (eval, exec, etc.)');
    }

    if (this.issues.some(i => i.category === SecurityCategory.DATA_EXPOSURE)) {
      recommendations.push('Implement secure credential management');
    }

    if (this.issues.some(i => i.category === SecurityCategory.IMPORT_SECURITY)) {
      recommendations.push('Review and validate all module imports');
    }

    if (this.issues.some(i => i.riskLevel === SecurityRiskLevel.CRITICAL)) {
      recommendations.push('Address all critical security issues before deployment');
    }

    if (recommendations.length === 0) {
      recommendations.push('Code appears secure, but continue monitoring for new vulnerabilities');
    }

    return recommendations;
  }
}

// Utility functions for security validation
export class SecurityValidator {
  /**
   * Quick security check for code snippet
   */
  static quickCheck(code: string): {
    isLikelySafe: boolean;
    issues: string[];
  } {
    const issues: string[] = [];

    // Check for obvious dangerous patterns
    if (/eval\s*\(/gi.test(code)) issues.push('Contains eval()');
    if (/exec\s*\(/gi.test(code)) issues.push('Contains exec()');
    if (/os\.system/gi.test(code)) issues.push('Contains os.system()');
    if (/subprocess.*shell\s*=\s*True/gi.test(code)) issues.push('Uses subprocess with shell=True');
    if (/(?:password|secret|key)\s*=\s*["'][^"']+["']/gi.test(code)) issues.push('Contains hardcoded credentials');

    return {
      isLikelySafe: issues.length === 0,
      issues
    };
  }

  /**
   * Validate import statement
   */
  static validateImport(importStatement: string): {
    isAllowed: boolean;
    reason?: string;
  } {
    const moduleName = importStatement.match(/(?:from\s+)?([a-zA-Z_][a-zA-Z0-9_]*)/)?.[1] || '';

    if (FORBIDDEN_IMPORTS.has(moduleName)) {
      return {
        isAllowed: false,
        reason: `Module '${moduleName}' is forbidden for security reasons`
      };
    }

    if (!ALLOWED_IMPORTS.has(moduleName) && !moduleName.startsWith('.')) {
      return {
        isAllowed: false,
        reason: `Module '${moduleName}' is not in the allowed imports list`
      };
    }

    return { isAllowed: true };
  }

  /**
   * Sanitize code for safe display
   */
  static sanitizeForDisplay(code: string): string {
    // Remove potential XSS in code comments or strings
    return code
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '[SCRIPT_REMOVED]')
      .replace(/<[^>]*>/g, '') // Remove HTML tags
      .replace(/javascript:/gi, 'javascript_removed:');
  }
}

// Export scanner instance
export const codeScanner = new CodeSecurityScanner();