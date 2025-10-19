"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";

// Disable static generation for this page as it uses searchParams
export const dynamic = 'force-dynamic';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  useExecutionStore,
  useTrainingJob,
} from "@/lib/stores/execution-store";
import { noCodeApiClient } from "@/lib/api/no-code-api";
import { getToken } from "@/lib/auth";
import {
  ArrowLeft,
  Download,
  Play,
  Copy,
  ExternalLink,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Code,
  BarChart3,
  Settings,
  Share,
} from "lucide-react";

interface ExecutionResultsPageParams extends Record<string, string> {
  id: string; // workflow id
  executionType: "strategy" | "training";
}

interface StrategyResults {
  strategyCode: string;
  executionConfig: any;
  metadata: {
    generated_at: string;
    code_lines: number;
    complexity_score: number;
    validation_passed: boolean;
  };
  backtestResults?: {
    totalReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
  };
}

interface TrainingResults {
  jobId: string;
  finalMetrics: {
    bestParameters: Record<string, any>;
    performanceMetrics: {
      sharpeRatio: number;
      sortinoRatio: number;
      calmarRatio: number;
      maxDrawdown: number;
      totalReturn: number;
      winRate: number;
      profitFactor: number;
    };
    validationMetrics: {
      outOfSampleSharpe?: number;
      walkForwardStability?: number;
      monteCarloConfidence?: number;
    };
  };
  optimizationSummary: {
    totalTrials: number;
    bestTrial: number;
    improvementOverDefault: number;
    trainingDurationMinutes: number;
  };
  generatedStrategyCode?: string;
}

