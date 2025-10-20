"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Plus,
  FileText,
  Calendar,
  Tag,
  User,
  Code2,
  Workflow as WorkflowIcon,
  Folder,
  FileCode,
  RefreshCw,
} from "lucide-react";
import { NoCodeApiClient, Workflow } from "@/lib/api/no-code-api";
import { fileManagementApi, ProjectInfo } from "@/lib/api/file-management-api";
import { useRouter } from "next/navigation";

export default function StrategyHubPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [ideProjects, setIdeProjects] = useState<ProjectInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [ideLoading, setIdeLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ideError, setIdeError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const noCodeApi = new NoCodeApiClient();
  const router = useRouter();

  useEffect(() => {
    fetchWorkflows();
    fetchIdeProjects();
  }, []);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      const workflowData = await noCodeApi.getWorkflows();
      setWorkflows(workflowData);
      setError(null);
    } catch (err) {
      setError("Failed to load workflows. Please try again.");
      console.error("Error fetching workflows:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchIdeProjects = async () => {
    try {
      setIdeLoading(true);
      const projectsData = await fileManagementApi.listProjects();
      setIdeProjects(projectsData);
      setIdeError(null);
    } catch (err) {
      setIdeError("Failed to load IDE projects. Please try again.");
      console.error("Error fetching IDE projects:", err);
    } finally {
      setIdeLoading(false);
    }
  };

  const handleCreateNew = () => {
    setIsModalOpen(true);
  };

  const handleNoCodeSelection = () => {
    setIsModalOpen(false);
    router.push("/strategy-hub/no-code-console");
  };

  const handleIdeSelection = () => {
    setIsModalOpen(false);
    router.push("/strategy-hub/ide");
  };

  const handleWorkflowClick = (workflow: Workflow) => {
    window.open(
      `/strategy-hub/no-code-console?workflow=${workflow.uuid}`,
      "_blank",
    );
  };

  const handleIdeProjectClick = (project: ProjectInfo) => {
    router.push(`/strategy-hub/ide?project=${project.id}`);
  };

  const handleRefreshWorkflows = () => {
    fetchWorkflows();
  };

  const handleRefreshIdeProjects = () => {
    fetchIdeProjects();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "compiled":
        return "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300";
      case "compiling":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300";
      case "failed":
        return "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300";
    }
  };

  const getLanguageIcon = (language: string) => {
    return <FileCode className="h-4 w-4" />;
  };

  const getFileCountText = (fileCount: number) => {
    return `${fileCount} file${fileCount !== 1 ? 's' : ''}`;
  };

  if (loading && ideLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex justify-between items-center mb-8">
          <div>
            <div className="h-8 w-64 bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
            <div className="h-4 w-96 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          </div>
          <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        </div>

        {/* No Code Workflows Skeleton */}
        <div className="mb-12">
          <div className="h-6 w-48 bg-gray-200 dark:bg-gray-700 rounded mb-4 animate-pulse" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="h-6 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
                  <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardHeader>
                <CardContent>
                  <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
                  <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardContent>
                <CardFooter>
                  <div className="h-8 w-full bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardFooter>
              </Card>
            ))}
          </div>
        </div>

        {/* IDE Files Skeleton */}
        <div>
          <div className="h-6 w-48 bg-gray-200 dark:bg-gray-700 rounded mb-4 animate-pulse" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[4, 5, 6].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="h-6 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
                  <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardHeader>
                <CardContent>
                  <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
                  <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardContent>
                <CardFooter>
                  <div className="h-8 w-full bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardFooter>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error && ideError) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <div className="text-red-500 mb-4">⚠️</div>
          <h3 className="text-lg font-semibold mb-2">
            Failed to Load Data
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Unable to load both workflows and IDE projects. Please try again.
          </p>
          <div className="flex gap-4 justify-center">
            <Button onClick={handleRefreshWorkflows} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh Workflows
            </Button>
            <Button onClick={handleRefreshIdeProjects} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh IDE Projects
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Strategy Hub
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage your no-code workflows and IDE-based trading strategies
          </p>
        </div>
        <Button onClick={handleCreateNew} size="lg">
          <Plus className="mr-2 h-4 w-4" />
          Create New Model
        </Button>
      </div>

      {/* No Code Workflows Section */}
      <div className="mb-12">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
            No Code Workflows
          </h2>
          {error && (
            <Button onClick={handleRefreshWorkflows} variant="outline" size="sm">
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="h-6 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
                  <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardHeader>
                <CardContent>
                  <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
                  <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardContent>
                <CardFooter>
                  <div className="h-8 w-full bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardFooter>
              </Card>
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-8 border border-red-200 dark:border-red-800 rounded-lg bg-red-50 dark:bg-red-950/20">
            <div className="text-red-500 mb-2">⚠️</div>
            <h3 className="text-lg font-semibold mb-2">Failed to Load Workflows</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
            <Button onClick={handleRefreshWorkflows} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          </div>
        ) : workflows.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
            <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No workflows yet</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Get started by creating your first trading strategy workflow
            </p>
            <Button onClick={handleCreateNew}>
              <Plus className="mr-2 h-4 w-4" />
              Create Your First Model
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {workflows.map((workflow) => (
              <Card
                key={workflow.uuid}
                className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
                onClick={() => handleWorkflowClick(workflow)}
              >
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-lg font-semibold truncate">
                        {workflow.name}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        {workflow.description || "No description provided"}
                      </CardDescription>
                    </div>
                    <Badge
                      className={`ml-2 ${getStatusColor(workflow.compilation_status)}`}
                      variant="secondary"
                    >
                      {workflow.compilation_status}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="space-y-3">
                    {/* Category */}
                    <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                      <Tag className="mr-2 h-3 w-3" />
                      <span className="capitalize">{workflow.category}</span>
                    </div>

                    {/* Tags */}
                    {workflow.tags && workflow.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {workflow.tags.slice(0, 3).map((tag, index) => (
                          <Badge
                            key={index}
                            variant="outline"
                            className="text-xs"
                          >
                            {tag}
                          </Badge>
                        ))}
                        {workflow.tags.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{workflow.tags.length - 3} more
                          </Badge>
                        )}
                      </div>
                    )}

                    {/* Updated Date */}
                    <div className="flex items-center text-xs text-gray-500 dark:text-gray-500">
                      <Calendar className="mr-1 h-3 w-3" />
                      Updated {formatDate(workflow.updated_at)}
                    </div>

                    {/* Execution Mode */}
                    <div className="flex items-center text-xs">
                      <User className="mr-1 h-3 w-3" />
                      <span className="capitalize">
                        {workflow.execution_mode.replace("_", " ")}
                      </span>
                    </div>
                  </div>
                </CardContent>

                <CardFooter>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleWorkflowClick(workflow);
                    }}
                  >
                    Open Workflow
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* IDE Files Section */}
      <div>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
            IDE Files
          </h2>
          {ideError && (
            <Button onClick={handleRefreshIdeProjects} variant="outline" size="sm">
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          )}
        </div>

        {ideLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="h-6 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
                  <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardHeader>
                <CardContent>
                  <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
                  <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardContent>
                <CardFooter>
                  <div className="h-8 w-full bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </CardFooter>
              </Card>
            ))}
          </div>
        ) : ideError ? (
          <div className="text-center py-8 border border-red-200 dark:border-red-800 rounded-lg bg-red-50 dark:bg-red-950/20">
            <div className="text-red-500 mb-2">⚠️</div>
            <h3 className="text-lg font-semibold mb-2">Failed to Load IDE Projects</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">{ideError}</p>
            <Button onClick={handleRefreshIdeProjects} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          </div>
        ) : ideProjects.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
            <Folder className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No IDE projects yet</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Create your first code-based trading strategy in the IDE
            </p>
            <Button onClick={handleIdeSelection}>
              <Code2 className="mr-2 h-4 w-4" />
              Open IDE
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {ideProjects.map((project) => (
              <Card
                key={project.id}
                className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
                onClick={() => handleIdeProjectClick(project)}
              >
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-lg font-semibold truncate flex items-center">
                        <Folder className="mr-2 h-5 w-5 text-blue-500" />
                        {project.name}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        {project.description || "No description provided"}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="space-y-3">
                    {/* File Count */}
                    <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                      <FileCode className="mr-2 h-3 w-3" />
                      <span>{getFileCountText(project.files?.length || 0)}</span>
                    </div>

                    {/* Project Path */}
                    <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                      <FileText className="mr-2 h-3 w-3" />
                      <span className="truncate">{project.path}</span>
                    </div>

                    {/* Updated Date */}
                    <div className="flex items-center text-xs text-gray-500 dark:text-gray-500">
                      <Calendar className="mr-1 h-3 w-3" />
                      Updated {formatDate(project.updated_at)}
                    </div>

                    {/* Settings Preview */}
                    {project.settings && Object.keys(project.settings).length > 0 && (
                      <div className="flex items-center text-xs">
                        <Tag className="mr-1 h-3 w-3" />
                        <span className="capitalize">
                          {Object.keys(project.settings).length} setting{Object.keys(project.settings).length !== 1 ? 's' : ''}
                        </span>
                      </div>
                    )}
                  </div>
                </CardContent>

                <CardFooter>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleIdeProjectClick(project);
                    }}
                  >
                    Open Project
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Model Type Selection Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Choose Model Type</DialogTitle>
            <DialogDescription>
              Select how you'd like to create your trading strategy
            </DialogDescription>
          </DialogHeader>

          <div className="flex gap-4 mt-6">
            {/* No Code Option */}
            <div
              onClick={handleNoCodeSelection}
              className="flex-1 p-6 border-2 border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-all duration-200 group"
            >
              <div className="text-center">
                <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200">
                  <WorkflowIcon className="h-8 w-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                  No Code
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Visual workflow builder with drag-and-drop interface
                </p>
              </div>
            </div>

            {/* IDE Option */}
            <div
              onClick={handleIdeSelection}
              className="flex-1 p-6 border-2 border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-950/30 transition-all duration-200 group"
            >
              <div className="text-center">
                <div className="mx-auto w-16 h-16 bg-gradient-to-br from-green-500 to-teal-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200">
                  <Code2 className="h-8 w-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                  IDE
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Code-based development environment for advanced strategies
                </p>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
