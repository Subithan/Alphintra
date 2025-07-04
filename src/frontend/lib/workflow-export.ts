import { Node, Edge } from 'reactflow';
import { NoCodeWorkflow } from '@/lib/stores/no-code-store';

export interface ExportedWorkflow {
  version: string;
  metadata: {
    name: string;
    description?: string;
    author?: string;
    created: string;
    modified: string;
    exportedAt: string;
    tags?: string[];
  };
  workflow: {
    nodes: Node[];
    edges: Edge[];
    parameters: Record<string, any>;
  };
  validation?: {
    isValid: boolean;
    errors: number;
    warnings: number;
  };
}

export class WorkflowExporter {
  /**
   * Export workflow to JSON format
   */
  static exportWorkflow(workflow: NoCodeWorkflow, options?: {
    includeValidation?: boolean;
    author?: string;
    tags?: string[];
  }): ExportedWorkflow {
    const exported: ExportedWorkflow = {
      version: '1.0.0',
      metadata: {
        name: workflow.name,
        description: workflow.description,
        author: options?.author || 'Anonymous',
        created: workflow.createdAt instanceof Date ? workflow.createdAt.toISOString() : workflow.createdAt,
        modified: workflow.lastModified ? 
          (workflow.lastModified instanceof Date ? workflow.lastModified.toISOString() : workflow.lastModified) 
          : new Date().toISOString(),
        exportedAt: new Date().toISOString(),
        tags: options?.tags || []
      },
      workflow: {
        nodes: this.sanitizeNodes(workflow.nodes),
        edges: this.sanitizeEdges(workflow.edges),
        parameters: workflow.parameters || {}
      }
    };

    return exported;
  }

  /**
   * Import workflow from JSON format
   */
  static importWorkflow(exportedData: string | ExportedWorkflow): NoCodeWorkflow {
    let data: ExportedWorkflow;
    
    if (typeof exportedData === 'string') {
      try {
        data = JSON.parse(exportedData);
      } catch (error) {
        throw new Error('Invalid JSON format');
      }
    } else {
      data = exportedData;
    }

    this.validateExportedWorkflow(data);

    const workflow: NoCodeWorkflow = {
      id: `imported-${Date.now()}`,
      name: data.metadata.name,
      description: data.metadata.description || '',
      nodes: data.workflow.nodes,
      edges: data.workflow.edges,
      parameters: data.workflow.parameters || {},
      createdAt: new Date(data.metadata.created),
      lastModified: new Date(data.metadata.modified)
    };

    return workflow;
  }

