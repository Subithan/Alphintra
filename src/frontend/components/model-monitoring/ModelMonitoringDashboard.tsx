"use client";

import React, { useState } from 'react';
import useSWR from 'swr';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertTriangle, CheckCircle, Clock } from 'lucide-react';

// Define the types based on the backend dataclasses
interface Alert {
  description: string;
  severity: string;
  timestamp: number;
  // Add other fields from backend alerts as needed
}

interface ModelHealthStatus {
  deployment_id: number;
  health_score: number;
  status: 'healthy' | 'warning' | 'critical';
  performance_metrics: Record<string, number>;
  accuracy_metrics: Record<string, number>;
  drift_metrics: Record<string, number>;
  alerts: Alert[];
  last_updated: number;
  recommendations: string[];
}

const fetcher = (url: string) => fetch(url).then(res => res.json());

const ModelMonitoringDashboard = () => {
  const [selectedDeploymentId, setSelectedDeploymentId] = useState<number | null>(null);

  const { data: healthStatuses, error } = useSWR<ModelHealthStatus[]>('/api/monitoring/health-statuses', fetcher, {
    refreshInterval: 30000 // Refresh every 30 seconds
  });

  const selectedDeployment = healthStatuses?.find(d => d.deployment_id === selectedDeploymentId);

  if (error) return <div>Failed to load monitoring data.</div>;
  if (!healthStatuses) return <div>Loading...</div>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Model Monitoring Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Monitored Deployments</CardTitle>
            </CardHeader>
            <CardContent>
              <Select onValueChange={(value) => setSelectedDeploymentId(Number(value))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a deployment" />
                </SelectTrigger>
                <SelectContent>
                  {healthStatuses.map(d => (
                    <SelectItem key={d.deployment_id} value={String(d.deployment_id)}>
                      Deployment #{d.deployment_id} - {d.status.charAt(0).toUpperCase() + d.status.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>
        </div>

        <div className="md:col-span-2">
          {selectedDeployment ? (
            <DeploymentDetails deployment={selectedDeployment} />
          ) : (
            <Card>
              <CardContent className="p-6">
                <p>Select a deployment to view its details.</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

const DeploymentDetails = ({ deployment }: { deployment: ModelHealthStatus }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning': return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'critical': return <AlertTriangle className="h-5 w-5 text-red-500" />;
      default: return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Deployment #{deployment.deployment_id} Details
            {getStatusIcon(deployment.status)}
            <Badge variant={deployment.status === 'critical' ? 'destructive' : 'secondary'}>{deployment.status}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p>Health Score: {deployment.health_score.toFixed(2)} / 100</p>
          <p>Last Updated: {new Date(deployment.last_updated * 1000).toLocaleString()}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Performance Metrics</CardTitle></CardHeader>
        <CardContent>
          <MetricsTable metrics={deployment.performance_metrics} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Accuracy Metrics</CardTitle></CardHeader>
        <CardContent>
          <MetricsTable metrics={deployment.accuracy_metrics} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Drift Metrics</CardTitle></CardHeader>
        <CardContent>
          <MetricsTable metrics={deployment.drift_metrics} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Recent Alerts</CardTitle></CardHeader>
        <CardContent>
          <AlertsList alerts={deployment.alerts} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Recommendations</CardTitle></CardHeader>
        <CardContent>
          <ul>
            {deployment.recommendations.map((rec, index) => (
              <li key={index} className="list-disc ml-4">{rec}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

const MetricsTable = ({ metrics }: { metrics: Record<string, number> }) => {
  if (Object.keys(metrics).length === 0) return <p>No metrics available.</p>;
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Metric</TableHead>
          <TableHead>Value</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {Object.entries(metrics).map(([key, value]) => (
          <TableRow key={key}>
            <TableCell>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</TableCell>
            <TableCell>{typeof value === 'number' ? value.toFixed(4) : value}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

const AlertsList = ({ alerts }: { alerts: Alert[] }) => {
  if (alerts.length === 0) return <p>No recent alerts.</p>;
  return (
    <div className="space-y-2">
      {alerts.map((alert, index) => (
        <div key={index} className={`p-2 rounded-md ${
          alert.severity === 'high' ? 'bg-red-100' :
          alert.severity === 'medium' ? 'bg-yellow-100' : 'bg-gray-100'
        }`}>
          <p className="font-semibold">{alert.description}</p>
          <p className="text-sm text-gray-600">
            Severity: {alert.severity} - {new Date(alert.timestamp * 1000).toLocaleString()}
          </p>
        </div>
      ))}
    </div>
  );
};

export default ModelMonitoringDashboard;
