/**
 * File Management API Client
 * 
 * Handles all file and project operations for the IDE interface,
 * communicating with the ai-ml-strategy-service backend.
 */

import { BaseApiClient } from './api-client';

// Types matching the backend models
export interface FileInfo {
  id: string;
  name: string;
  path: string;
  content?: string;
  language: string;
  size: number;
  modified: boolean;
  created_at: string;
  updated_at: string;
  is_directory: boolean;
}

export interface ProjectInfo {
  id: string;
  name: string;
  description?: string;
  path: string;
  files: FileInfo[];
  created_at: string;
  updated_at: string;
  settings: {
    aiEnabled?: boolean;
    suggestions?: boolean;
    autoComplete?: boolean;
    errorDetection?: boolean;
    testGeneration?: boolean;
    [key: string]: any;
  };
}

export interface CreateFileRequest {
  name: string;
  content?: string;
  language?: string;
  project_id?: string;
}

export interface UpdateFileRequest {
  content: string;
  language?: string;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  template?: 'basic' | 'trading' | 'ml' | 'research';
}

export interface FileListOptions {
  include_content?: boolean;
}

export interface ApiError extends Error {
  status?: number;
  statusText?: string;
  response?: any;
}

export class FileManagementApi extends BaseApiClient {
  constructor() {
    // Configure for ai-ml-strategy-service
    super({
      baseUrl: process.env.NEXT_PUBLIC_AI_ML_SERVICE_URL || 'http://localhost:8001',
      timeout: 60000, // File operations may take longer
    });
  }

  // Project Management
  async createProject(request: CreateProjectRequest): Promise<ProjectInfo> {
    return this.post<ProjectInfo>('/api/files/projects', request);
  }

  async listProjects(): Promise<ProjectInfo[]> {
    return this.get<ProjectInfo[]>('/api/files/projects');
  }

  async getProject(projectId: string): Promise<ProjectInfo> {
    return this.get<ProjectInfo>(`/api/files/projects/${projectId}`);
  }

  async deleteProject(projectId: string): Promise<{ message: string }> {
    return this.delete<{ message: string }>(`/api/files/projects/${projectId}`);
  }

  // File Management
  async createFile(projectId: string, request: CreateFileRequest): Promise<FileInfo> {
    return this.post<FileInfo>(`/api/files/projects/${projectId}/files`, request);
  }

  async getFile(projectId: string, filename: string): Promise<FileInfo> {
    // URL encode the filename to handle paths with special characters
    const encodedFilename = encodeURIComponent(filename);
    return this.get<FileInfo>(`/api/files/projects/${projectId}/files/${encodedFilename}`);
  }

  async updateFile(projectId: string, filename: string, request: UpdateFileRequest): Promise<FileInfo> {
    const encodedFilename = encodeURIComponent(filename);
    return this.put<FileInfo>(`/api/files/projects/${projectId}/files/${encodedFilename}`, request);
  }

  async deleteFile(projectId: string, filename: string): Promise<{ message: string }> {
    const encodedFilename = encodeURIComponent(filename);
    return this.delete<{ message: string }>(`/api/files/projects/${projectId}/files/${encodedFilename}`);
  }

  async listProjectFiles(projectId: string, options: FileListOptions = {}): Promise<FileInfo[]> {
    const queryParams = this.buildQueryString(options);
    const endpoint = `/api/files/projects/${projectId}/files${queryParams ? `?${queryParams}` : ''}`;
    return this.get<FileInfo[]>(endpoint);
  }

  // Convenience methods for IDE integration
  async saveFile(projectId: string, filename: string, content: string, language?: string): Promise<FileInfo> {
    try {
      // Try to update existing file first
      return await this.updateFile(projectId, filename, { content, language });
    } catch (error) {
      // If file doesn't exist, create it
      if ((error as ApiError).status === 404) {
        return await this.createFile(projectId, {
          name: filename,
          content,
          language: language || this.detectLanguageFromFilename(filename)
        });
      }
      throw error;
    }
  }

  async loadFile(projectId: string, filename: string): Promise<FileInfo> {
    return this.getFile(projectId, filename);
  }

  async loadProject(projectId: string, includeFileContents: boolean = false): Promise<ProjectInfo> {
    const project = await this.getProject(projectId);
    
    if (includeFileContents && project.files.length > 0) {
      // Load content for each file
      const filesWithContent = await Promise.all(
        project.files.map(async (file) => {
          if (!file.is_directory) {
            try {
              const fileWithContent = await this.getFile(projectId, file.name);
              return fileWithContent;
            } catch (error) {
              console.warn(`Failed to load content for file ${file.name}:`, error);
              return file;
            }
          }
          return file;
        })
      );
      project.files = filesWithContent;
    }
    
    return project;
  }

  async createProjectFromTemplate(name: string, template: 'basic' | 'trading' | 'ml' | 'research', description?: string): Promise<ProjectInfo> {
    return this.createProject({
      name,
      description,
      template
    });
  }

  // Utility methods
  private detectLanguageFromFilename(filename: string): string {
    const ext = filename.split('.').pop()?.toLowerCase();
    const languageMap: Record<string, string> = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'jsx': 'javascript',
      'html': 'html',
      'css': 'css',
      'json': 'json',
      'md': 'markdown',
      'sql': 'sql',
      'yaml': 'yaml',
      'yml': 'yaml',
      'txt': 'plaintext'
    };
    return languageMap[ext || ''] || 'plaintext';
  }

  // Batch operations
  async saveMultipleFiles(projectId: string, files: Array<{ filename: string; content: string; language?: string }>): Promise<FileInfo[]> {
    const results = await Promise.allSettled(
      files.map(file => this.saveFile(projectId, file.filename, file.content, file.language))
    );

    const savedFiles: FileInfo[] = [];
    const errors: Error[] = [];

    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        savedFiles.push(result.value);
      } else {
        errors.push(new Error(`Failed to save ${files[index].filename}: ${result.reason}`));
      }
    });

    if (errors.length > 0 && savedFiles.length === 0) {
      throw new Error(`Failed to save any files: ${errors.map(e => e.message).join(', ')}`);
    }

    if (errors.length > 0) {
      console.warn('Some files failed to save:', errors);
    }

    return savedFiles;
  }

  // Health check for file management service
  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.get<{ status: string; service: string }>('/health');
  }

  // Get service status
  async getServiceStatus(): Promise<{ status: string; version: string; phase: string }> {
    return this.get('/api/status');
  }
}

// Singleton instance
export const fileManagementApi = new FileManagementApi();
export default fileManagementApi;