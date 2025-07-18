'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { noCodeApiClient, WorkflowVersion, WorkflowVersionDetails } from '@/lib/api/no-code-api';
import { 
  Clock, 
  GitBranch, 
  Eye, 
  RotateCcw, 
  Copy, 
  Trash2, 
  Plus,
  GitCommit,
  Calendar,
  User,
  FileText,
  GitMerge
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface VersionHistoryPanelProps {
  workflowId: string;
  currentVersion: number;
  onVersionRestore?: (version: number) => void;
  onVersionCreate?: () => void;
}

interface VersionActivity {
  id: string;
  action_type: string;
  description: string;
  user_name?: string;
  version?: number;
  timestamp: string;
  metadata?: Record<string, any>;
}

const VersionHistoryPanel: React.FC<VersionHistoryPanelProps> = ({
  workflowId,
  currentVersion,
  onVersionRestore,
  onVersionCreate
}) => {
  const [versions, setVersions] = useState<WorkflowVersion[]>([]);
  const [activities, setActivities] = useState<VersionActivity[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<WorkflowVersionDetails | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingVersion, setIsCreatingVersion] = useState(false);
  const [compareVersions, setCompareVersions] = useState<{from: number; to: number} | null>(null);
  const [newVersionName, setNewVersionName] = useState('');
  const [newVersionSummary, setNewVersionSummary] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showCompareDialog, setShowCompareDialog] = useState(false);
  const { toast } = useToast();

  const loadVersions = useCallback(async () => {
    if (!workflowId) return;
    
    setIsLoading(true);
    try {
      const [versionsData, historyData] = await Promise.all([
        noCodeApiClient.getVersions(workflowId),
        noCodeApiClient.getWorkflowHistory(workflowId, { limit: 20 })
      ]);
      
      setVersions(versionsData);
      setActivities(historyData.activities);
    } catch (error) {
      console.error('Error loading versions:', error);
      toast({
        title: "Error",
        description: "Failed to load version history",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [workflowId, toast]);

  useEffect(() => {
    loadVersions();
  }, [loadVersions]);

  const handleCreateVersion = async () => {
    if (!workflowId) return;
    
    setIsCreatingVersion(true);
    try {
      await noCodeApiClient.createVersion(workflowId, {
        name: newVersionName || `Version ${versions.length + 1}`,
        changes_summary: newVersionSummary
      });
      
      toast({
        title: "Success",
        description: "Version created successfully",
      });
      
      setNewVersionName('');
      setNewVersionSummary('');
      setShowCreateDialog(false);
      await loadVersions();
      onVersionCreate?.();
    } catch (error) {
      console.error('Error creating version:', error);
      toast({
        title: "Error",
        description: "Failed to create version",
        variant: "destructive",
      });
    } finally {
      setIsCreatingVersion(false);
    }
  };

  const handleRestoreVersion = async (version: number) => {
    if (!workflowId) return;
    
    try {
      await noCodeApiClient.restoreVersion(workflowId, version);
      
      toast({
        title: "Success",
        description: `Restored to version ${version}`,
      });
      
      await loadVersions();
      onVersionRestore?.(version);
    } catch (error) {
      console.error('Error restoring version:', error);
      toast({
        title: "Error",
        description: "Failed to restore version",
        variant: "destructive",
      });
    }
  };

  const handleViewVersion = async (version: number) => {
    try {
      const versionDetails = await noCodeApiClient.getVersion(workflowId, version);
      setSelectedVersion(versionDetails);
    } catch (error) {
      console.error('Error loading version details:', error);
      toast({
        title: "Error",
        description: "Failed to load version details",
        variant: "destructive",
      });
    }
  };

  const handleDeleteVersion = async (version: number) => {
    if (!workflowId) return;
    
    try {
      await noCodeApiClient.deleteVersion(workflowId, version);
      
      toast({
        title: "Success",
        description: `Version ${version} deleted`,
      });
      
      await loadVersions();
    } catch (error) {
      console.error('Error deleting version:', error);
      toast({
        title: "Error",
        description: "Failed to delete version",
        variant: "destructive",
      });
    }
  };

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'created':
        return <Plus className="h-4 w-4" />;
      case 'updated':
        return <FileText className="h-4 w-4" />;
      case 'executed':
        return <GitCommit className="h-4 w-4" />;
      case 'versioned':
        return <GitBranch className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getActionColor = (actionType: string) => {
    switch (actionType) {
      case 'created':
        return 'bg-green-100 text-green-800';
      case 'updated':
        return 'bg-blue-100 text-blue-800';
      case 'executed':
        return 'bg-purple-100 text-purple-800';
      case 'versioned':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">Version History</h3>
          <p className="text-sm text-muted-foreground">
            Track changes and manage versions of your workflow
          </p>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Create Version
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Version</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Version Name</label>
                <Input
                  placeholder={`Version ${versions.length + 1}`}
                  value={newVersionName}
                  onChange={(e) => setNewVersionName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Summary of Changes</label>
                <Textarea
                  placeholder="Describe what changed in this version..."
                  value={newVersionSummary}
                  onChange={(e) => setNewVersionSummary(e.target.value)}
                  rows={3}
                />
              </div>
            </div>
            <div className="flex justify-end space-x-2">
              <Button 
                variant="outline" 
                onClick={() => setShowCreateDialog(false)}
              >
                Cancel
              </Button>
              <Button 
                onClick={handleCreateVersion}
                disabled={isCreatingVersion}
              >
                {isCreatingVersion ? 'Creating...' : 'Create Version'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Versions List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              Versions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              {isLoading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="text-sm text-muted-foreground">Loading versions...</div>
                </div>
              ) : versions.length === 0 ? (
                <div className="flex items-center justify-center h-32">
                  <div className="text-sm text-muted-foreground">No versions yet</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {versions.map((version) => (
                    <div
                      key={version.id}
                      className={`p-3 rounded-lg border ${
                        version.version === currentVersion 
                          ? 'border-primary bg-primary/5' 
                          : 'border-border hover:bg-accent'
                      } transition-colors`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant={version.version === currentVersion ? 'default' : 'secondary'}>
                            v{version.version}
                          </Badge>
                          {version.version === currentVersion && (
                            <Badge variant="outline" className="text-xs">Current</Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleViewVersion(version.version)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {version.version !== currentVersion && (
                            <>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleRestoreVersion(version.version)}
                              >
                                <RotateCcw className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleDeleteVersion(version.version)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                      
                      <div className="mt-2">
                        <div className="font-medium text-sm">{version.name}</div>
                        {version.changes_summary && (
                          <div className="text-xs text-muted-foreground mt-1">
                            {version.changes_summary}
                          </div>
                        )}
                        <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          {formatDistanceToNow(new Date(version.created_at), { addSuffix: true })}
                          {version.created_by && (
                            <>
                              <User className="h-3 w-3 ml-2" />
                              {version.created_by}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Activity Timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              {activities.length === 0 ? (
                <div className="flex items-center justify-center h-32">
                  <div className="text-sm text-muted-foreground">No recent activity</div>
                </div>
              ) : (
                <div className="space-y-4">
                  {activities.map((activity, index) => (
                    <div key={activity.id} className="flex gap-3">
                      <div className={`
                        flex items-center justify-center w-8 h-8 rounded-full
                        ${getActionColor(activity.action_type)}
                      `}>
                        {getActionIcon(activity.action_type)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="text-sm">
                          <span className="font-medium">{activity.description}</span>
                          {activity.version && (
                            <Badge variant="outline" className="ml-2 text-xs">
                              v{activity.version}
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                          <span>{formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}</span>
                          {activity.user_name && (
                            <>
                              <span>•</span>
                              <span>{activity.user_name}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Version Comparison */}
      {versions.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitMerge className="h-5 w-5" />
              Compare Versions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">From Version</label>
                <select 
                  className="w-32 px-3 py-2 border border-input rounded-md"
                  value={compareVersions?.from || ''}
                  onChange={(e) => setCompareVersions(prev => ({ 
                    ...prev, 
                    from: parseInt(e.target.value),
                    to: prev?.to || currentVersion 
                  }))}
                >
                  <option value="">Select</option>
                  {versions.map(v => (
                    <option key={v.id} value={v.version}>v{v.version}</option>
                  ))}
                </select>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">To Version</label>
                <select 
                  className="w-32 px-3 py-2 border border-input rounded-md"
                  value={compareVersions?.to || currentVersion}
                  onChange={(e) => setCompareVersions(prev => ({ 
                    ...prev, 
                    from: prev?.from || 1,
                    to: parseInt(e.target.value) 
                  }))}
                >
                  <option value="">Select</option>
                  {versions.map(v => (
                    <option key={v.id} value={v.version}>v{v.version}</option>
                  ))}
                </select>
              </div>
              
              <Button
                disabled={!compareVersions?.from || !compareVersions?.to}
                onClick={() => setShowCompareDialog(true)}
                className="mt-6"
              >
                Compare
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Version Details Dialog */}
      {selectedVersion && (
        <Dialog open={!!selectedVersion} onOpenChange={() => setSelectedVersion(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Version {selectedVersion.version} Details</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium">Workflow Information</h4>
                <div className="grid grid-cols-2 gap-4 mt-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Name:</span> {selectedVersion.name}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Version:</span> {selectedVersion.version}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Created:</span> {new Date(selectedVersion.created_at).toLocaleString()}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Updated:</span> {new Date(selectedVersion.updated_at).toLocaleString()}
                  </div>
                </div>
              </div>
              
              <Separator />
              
              <div>
                <h4 className="font-medium">Workflow Structure</h4>
                <div className="grid grid-cols-2 gap-4 mt-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Nodes:</span> {selectedVersion.workflow_data.nodes.length}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Connections:</span> {selectedVersion.workflow_data.edges.length}
                  </div>
                </div>
              </div>
              
              {selectedVersion.description && (
                <>
                  <Separator />
                  <div>
                    <h4 className="font-medium">Description</h4>
                    <p className="text-sm text-muted-foreground mt-2">
                      {selectedVersion.description}
                    </p>
                  </div>
                </>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default VersionHistoryPanel;