export default function ExecutionResultsPage() {
  const params = useParams<ExecutionResultsPageParams>();
  const router = useRouter();
  const searchParams = useSearchParams();

  const workflowId = params.id;
  const executionType = params.executionType;

  const [results, setResults] = useState<
    StrategyResults | TrainingResults | null
  >(null);
  const [workflowName, setWorkflowName] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("overview");

  const jobId = searchParams.get("jobId");
  const executionId = searchParams.get("executionId");

  const trainingJob = useTrainingJob(jobId);
  const { setExecutionStatus, getExecutionRecord } = useExecutionStore();

  useEffect(() => {
    setExecutionStatus("completed");
    loadResults();
  }, [workflowId, executionType, jobId]);

  const loadResults = async () => {
    try {
      setIsLoading(true);

      if (executionType === "strategy") {
        await loadStrategyResults();
      } else if (executionType === "training") {
        await loadTrainingResults();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load results");
    } finally {
      setIsLoading(false);
    }
  };

  const loadStrategyResults = async () => {
    // Try to get results from execution record first
    if (executionId) {
      const record = getExecutionRecord(executionId);
      if (record?.results) {
        setResults(record.results);
        setWorkflowName(record.workflowName);
        return;
      }
    }

    // Get workflow with generated code using the API client
    const workflow = await noCodeApiClient.getWorkflow(workflowId);
    const data = {
      strategyCode: workflow.generated_code || "",
      workflowName: workflow.name,
      executionConfig: workflow.execution_metadata || {},
      metadata: {
        generated_at: workflow.updated_at,
        code_lines: workflow.generated_code?.split("\n").length || 0,
        complexity_score: 75, // Could be calculated from workflow complexity
        validation_passed: workflow.validation_status === "valid",
      },
    };
    setResults(data);
    setWorkflowName(data.workflowName || `Workflow ${workflowId}`);
  };

  const loadTrainingResults = async () => {
    if (!jobId) {
      throw new Error("Training job ID is required");
    }

    // Check if we have results in training job store
    if (trainingJob?.status === "completed") {
      // Fetch detailed results
      const token = getToken();
      const response = await fetch(`/api/training/jobs/${jobId}/results`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      if (!response.ok) {
        throw new Error("Failed to load training results");
      }

      const data = await response.json();
      setResults(data);
      setWorkflowName(trainingJob.workflowName);
    } else {
      throw new Error("Training job not completed or not found");
    }
  };

  const handleDownloadResults = () => {
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${executionType}_results_${workflowId}_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleCopyCode = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      // Could add a toast notification here
    } catch (err) {
      console.error("Failed to copy code:", err);
    }
  };

  const handleRunAgain = () => {
    router.push(`/workflows/${workflowId}/execute?from=results`);
  };

  const handleBackToWorkflow = () => {
    router.push(`/strategy-hub?workflow=${workflowId}`);
  };

  const handleDeployStrategy = () => {
    // Navigate to deployment flow
    router.push(
      `/workflows/${workflowId}/deploy${jobId ? `?jobId=${jobId}` : ""}`,
    );
  };

  const renderStrategyResults = (results: StrategyResults) => (
    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="code">Strategy Code</TabsTrigger>
        <TabsTrigger value="backtest">Backtest</TabsTrigger>
        <TabsTrigger value="config">Configuration</TabsTrigger>
      </TabsList>

      <TabsContent value="overview" className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span>Strategy Generated</span>
              </CardTitle>
              <CardDescription>
                Your strategy code was successfully generated
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Lines of Code:</span>
                  <Badge variant="outline">{results.metadata.code_lines}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Complexity Score:</span>
                  <Badge variant="outline">
                    {results.metadata.complexity_score}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Validation:</span>
                  <Badge
                    className={
                      results.metadata.validation_passed
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                    }
                  >
                    {results.metadata.validation_passed ? "Passed" : "Failed"}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Generated:</span>
                  <span className="text-sm text-muted-foreground">
                    {new Date(results.metadata.generated_at).toLocaleString()}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {results.backtestResults && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5 text-blue-600" />
                  <span>Quick Backtest</span>
                </CardTitle>
                <CardDescription>
                  Performance with default parameters
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Total Return:</span>
                    <Badge variant="outline">
                      {(results.backtestResults.totalReturn * 100).toFixed(2)}%
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Sharpe Ratio:</span>
                    <Badge variant="outline">
                      {results.backtestResults.sharpeRatio.toFixed(2)}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Max Drawdown:</span>
                    <Badge variant="outline">
                      {(results.backtestResults.maxDrawdown * 100).toFixed(2)}%
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Win Rate:</span>
                    <Badge variant="outline">
                      {(results.backtestResults.winRate * 100).toFixed(1)}%
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </TabsContent>

      <TabsContent value="code" className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Generated Strategy Code</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleCopyCode(results.strategyCode)}
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy Code
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96 w-full border rounded p-4">
              <pre className="text-sm font-mono whitespace-pre-wrap">
                <code>{results.strategyCode}</code>
              </pre>
            </ScrollArea>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="backtest" className="space-y-4">
        {results.backtestResults ? (
          <Card>
            <CardHeader>
              <CardTitle>Backtest Results</CardTitle>
              <CardDescription>
                Performance analysis with your parameters
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p>Detailed backtest results would be displayed here...</p>
            </CardContent>
          </Card>
        ) : (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              No backtest results available. Run the strategy through our
              backtesting engine for detailed performance analysis.
            </AlertDescription>
          </Alert>
        )}
      </TabsContent>

      <TabsContent value="config" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Execution Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-60 w-full">
              <pre className="text-sm whitespace-pre-wrap">
                {JSON.stringify(results.executionConfig, null, 2)}
              </pre>
            </ScrollArea>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );

  const renderTrainingResults = (results: TrainingResults) => (
    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="parameters">Best Parameters</TabsTrigger>
        <TabsTrigger value="performance">Performance</TabsTrigger>
        <TabsTrigger value="code">Optimized Code</TabsTrigger>
      </TabsList>

      <TabsContent value="overview" className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <span>Optimization Complete</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Total Trials:</span>
                  <Badge variant="outline">
                    {results.optimizationSummary.totalTrials}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Best Trial:</span>
                  <Badge variant="outline">
                    #{results.optimizationSummary.bestTrial}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Training Time:</span>
                  <Badge variant="outline">
                    {Math.round(
                      results.optimizationSummary.trainingDurationMinutes,
                    )}
                    m
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Improvement:</span>
                  <Badge className="bg-green-100 text-green-800">
                    +
                    {(
                      results.optimizationSummary.improvementOverDefault * 100
                    ).toFixed(1)}
                    %
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Sharpe Ratio:</span>
                  <Badge variant="outline">
                    {results.finalMetrics.performanceMetrics.sharpeRatio.toFixed(
                      2,
                    )}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Total Return:</span>
                  <Badge variant="outline">
                    {(
                      results.finalMetrics.performanceMetrics.totalReturn * 100
                    ).toFixed(2)}
                    %
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Win Rate:</span>
                  <Badge variant="outline">
                    {(
                      results.finalMetrics.performanceMetrics.winRate * 100
                    ).toFixed(1)}
                    %
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Max Drawdown:</span>
                  <Badge variant="outline">
                    {(
                      results.finalMetrics.performanceMetrics.maxDrawdown * 100
                    ).toFixed(2)}
                    %
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {results.finalMetrics.validationMetrics && (
            <Card>
              <CardHeader>
                <CardTitle>Validation</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {results.finalMetrics.validationMetrics.outOfSampleSharpe && (
                    <div className="flex justify-between">
                      <span>Out-of-Sample Sharpe:</span>
                      <Badge variant="outline">
                        {results.finalMetrics.validationMetrics.outOfSampleSharpe.toFixed(
                          2,
                        )}
                      </Badge>
                    </div>
                  )}
                  {results.finalMetrics.validationMetrics
                    .walkForwardStability && (
                    <div className="flex justify-between">
                      <span>Stability Score:</span>
                      <Badge variant="outline">
                        {results.finalMetrics.validationMetrics.walkForwardStability.toFixed(
                          2,
                        )}
                      </Badge>
                    </div>
                  )}
                  {results.finalMetrics.validationMetrics
                    .monteCarloConfidence && (
                    <div className="flex justify-between">
                      <span>Confidence:</span>
                      <Badge variant="outline">
                        {(
                          results.finalMetrics.validationMetrics
                            .monteCarloConfidence * 100
                        ).toFixed(0)}
                        %
                      </Badge>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </TabsContent>

      <TabsContent value="parameters" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Optimized Parameters</CardTitle>
            <CardDescription>
              The best parameter values found during optimization
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(results.finalMetrics.bestParameters).map(
                ([key, value]) => (
                  <div
                    key={key}
                    className="flex justify-between items-center p-3 bg-muted/20 rounded"
                  >
                    <span className="font-medium capitalize">
                      {key.replace(/_/g, " ")}
                    </span>
                    <Badge variant="outline">
                      {typeof value === "number"
                        ? value.toFixed(4)
                        : String(value)}
                    </Badge>
                  </div>
                ),
              )}
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="performance" className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Risk Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Sharpe Ratio:</span>
                  <span className="font-mono">
                    {results.finalMetrics.performanceMetrics.sharpeRatio.toFixed(
                      3,
                    )}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Sortino Ratio:</span>
                  <span className="font-mono">
                    {results.finalMetrics.performanceMetrics.sortinoRatio.toFixed(
                      3,
                    )}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Calmar Ratio:</span>
                  <span className="font-mono">
                    {results.finalMetrics.performanceMetrics.calmarRatio.toFixed(
                      3,
                    )}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Return Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Total Return:</span>
                  <span className="font-mono">
                    {(
                      results.finalMetrics.performanceMetrics.totalReturn * 100
                    ).toFixed(2)}
                    %
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Win Rate:</span>
                  <span className="font-mono">
                    {(
                      results.finalMetrics.performanceMetrics.winRate * 100
                    ).toFixed(1)}
                    %
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Profit Factor:</span>
                  <span className="font-mono">
                    {results.finalMetrics.performanceMetrics.profitFactor.toFixed(
                      2,
                    )}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="code" className="space-y-4">
        {results.generatedStrategyCode ? (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Optimized Strategy Code</CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopyCode(results.generatedStrategyCode!)}
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy Code
                </Button>
              </div>
              <CardDescription>
                Strategy code with optimized parameters
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96 w-full border rounded p-4">
                <pre className="text-sm font-mono whitespace-pre-wrap">
                  <code>{results.generatedStrategyCode}</code>
                </pre>
              </ScrollArea>
            </CardContent>
          </Card>
        ) : (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Optimized strategy code is being generated. Please check back in a
              moment.
            </AlertDescription>
          </Alert>
        )}
      </TabsContent>
    </Tabs>
  );

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center space-y-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-muted-foreground">Loading results...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="container mx-auto py-8">
        <div className="max-w-2xl mx-auto">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error || "Results not found"}</AlertDescription>
          </Alert>
          <div className="mt-4 flex space-x-2">
            <Button variant="outline" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
            <Button onClick={() => window.location.reload()}>Try Again</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" onClick={handleBackToWorkflow}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Workflow
              </Button>
              <div className="h-6 border-l border-gray-300" />
              <div>
                <h1 className="text-3xl font-bold tracking-tight">
                  {executionType === "strategy"
                    ? "Strategy Results"
                    : "Training Results"}
                </h1>
                <p className="text-muted-foreground">
                  Results for "{workflowName}"
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Button variant="outline" onClick={handleDownloadResults}>
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
              <Button variant="outline" onClick={handleRunAgain}>
                <Play className="h-4 w-4 mr-2" />
                Run Again
              </Button>
              <Button onClick={handleDeployStrategy}>
                <ExternalLink className="h-4 w-4 mr-2" />
                Deploy Strategy
              </Button>
            </div>
          </div>

          {/* Success Alert */}
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              {executionType === "strategy"
                ? "Strategy generated successfully! Your trading strategy is ready to use."
                : "Training completed successfully! Your optimized strategy parameters have been found."}
            </AlertDescription>
          </Alert>
        </div>

        {/* Results Content */}
        <div className="space-y-6">
          {executionType === "strategy"
            ? renderStrategyResults(results as StrategyResults)
            : renderTrainingResults(results as TrainingResults)}
        </div>
      </div>
    </div>
  );
}
