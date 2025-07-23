export interface Strategy {
  id: string;
  name: string;
  developer: string;
  description: string;
  longDescription?: string;
  roi: number;
  roiChange: number;
  tradingPairs: string[];
  rating: number;
  reviews: number;
  downloads: number;
  price: number | 'free';
  riskLevel: 'low' | 'medium' | 'high';
  category: string;
  assetType: string;
  version: string;
  lastUpdated: string;
  publishedDate?: string;
  lastRevision?: string;
  backtestResults: BacktestResults;
  isPro: boolean;
  isVerified: boolean;
  supportedExchanges?: string[];
  minCapital?: number;
  maxPositions?: number;
  features?: string[];
  requirements?: {
    capital: string;
    exchanges: string;
    api: string;
    experience: string;
  };
}

export interface BacktestResults {
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  avgTrade: number;
  profitFactor: number;
  totalTrades: number;
  avgHoldingTime: string;
}

export interface Review {
  id: string;
  user: string;
  rating: number;
  date: string;
  title: string;
  content: string;
  helpful: number;
  unhelpful: number;
  verified: boolean;
  tradingExperience: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
  pros: string[];
  cons: string[];
}

export interface MarketplaceFilters {
  assetType: string;
  riskLevel: string;
  priceRange: string;
  rating: number;
}

export interface PerformanceDataPoint {
  date: string;
  value: number;
  benchmark?: number;
}

export interface DrawdownDataPoint {
  date: string;
  drawdown: number;
}

export interface MonthlyReturn {
  month: string;
  return: number;
  benchmark: number;
}

export interface RatingDistribution {
  stars: number;
  count: number;
  percentage: number;
}

export interface RiskMetric {
  metric: string;
  value: string;
  status: 'good' | 'warning' | 'bad' | 'neutral';
}

export interface TradeDistribution {
  name: string;
  value: number;
  color: string;
}

export interface TimeFramePerformance {
  period: string;
  return: number;
  trades: number;
  winRate: number;
}

export type ViewMode = 'grid' | 'list';
export type SortOption = 'popularity' | 'roi-desc' | 'roi-asc' | 'rating' | 'price-asc' | 'price-desc';
export type FilterOption = 'all' | 'verified' | 'rating-5' | 'rating-4' | 'rating-3';
export type SortBy = 'helpful' | 'recent' | 'rating';

// API Response Types
export interface StrategyResponse {
  strategies: Strategy[];
  total: number;
  page: number;
  limit: number;
}

export interface ReviewResponse {
  reviews: Review[];
  total: number;
  averageRating: number;
  ratingDistribution: RatingDistribution[];
}

// Component Props Types
export interface StrategyCardProps {
  strategy: Strategy;
  viewMode: ViewMode;
  onPlugIn?: (strategyId: string) => void;
  onViewDetails?: (strategyId: string) => void;
}

export interface FilterSidebarProps {
  filters: MarketplaceFilters;
  onFiltersChange: (filters: MarketplaceFilters) => void;
}

export interface PerformanceChartProps {
  data?: PerformanceDataPoint[];
  drawdownData?: DrawdownDataPoint[];
}

export interface BacktestResultsProps {
  results: BacktestResults;
  monthlyReturns?: MonthlyReturn[];
  riskMetrics?: RiskMetric[];
}

export interface ReviewSectionProps {
  strategyId: string;
  rating: number;
  reviewCount: number;
  reviews?: Review[];
}

// Search and Filter Types
export interface SearchParams {
  query?: string;
  category?: string;
  assetType?: string;
  riskLevel?: string;
  priceRange?: string;
  rating?: number;
  sortBy?: SortOption;
  page?: number;
  limit?: number;
}

// Developer Types
export interface Developer {
  id: string;
  name: string;
  username: string;
  avatar?: string;
  verified: boolean;
  totalStrategies: number;
  totalDownloads: number;
  averageRating: number;
  joinDate: string;
  bio?: string;
  website?: string;
  socialLinks?: {
    twitter?: string;
    telegram?: string;
    discord?: string;
  };
}

// Marketplace Statistics
export interface MarketplaceStats {
  totalStrategies: number;
  totalDevelopers: number;
  totalDownloads: number;
  averageROI: number;
  averageRating: number;
  topCategories: Array<{
    name: string;
    count: number;
  }>;
}

// Error Types
export interface MarketplaceError {
  code: string;
  message: string;
  details?: any;
}

// Hook Types
export interface UseMarketplaceReturn {
  strategies: Strategy[];
  loading: boolean;
  error: MarketplaceError | null;
  totalCount: number;
  hasNextPage: boolean;
  loadMore: () => void;
  refetch: () => void;
}

export interface UseStrategyDetailReturn {
  strategy: Strategy | null;
  reviews: Review[];
  loading: boolean;
  error: MarketplaceError | null;
  refetch: () => void;
}

// Configuration Types
export interface MarketplaceConfig {
  itemsPerPage: number;
  maxFilters: number;
  enableReviews: boolean;
  enableRatings: boolean;
  currencies: string[];
  supportedExchanges: string[];
  riskLevels: Array<{
    level: 'low' | 'medium' | 'high';
    label: string;
    color: string;
  }>;
}