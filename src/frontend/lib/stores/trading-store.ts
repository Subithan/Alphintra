import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

interface Portfolio {
  totalValue: number;
  cashBalance: number;
  positions: Position[];
  dailyPnL: number;
  totalPnL: number;
}

interface Position {
  id: string;
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  unrealizedPnL: number;
  realizedPnL: number;
  side: 'LONG' | 'SHORT';
}

interface Strategy {
  id: string;
  name: string;
  description: string;
  status: 'ACTIVE' | 'PAUSED' | 'STOPPED';
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  totalTrades: number;
  createdAt: string;
  updatedAt: string;
}

interface MarketData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  timestamp: string;
}

interface TradingState {
  // Portfolio data
  portfolio: Portfolio | null;
  
  // Active strategies
  strategies: Strategy[];
  activeStrategy: Strategy | null;
  
  // Market data
  marketData: Record<string, MarketData>;
  watchlist: string[];
  
  // UI state
  selectedTimeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d';
  selectedSymbol: string | null;
  
  // Loading states
  isLoadingPortfolio: boolean;
  isLoadingStrategies: boolean;
  isLoadingMarketData: boolean;
}

interface TradingActions {
  // Portfolio actions
  setPortfolio: (portfolio: Portfolio) => void;
  updatePortfolio: (updates: Partial<Portfolio>) => void;
  
  // Strategy actions
  setStrategies: (strategies: Strategy[]) => void;
  addStrategy: (strategy: Strategy) => void;
  updateStrategy: (id: string, updates: Partial<Strategy>) => void;
  removeStrategy: (id: string) => void;
  setActiveStrategy: (strategy: Strategy | null) => void;
  
  // Market data actions
  setMarketData: (symbol: string, data: MarketData) => void;
  updateMarketData: (updates: Record<string, MarketData>) => void;
  addToWatchlist: (symbol: string) => void;
  removeFromWatchlist: (symbol: string) => void;
  
  // UI actions
  setSelectedTimeframe: (timeframe: TradingState['selectedTimeframe']) => void;
  setSelectedSymbol: (symbol: string | null) => void;
  
  // Loading actions
  setLoadingPortfolio: (loading: boolean) => void;
  setLoadingStrategies: (loading: boolean) => void;
  setLoadingMarketData: (loading: boolean) => void;
  
  // Reset actions
  resetTradingState: () => void;
}

type TradingStore = TradingState & TradingActions;

const initialState: TradingState = {
  portfolio: null,
  strategies: [],
  activeStrategy: null,
  marketData: {},
  watchlist: ['BTCUSD', 'ETHUSD', 'AAPL', 'TSLA', 'GOOGL'],
  selectedTimeframe: '1h',
  selectedSymbol: null,
  isLoadingPortfolio: false,
  isLoadingStrategies: false,
  isLoadingMarketData: false,
};

export const useTradingStore = create<TradingStore>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,

    // Portfolio actions
    setPortfolio: (portfolio: Portfolio) => {
      set({ portfolio });
    },

    updatePortfolio: (updates: Partial<Portfolio>) => {
      const currentPortfolio = get().portfolio;
      if (currentPortfolio) {
        set({
          portfolio: { ...currentPortfolio, ...updates },
        });
      }
    },

    // Strategy actions
    setStrategies: (strategies: Strategy[]) => {
      set({ strategies });
    },

    addStrategy: (strategy: Strategy) => {
      set((state) => ({
        strategies: [...state.strategies, strategy],
      }));
    },

    updateStrategy: (id: string, updates: Partial<Strategy>) => {
      set((state) => ({
        strategies: state.strategies.map((strategy) =>
          strategy.id === id ? { ...strategy, ...updates } : strategy
        ),
      }));
    },

    removeStrategy: (id: string) => {
      set((state) => ({
        strategies: state.strategies.filter((strategy) => strategy.id !== id),
        activeStrategy: state.activeStrategy?.id === id ? null : state.activeStrategy,
      }));
    },

    setActiveStrategy: (strategy: Strategy | null) => {
      set({ activeStrategy: strategy });
    },

    // Market data actions
    setMarketData: (symbol: string, data: MarketData) => {
      set((state) => ({
        marketData: { ...state.marketData, [symbol]: data },
      }));
    },

    updateMarketData: (updates: Record<string, MarketData>) => {
      set((state) => ({
        marketData: { ...state.marketData, ...updates },
      }));
    },

    addToWatchlist: (symbol: string) => {
      set((state) => ({
        watchlist: state.watchlist.includes(symbol)
          ? state.watchlist
          : [...state.watchlist, symbol],
      }));
    },

    removeFromWatchlist: (symbol: string) => {
      set((state) => ({
        watchlist: state.watchlist.filter((s) => s !== symbol),
      }));
    },

    // UI actions
    setSelectedTimeframe: (timeframe: TradingState['selectedTimeframe']) => {
      set({ selectedTimeframe: timeframe });
    },

    setSelectedSymbol: (symbol: string | null) => {
      set({ selectedSymbol: symbol });
    },

    // Loading actions
    setLoadingPortfolio: (loading: boolean) => {
      set({ isLoadingPortfolio: loading });
    },

    setLoadingStrategies: (loading: boolean) => {
      set({ isLoadingStrategies: loading });
    },

    setLoadingMarketData: (loading: boolean) => {
      set({ isLoadingMarketData: loading });
    },

    // Reset actions
    resetTradingState: () => {
      set(initialState);
    },
  }))
);

// Selectors for computed values
export const useTradingSelectors = () => {
  const store = useTradingStore();
  
  return {
    // Portfolio selectors
    totalPortfolioValue: store.portfolio?.totalValue || 0,
    portfolioChange: store.portfolio?.dailyPnL || 0,
    portfolioChangePercent: store.portfolio
      ? (store.portfolio.dailyPnL / (store.portfolio.totalValue - store.portfolio.dailyPnL)) * 100
      : 0,
    
    // Strategy selectors
    activeStrategiesCount: store.strategies.filter(s => s.status === 'ACTIVE').length,
    totalStrategiesReturn: store.strategies.reduce((sum, s) => sum + s.totalReturn, 0) / store.strategies.length || 0,
    
    // Market data selectors
    watchlistData: store.watchlist.map(symbol => store.marketData[symbol]).filter(Boolean),
    selectedSymbolData: store.selectedSymbol ? store.marketData[store.selectedSymbol] : null,
  };
};