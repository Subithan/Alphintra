'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Code2,
  Download,
  Copy,
  CheckCircle,
  XCircle,
  FileText,
  Settings,
  RefreshCw,
  Eye,
  EyeOff,
  Zap,
  Shield,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Info
} from 'lucide-react';
import { GeneratedCode, AdvancedCodeGenerator } from '@/lib/code-generator';
import { useNoCodeStore } from '@/lib/stores/no-code-store';
import { CodeSecurityScanner, SecurityScanResult, SecurityRiskLevel } from '@/lib/security/code-scanner';

interface CodeViewerProps {
  isOpen: boolean;
  onClose: () => void;
  generatedCode?: GeneratedCode;
  className?: string;
}

export function CodeViewer({ isOpen, onClose, generatedCode, className }: CodeViewerProps) {
  const { currentWorkflow } = useNoCodeStore();
  const [code, setCode] = useState<GeneratedCode | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copiedSection, setCopiedSection] = useState<string | null>(null);
  const [showLineNumbers, setShowLineNumbers] = useState(true);
  const [securityScan, setSecurityScan] = useState<SecurityScanResult | null>(null);
  const [isScanning, setIsScanning] = useState(false);

  useEffect(() => {
    if (generatedCode) {
      setCode(generatedCode);
      runSecurityScan(generatedCode);
    } else if (isOpen && currentWorkflow) {
      generateCode();
    }
  }, [isOpen, generatedCode, currentWorkflow]);

  const generateCode = async () => {
    if (!currentWorkflow) return;

    setIsGenerating(true);
    try {
      const generator = new AdvancedCodeGenerator(currentWorkflow);
      const result = generator.generateStrategy();
      setCode(result);
      runSecurityScan(result);
    } catch (error) {
      console.error('Code generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const runSecurityScan = async (codeToScan: GeneratedCode) => {
    setIsScanning(true);
    try {
      const scanner = new CodeSecurityScanner();
      const scanResult = scanner.scanCode(codeToScan);
      setSecurityScan(scanResult);
    } catch (error) {
      console.error('Security scan failed:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const handleCopyToClipboard = async (content: string, section: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedSection(section);
      setTimeout(() => setCopiedSection(null), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const handleDownloadFile = (content: string, filename: string, type: string = 'text/plain') => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const renderCodeBlock = (content: string, language: string = 'python') => {
    const lines = content.split('\n');
    
    return (
      <div className="relative">
        <div className="absolute top-2 right-2 z-10">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowLineNumbers(!showLineNumbers)}
            className="h-8 w-8 p-0"
          >
            {showLineNumbers ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </Button>
        </div>
        <pre className="bg-muted/50 rounded-lg p-4 text-sm overflow-x-auto">
          <code className={`language-${language}`}>
            {showLineNumbers ? (
              lines.map((line, index) => (
                <div key={index} className="flex">
                  <span className="select-none text-muted-foreground mr-4 text-right w-8">
                    {index + 1}
                  </span>
                  <span className="flex-1">{line}</span>
                </div>
              ))
            ) : (
              content
            )}
          </code>
        </pre>
      </div>
    );
  };

  const getSecurityIcon = () => {
    if (!securityScan) return <Shield className="h-5 w-5 text-gray-500" />;
    
    if (securityScan.summary.critical > 0) {
      return <XCircle className="h-5 w-5 text-red-500" />;
    } else if (securityScan.summary.high > 0) {
      return <ShieldAlert className="h-5 w-5 text-orange-500" />;
    } else if (securityScan.summary.medium > 0) {
      return <ShieldAlert className="h-5 w-5 text-yellow-500" />;
    } else {
      return <ShieldCheck className="h-5 w-5 text-green-500" />;
    }
  };

  const getSecurityStatus = () => {
    if (!securityScan) return 'Scanning...';
    return securityScan.isSecure ? 'Secure' : 'Issues Found';
  };

  const renderMetrics = () => {
    if (!code) return null;

    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center space-x-3">
              <Zap className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium">Complexity</p>
                <p className="text-2xl font-bold">{code.metadata.complexity}</p>
                <p className="text-xs text-muted-foreground">
                  {code.metadata.complexity < 100 ? 'Simple' : 
                   code.metadata.complexity < 500 ? 'Moderate' : 'Complex'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center space-x-3">
              <Settings className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">Execution Time</p>
                <p className="text-2xl font-bold">{code.metadata.estimatedPerformance.executionTime}</p>
                <p className="text-xs text-muted-foreground">Estimated</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center space-x-3">
              <FileText className="h-5 w-5 text-purple-500" />
              <div>
                <p className="text-sm font-medium">Memory Usage</p>
                <p className="text-2xl font-bold">{code.metadata.estimatedPerformance.memoryUsage}</p>
                <p className="text-xs text-muted-foreground">Estimated</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center space-x-3">
              {isScanning ? (
                <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />
              ) : (
                getSecurityIcon()
              )}
              <div>
                <p className="text-sm font-medium">Security</p>
                <p className="text-2xl font-bold">
                  {securityScan ? `${100 - securityScan.overallRiskScore}%` : '--'}
                </p>
                <p className="text-xs text-muted-foreground">
                  {isScanning ? 'Scanning...' : getSecurityStatus()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className={`w-full max-w-6xl max-h-[90vh] ${className}`}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl font-semibold flex items-center space-x-2">
              <Code2 className="h-6 w-6 text-blue-500" />
              <span>Generated Trading Strategy</span>
              {code && (
                <Badge variant="outline" className="ml-2">
                  {code.metadata.name}
                </Badge>
              )}
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={generateCode}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                {isGenerating ? 'Generating...' : 'Regenerate'}
              </Button>
              <Button variant="outline" size="sm" onClick={onClose}>
                Close
              </Button>
            </div>
          </div>

          {code && (
            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
              <span>Generated: {new Date(code.metadata.generatedAt).toLocaleString()}</span>
              <span>•</span>
              <span>Version: {code.metadata.version}</span>
              <span>•</span>
              <span>Author: {code.metadata.author}</span>
            </div>
          )}
        </CardHeader>

        <CardContent className="p-0">
          {isGenerating ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center space-y-3">
                <RefreshCw className="h-12 w-12 mx-auto text-blue-500 animate-spin" />
                <div>
                  <h3 className="font-medium">Generating Trading Strategy</h3>
                  <p className="text-sm text-muted-foreground">
                    Converting your workflow into Python code...
                  </p>
                </div>
              </div>
            </div>
          ) : code ? (
            <div className="px-6 pb-6">
              {renderMetrics()}

              <Tabs defaultValue="strategy" className="w-full">
                <TabsList className="grid w-full grid-cols-7">
                  <TabsTrigger value="strategy">Strategy</TabsTrigger>
                  <TabsTrigger value="security">
                    <div className="flex items-center space-x-1">
                      {getSecurityIcon()}
                      <span>Security</span>
                    </div>
                  </TabsTrigger>
                  <TabsTrigger value="requirements">Requirements</TabsTrigger>
                  <TabsTrigger value="tests">Tests</TabsTrigger>
                  <TabsTrigger value="docs">Documentation</TabsTrigger>
                  <TabsTrigger value="classes">Classes</TabsTrigger>
                  <TabsTrigger value="functions">Functions</TabsTrigger>
                </TabsList>

                <TabsContent value="security" className="mt-4">
                  <div className="space-y-6">
                    {/* Security Overview */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-base flex items-center space-x-2">
                            {getSecurityIcon()}
                            <span>Security Score</span>
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-center">
                            <div className="text-3xl font-bold mb-2">
                              {securityScan ? `${100 - securityScan.overallRiskScore}%` : '--'}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {securityScan ? (securityScan.isSecure ? 'Secure Code' : 'Security Issues Found') : 'Scanning...'}
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-base">Issue Summary</CardTitle>
                        </CardHeader>
                        <CardContent>
                          {securityScan ? (
                            <div className="space-y-2">
                              <div className="flex justify-between">
                                <span className="flex items-center space-x-1">
                                  <XCircle className="h-4 w-4 text-red-500" />
                                  <span className="text-sm">Critical</span>
                                </span>
                                <Badge variant={securityScan.summary.critical > 0 ? "destructive" : "secondary"}>
                                  {securityScan.summary.critical}
                                </Badge>
                              </div>
                              <div className="flex justify-between">
                                <span className="flex items-center space-x-1">
                                  <AlertTriangle className="h-4 w-4 text-orange-500" />
                                  <span className="text-sm">High</span>
                                </span>
                                <Badge variant={securityScan.summary.high > 0 ? "destructive" : "secondary"}>
                                  {securityScan.summary.high}
                                </Badge>
                              </div>
                              <div className="flex justify-between">
                                <span className="flex items-center space-x-1">
                                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                                  <span className="text-sm">Medium</span>
                                </span>
                                <Badge variant={securityScan.summary.medium > 0 ? "destructive" : "secondary"}>
                                  {securityScan.summary.medium}
                                </Badge>
                              </div>
                              <div className="flex justify-between">
                                <span className="flex items-center space-x-1">
                                  <Info className="h-4 w-4 text-blue-500" />
                                  <span className="text-sm">Low</span>
                                </span>
                                <Badge variant="secondary">
                                  {securityScan.summary.low}
                                </Badge>
                              </div>
                            </div>
                          ) : (
                            <div className="text-center py-4">
                              <RefreshCw className="h-8 w-8 mx-auto text-blue-500 animate-spin mb-2" />
                              <p className="text-sm text-muted-foreground">Scanning for security issues...</p>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>

                    {/* Security Issues */}
                    {securityScan && securityScan.issues.length > 0 && (
                      <div>
                        <h4 className="text-lg font-medium mb-4">Security Issues</h4>
                        <div className="space-y-3">
                          {securityScan.issues.map((issue) => (
                            <Card key={issue.id} className={`border-l-4 ${
                              issue.riskLevel === SecurityRiskLevel.CRITICAL ? 'border-l-red-500' :
                              issue.riskLevel === SecurityRiskLevel.HIGH ? 'border-l-orange-500' :
                              issue.riskLevel === SecurityRiskLevel.MEDIUM ? 'border-l-yellow-500' :
                              'border-l-blue-500'
                            }`}>
                              <CardContent className="pt-4">
                                <div className="flex items-start space-x-3">
                                  <div className="flex-shrink-0">
                                    {issue.riskLevel === SecurityRiskLevel.CRITICAL ? (
                                      <XCircle className="h-5 w-5 text-red-500" />
                                    ) : issue.riskLevel === SecurityRiskLevel.HIGH ? (
                                      <AlertTriangle className="h-5 w-5 text-orange-500" />
                                    ) : issue.riskLevel === SecurityRiskLevel.MEDIUM ? (
                                      <AlertTriangle className="h-5 w-5 text-yellow-500" />
                                    ) : (
                                      <Info className="h-5 w-5 text-blue-500" />
                                    )}
                                  </div>
                                  <div className="flex-1">
                                    <div className="flex items-center space-x-2 mb-1">
                                      <h5 className="font-medium">{issue.title}</h5>
                                      <Badge variant={
                                        issue.riskLevel === SecurityRiskLevel.CRITICAL ? "destructive" :
                                        issue.riskLevel === SecurityRiskLevel.HIGH ? "destructive" :
                                        issue.riskLevel === SecurityRiskLevel.MEDIUM ? "default" :
                                        "secondary"
                                      }>
                                        {issue.riskLevel.toUpperCase()}
                                      </Badge>
                                      {issue.cweId && (
                                        <Badge variant="outline" className="text-xs">
                                          {issue.cweId}
                                        </Badge>
                                      )}
                                    </div>
                                    <p className="text-sm text-muted-foreground mb-2">
                                      {issue.description}
                                    </p>
                                    <div className="text-xs text-muted-foreground mb-2">
                                      📍 Line {issue.location.line} in {issue.location.context}
                                      {issue.location.function && ` (${issue.location.function})`}
                                    </div>
                                    <div className="bg-muted/50 p-2 rounded text-xs mb-2">
                                      💡 <strong>Recommendation:</strong> {issue.recommendation}
                                    </div>
                                    <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                                      <span>Severity: {issue.severity}/10</span>
                                      <span>Confidence: {issue.confidence}/10</span>
                                    </div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Security Recommendations */}
                    {securityScan && securityScan.recommendations.length > 0 && (
                      <div>
                        <h4 className="text-lg font-medium mb-4">Security Recommendations</h4>
                        <Card>
                          <CardContent className="pt-4">
                            <div className="space-y-2">
                              {securityScan.recommendations.map((recommendation, index) => (
                                <div key={index} className="flex items-start space-x-2">
                                  <span className="text-green-500 mt-1">✓</span>
                                  <span className="text-sm">{recommendation}</span>
                                </div>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    )}

                    {/* Scan Details */}
                    {securityScan && (
                      <div>
                        <h4 className="text-lg font-medium mb-4">Scan Details</h4>
                        <Card>
                          <CardContent className="pt-4">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              <div>
                                <span className="text-muted-foreground">Scan Time:</span>
                                <div className="font-medium">{securityScan.scanDuration}ms</div>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Scanner Version:</span>
                                <div className="font-medium">{securityScan.scannerVersion}</div>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Risk Score:</span>
                                <div className="font-medium">{securityScan.overallRiskScore}/100</div>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Scanned At:</span>
                                <div className="font-medium">{securityScan.scanTimestamp.toLocaleTimeString()}</div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="strategy" className="mt-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-lg font-medium">Complete Trading Strategy</h4>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleCopyToClipboard(code.strategy, 'strategy')}
                        >
                          {copiedSection === 'strategy' ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                          Copy
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownloadFile(
                            code.strategy, 
                            `${code.metadata.name.toLowerCase().replace(/\s+/g, '_')}_strategy.py`,
                            'text/python'
                          )}
                        >
                          <Download className="h-4 w-4" />
                          Download
                        </Button>
                      </div>
                    </div>
                    <ScrollArea className="h-96">
                      {renderCodeBlock(code.strategy)}
                    </ScrollArea>
                  </div>
                </TabsContent>

                <TabsContent value="requirements" className="mt-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-lg font-medium">Requirements.txt</h4>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleCopyToClipboard(code.requirements.join('\n'), 'requirements')}
                        >
                          {copiedSection === 'requirements' ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                          Copy
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownloadFile(
                            code.requirements.join('\n'), 
                            'requirements.txt',
                            'text/plain'
                          )}
                        >
                          <Download className="h-4 w-4" />
                          Download
                        </Button>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {code.requirements.map((req, index) => (
                        <Badge key={index} variant="secondary" className="justify-start">
                          {req}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="tests" className="mt-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-lg font-medium">Unit Tests</h4>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleCopyToClipboard(code.tests, 'tests')}
                        >
                          {copiedSection === 'tests' ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                          Copy
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownloadFile(
                            code.tests, 
                            `test_${code.metadata.name.toLowerCase().replace(/\s+/g, '_')}.py`,
                            'text/python'
                          )}
                        >
                          <Download className="h-4 w-4" />
                          Download
                        </Button>
                      </div>
                    </div>
                    <ScrollArea className="h-96">
                      {renderCodeBlock(code.tests)}
                    </ScrollArea>
                  </div>
                </TabsContent>

                <TabsContent value="docs" className="mt-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-lg font-medium">Documentation</h4>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleCopyToClipboard(code.documentation, 'docs')}
                        >
                          {copiedSection === 'docs' ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                          Copy
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownloadFile(
                            code.documentation, 
                            `${code.metadata.name.toLowerCase().replace(/\s+/g, '_')}_README.md`,
                            'text/markdown'
                          )}
                        >
                          <Download className="h-4 w-4" />
                          Download
                        </Button>
                      </div>
                    </div>
                    <ScrollArea className="h-96">
                      {renderCodeBlock(code.documentation, 'markdown')}
                    </ScrollArea>
                  </div>
                </TabsContent>

                <TabsContent value="classes" className="mt-4">
                  <div className="space-y-4">
                    <h4 className="text-lg font-medium">Generated Classes</h4>
                    {code.classes.map((cls, index) => (
                      <Card key={index}>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-base">{cls.name}</CardTitle>
                          <p className="text-sm text-muted-foreground">{cls.description}</p>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div>
                              <h5 className="text-sm font-medium mb-2">Methods ({cls.methods.length})</h5>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                {cls.methods.map((method, methodIndex) => (
                                  <Badge key={methodIndex} variant="outline">
                                    {method.name}() → {method.returnType}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                            <Separator />
                            <div>
                              <h5 className="text-sm font-medium mb-2">Properties ({cls.properties.length})</h5>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                {cls.properties.map((prop, propIndex) => (
                                  <Badge key={propIndex} variant="secondary">
                                    {prop.name}: {prop.type}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="functions" className="mt-4">
                  <div className="space-y-4">
                    <h4 className="text-lg font-medium">Helper Functions</h4>
                    {code.functions.map((func, index) => (
                      <Card key={index}>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-base flex items-center space-x-2">
                            <span>{func.name}()</span>
                            <Badge variant="outline">{func.returnType}</Badge>
                          </CardTitle>
                          <p className="text-sm text-muted-foreground">{func.description}</p>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <h5 className="text-sm font-medium">Parameters</h5>
                            {func.parameters.length > 0 ? (
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                {func.parameters.map((param, paramIndex) => (
                                  <Badge key={paramIndex} variant="secondary">
                                    {param.name}: {param.type}
                                  </Badge>
                                ))}
                              </div>
                            ) : (
                              <p className="text-sm text-muted-foreground">No parameters</p>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          ) : (
            <div className="flex items-center justify-center py-20">
              <div className="text-center space-y-3">
                <XCircle className="h-12 w-12 mx-auto text-red-500" />
                <div>
                  <h3 className="font-medium">Code Generation Failed</h3>
                  <p className="text-sm text-muted-foreground">
                    Unable to generate code from the current workflow
                  </p>
                </div>
                <Button onClick={generateCode} variant="outline">
                  Try Again
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}