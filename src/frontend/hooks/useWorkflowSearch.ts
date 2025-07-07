import { useState, useCallback, useEffect, useMemo } from 'react';
import { noCodeApiClient, Workflow, WorkflowNode } from '@/lib/api/no-code-api';
import { useDebounce } from './useDebounce';

export interface SearchFilters {
  category?: string;
  tags?: string[];
  isPublic?: boolean;
}

export interface SearchState {
  query: string;
  results: Workflow[];
  nodeResults: {
    nodes: WorkflowNode[];
    matches: Array<{
      nodeId: string;
      field: string;
      value: string;
    }>;
  } | null;
  loading: boolean;
  error: string | null;
  total: number;
  hasMore: boolean;
}

export interface SearchActions {
  setQuery: (query: string) => void;
  setFilters: (filters: SearchFilters) => void;
  searchWorkflows: () => Promise<void>;
  searchNodes: (workflowId: string) => Promise<void>;
  loadMore: () => Promise<void>;
  clearResults: () => void;
  clearError: () => void;
}

export function useWorkflowSearch(
  initialQuery: string = '',
  initialFilters: SearchFilters = {}
): [SearchState, SearchActions] {
  const [query, setQuery] = useState(initialQuery);
  const [filters, setFilters] = useState<SearchFilters>(initialFilters);
  const [results, setResults] = useState<Workflow[]>([]);
  const [nodeResults, setNodeResults] = useState<SearchState['nodeResults']>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);

  const debouncedQuery = useDebounce(query, 300);

  const searchWorkflows = useCallback(async (isLoadMore = false) => {
    if (!debouncedQuery.trim() && Object.keys(filters).length === 0) {
      setResults([]);
      setTotal(0);
      setHasMore(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const currentOffset = isLoadMore ? offset : 0;
      const response = await noCodeApiClient.searchWorkflows(debouncedQuery, {
        ...filters,
        limit: 20,
        offset: currentOffset,
      });

      if (isLoadMore) {
        setResults(prev => [...prev, ...response.workflows]);
      } else {
        setResults(response.workflows);
        setOffset(0);
      }

      setTotal(response.total);
      setHasMore(response.hasMore);
      setOffset(currentOffset + response.workflows.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      if (!isLoadMore) {
        setResults([]);
        setTotal(0);
        setHasMore(false);
      }
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, filters, offset]);

  const searchNodes = useCallback(async (workflowId: string) => {
    if (!debouncedQuery.trim()) {
      setNodeResults(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await noCodeApiClient.searchNodes(workflowId, debouncedQuery);
      setNodeResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Node search failed');
      setNodeResults(null);
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery]);

  const loadMore = useCallback(async () => {
    if (!hasMore || loading) return;
    await searchWorkflows(true);
  }, [hasMore, loading, searchWorkflows]);

  const clearResults = useCallback(() => {
    setResults([]);
    setNodeResults(null);
    setTotal(0);
    setHasMore(false);
    setOffset(0);
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Auto-search when query or filters change
  useEffect(() => {
    if (debouncedQuery || Object.keys(filters).length > 0) {
      searchWorkflows();
    } else {
      clearResults();
    }
  }, [debouncedQuery, filters, searchWorkflows, clearResults]);

  const state: SearchState = {
    query,
    results,
    nodeResults,
    loading,
    error,
    total,
    hasMore,
  };

  const actions: SearchActions = {
    setQuery,
    setFilters,
    searchWorkflows: () => searchWorkflows(false),
    searchNodes,
    loadMore,
    clearResults,
    clearError,
  };

  return [state, actions];
}

// Hook for quick search suggestions
export function useSearchSuggestions(query: string) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  
  const debouncedQuery = useDebounce(query, 200);

  useEffect(() => {
    if (!debouncedQuery.trim() || debouncedQuery.length < 2) {
      setSuggestions([]);
      return;
    }

    setLoading(true);

    // Simulate suggestions - in real implementation, this would call an API
    const mockSuggestions = [
      'Moving Average Crossover',
      'RSI Strategy',
      'Bollinger Bands',
      'MACD Signal',
      'Mean Reversion',
      'Momentum Strategy',
      'Arbitrage',
      'Grid Trading'
    ].filter(s => s.toLowerCase().includes(debouncedQuery.toLowerCase()));

    setTimeout(() => {
      setSuggestions(mockSuggestions.slice(0, 5));
      setLoading(false);
    }, 100);
  }, [debouncedQuery]);

  return { suggestions, loading };
}

// Hook for search history
export function useSearchHistory() {
  const [history, setHistory] = useState<string[]>([]);

  useEffect(() => {
    const savedHistory = localStorage.getItem('workflow-search-history');
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch {
        setHistory([]);
      }
    }
  }, []);

  const addToHistory = useCallback((query: string) => {
    if (!query.trim()) return;

    setHistory(prev => {
      const filtered = prev.filter(item => item !== query);
      const newHistory = [query, ...filtered].slice(0, 10); // Keep last 10 searches
      localStorage.setItem('workflow-search-history', JSON.stringify(newHistory));
      return newHistory;
    });
  }, []);

  const clearHistory = useCallback(() => {
    setHistory([]);
    localStorage.removeItem('workflow-search-history');
  }, []);

  return {
    history,
    addToHistory,
    clearHistory,
  };
}