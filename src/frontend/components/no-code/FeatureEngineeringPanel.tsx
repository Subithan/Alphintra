"use client"

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, Zap, AlertCircle, CheckCircle } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

interface FeatureEngineeringPanelProps {
  workflowDefinition: object;
  datasetId: string;
  onFeaturesGenerated?: (features: string[]) => void;
}

interface FeatureEngineeringResult {
  selected_features: string[];
  generated_features_count: number;
}

export function FeatureEngineeringPanel({
  workflowDefinition,
  datasetId,
  onFeaturesGenerated,
}: FeatureEngineeringPanelProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FeatureEngineeringResult | null>(null);

  const handleGenerateFeatures = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      // The API endpoint is on a different port, so we need the full URL
      const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/feature-engineering`;

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add authorization headers if needed
          // 'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          workflow_definition: workflowDefinition,
          dataset_id: datasetId,
          n_features_to_select: 50,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate features.');
      }

      const data: FeatureEngineeringResult = await response.json();
      setResult(data);
      if (onFeaturesGenerated) {
        onFeaturesGenerated(data.selected_features);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Zap className="mr-2 h-5 w-5 text-yellow-500" />
          Automated Feature Engineering
        </CardTitle>
        <CardDescription>
          Generate and select new features to improve your model's performance.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Button onClick={handleGenerateFeatures} disabled={isLoading || !datasetId}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating Features...
              </>
            ) : (
              'Run Feature Engineering'
            )}
          </Button>
          {!datasetId && <p className="text-xs text-red-500">A dataset must be selected.</p>}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error Generating Features</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {result && (
            <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertTitle>Feature Generation Successful!</AlertTitle>
                <AlertDescription className="space-y-3 pt-2">
                    <p>
                        Generated a total of <span className="font-bold">{result.generated_features_count}</span> features
                        and selected the top <span className="font-bold">{result.selected_features.length}</span>.
                    </p>
                    <ScrollArea className="h-48 w-full rounded-md border p-4">
                        <div className="flex flex-wrap gap-2">
                        {result.selected_features.map((feature) => (
                            <Badge key={feature} variant="outline">{feature}</Badge>
                        ))}
                        </div>
                    </ScrollArea>
                </AlertDescription>
            </Alert>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