  /**
   * Export workflow as downloadable file
   */
  static downloadWorkflow(workflow: NoCodeWorkflow, options?: {
    author?: string;
    tags?: string[];
  }): void {
    const exported = this.exportWorkflow(workflow, options);
    const blob = new Blob([JSON.stringify(exported, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${workflow.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_workflow.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * Export workflow to clipboard
   */
  static async copyWorkflowToClipboard(workflow: NoCodeWorkflow): Promise<void> {
    const exported = this.exportWorkflow(workflow);
    const jsonString = JSON.stringify(exported, null, 2);
    
    try {
      await navigator.clipboard.writeText(jsonString);
    } catch (error) {
      throw new Error('Failed to copy to clipboard');
    }
  }

  /**
   * Import workflow from file
   */
  static importWorkflowFromFile(file: File): Promise<NoCodeWorkflow> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (event) => {
        try {
          const content = event.target?.result as string;
          const workflow = this.importWorkflow(content);
          resolve(workflow);
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };
      
      reader.readAsText(file);
    });
  }

  /**
   * Convert workflow to shareable URL
   */
  static workflowToShareableUrl(workflow: NoCodeWorkflow, baseUrl?: string): string {
    const exported = this.exportWorkflow(workflow);
    const compressed = this.compressWorkflow(exported);
    const encoded = btoa(compressed);
    
    const base = baseUrl || window.location.origin + window.location.pathname;
    return `${base}?workflow=${encoded}`;
  }

  /**
   * Import workflow from shareable URL
   */
  static importWorkflowFromUrl(url: string): NoCodeWorkflow | null {
    try {
      const urlObj = new URL(url);
      const workflowParam = urlObj.searchParams.get('workflow');
      
      if (!workflowParam) return null;
      
      const compressed = atob(workflowParam);
      const exported = this.decompressWorkflow(compressed);
      
      return this.importWorkflow(exported);
    } catch (error) {
      console.error('Failed to import workflow from URL:', error);
      return null;
    }
  }

  // Helper methods
  private static sanitizeNodes(nodes: Node[]): Node[] {
    return nodes.map(node => ({
      ...node,
      // Remove any runtime-specific properties
      selected: false,
      dragging: false,
      // Ensure position is clean
      position: {
        x: Math.round(node.position.x),
        y: Math.round(node.position.y)
      }
    }));
  }

  private static sanitizeEdges(edges: Edge[]): Edge[] {
    return edges.map(edge => ({
      ...edge,
      // Remove any runtime-specific properties
      selected: false
    }));
  }

  private static validateExportedWorkflow(data: ExportedWorkflow): void {
    if (!data.version) {
      throw new Error('Missing version information');
    }

    if (!data.metadata) {
      throw new Error('Missing metadata');
    }

    if (!data.metadata.name) {
      throw new Error('Missing workflow name');
    }

    if (!data.workflow) {
      throw new Error('Missing workflow data');
    }

    if (!Array.isArray(data.workflow.nodes)) {
      throw new Error('Invalid nodes format');
    }

    if (!Array.isArray(data.workflow.edges)) {
      throw new Error('Invalid edges format');
    }

    // Validate version compatibility
    const supportedVersions = ['1.0.0'];
    if (!supportedVersions.includes(data.version)) {
      console.warn(`Workflow version ${data.version} may not be fully compatible`);
    }
  }

  private static compressWorkflow(exported: ExportedWorkflow): string {
    // Simple compression by removing whitespace and shortening property names
    const compressed = {
      v: exported.version,
      m: {
        n: exported.metadata.name,
        d: exported.metadata.description,
        a: exported.metadata.author,
        c: exported.metadata.created,
        t: exported.metadata.tags
      },
      w: {
        n: exported.workflow.nodes,
        e: exported.workflow.edges,
        p: exported.workflow.parameters
      }
    };

    return JSON.stringify(compressed);
  }

  private static decompressWorkflow(compressed: string): ExportedWorkflow {
    const data = JSON.parse(compressed);
    
    return {
      version: data.v,
      metadata: {
        name: data.m.n,
        description: data.m.d,
        author: data.m.a,
        created: data.m.c,
        modified: data.m.c, // Use created as modified for compressed format
        exportedAt: new Date().toISOString(),
        tags: data.m.t || []
      },
      workflow: {
        nodes: data.w.n,
        edges: data.w.e,
        parameters: data.w.p || {}
      }
    };
  }
}

// Utility functions for workflow management
export const WorkflowUtils = {
  /**
   * Generate workflow statistics
   */
  getWorkflowStats(workflow: NoCodeWorkflow) {
    const nodeTypes = workflow.nodes.reduce((acc, node) => {
      if (node.type) {
        acc[node.type] = (acc[node.type] || 0) + 1;
      }
      return acc;
    }, {} as Record<string, number>);

    return {
      totalNodes: workflow.nodes.length,
      totalEdges: workflow.edges.length,
      nodeTypes,
      hasDataSource: workflow.nodes.some(n => n.type === 'dataSource' || n.type === 'customDataset'),
      hasOutput: workflow.nodes.some(n => n.type === 'output' || n.type === 'action'),
      hasRiskManagement: workflow.nodes.some(n => n.type === 'risk'),
      complexity: workflow.nodes.length + workflow.edges.length
    };
  },

  /**
   * Create workflow thumbnail/preview
   */
  generateWorkflowPreview(workflow: NoCodeWorkflow): string {
    const stats = this.getWorkflowStats(workflow);
    
    // Generate a simple text-based preview
    const preview = [
      `📊 ${workflow.name}`,
      `🔢 ${stats.totalNodes} nodes, ${stats.totalEdges} connections`,
      `📈 ${Object.keys(stats.nodeTypes).join(', ')}`,
      stats.hasDataSource ? '✅ Data source' : '❌ No data source',
      stats.hasOutput ? '✅ Output/Actions' : '❌ No output',
      stats.hasRiskManagement ? '✅ Risk management' : '⚠️ No risk management'
    ].join('\n');

    return preview;
  },

  /**
   * Compare two workflows
   */
  compareWorkflows(workflow1: NoCodeWorkflow, workflow2: NoCodeWorkflow) {
    const stats1 = this.getWorkflowStats(workflow1);
    const stats2 = this.getWorkflowStats(workflow2);

    return {
      nodeCountDiff: stats2.totalNodes - stats1.totalNodes,
      edgeCountDiff: stats2.totalEdges - stats1.totalEdges,
      complexityDiff: stats2.complexity - stats1.complexity,
      addedNodeTypes: Object.keys(stats2.nodeTypes).filter(type => !stats1.nodeTypes[type]),
      removedNodeTypes: Object.keys(stats1.nodeTypes).filter(type => !stats2.nodeTypes[type])
    };
  }
};