'use client';

import React, { useState, useMemo, useEffect } from 'react';
import { Search } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import HeaderSection from '@/components/marketplace/HeaderSection';
import FilterSection from '@/components/marketplace/FilterSection';
import StatsBar from '@/components/marketplace/StatsBar';
import StrategyGrid from '@/components/marketplace/StrategyGrid';
import StrategyModal from '@/components/marketplace/StrategyModal';
import FilterSidebar from '@/components/marketplace/FilterSidebar';
import { Strategy } from '@/components/marketplace/types';
// import mockStrategies from '@/components/marketplace/mockStrategies'; // Deleted (using live data)
import { useTheme } from '@/components/marketplace/useTheme';
import { fetchStrategies } from '@/app/api/strategyApi'; // New API import

export default function MarketplacePage() {
  const { theme } = useTheme();

  // 1. STATE FOR LIVE DATA AND LOADING
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Existing state...
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('popularity');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [filters, setFilters] = useState({
    assetType: 'all',
    riskLevel: 'all',
    rating: 0,
    verificationStatus: 'all',
  });

  // 2. FETCH DATA ONCE COMPONENT MOUNTS
  useEffect(() => {
    setIsLoading(true);
    fetchStrategies()
      .then(data => setStrategies(data))
      .catch(error => console.error("Failed to load strategies:", error))
      .finally(() => setIsLoading(false));
  }, []); // Empty dependency array means this runs only once on mount

  const filteredStrategies = useMemo(() => {
    // 3. CHANGE TO USE LIVE DATA: strategies
    const filtered = strategies
      .filter((strategy) => {
        const matchesSearch =
          strategy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          strategy.creatorName.toLowerCase().includes(searchQuery.toLowerCase()) ||
          strategy.description.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesCategory = selectedCategory === 'all' || strategy.category.toLowerCase() === selectedCategory.toLowerCase();
        const matchesAssetType = filters.assetType === 'all' || strategy.assetType.toLowerCase() === filters.assetType.toLowerCase();
        const matchesRiskLevel = filters.riskLevel === 'all' || strategy.riskLevel === filters.riskLevel;
        const matchesRating = strategy.rating >= filters.rating;
        const matchesVerification = filters.verificationStatus === 'all' || strategy.verificationStatus === filters.verificationStatus;

        return matchesSearch && matchesCategory && matchesAssetType && matchesRiskLevel && matchesRating && matchesVerification;
      });

    // Create a copy of the array before sorting to avoid mutation
    const sortedStrategies = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'roi-desc':
          return b.performance.totalReturn - a.performance.totalReturn;
        case 'rating':
          return b.rating - a.rating;
        case 'price-asc': {
          const priceA = a.price === 'free' ? 0 : a.price;
          const priceB = b.price === 'free' ? 0 : b.price;
          return priceA - priceB;
        }
        case 'price-desc': {
          const priceA = a.price === 'free' ? 0 : a.price;
          const priceB = b.price === 'free' ? 0 : b.price;
          return priceB - priceA;
        }
        case 'popularity':
        default:
          return b.subscriberCount - a.subscriberCount;
      }
    });

    return sortedStrategies;
  }, [searchQuery, selectedCategory, filters, sortBy, strategies]); // Added 'strategies' dependency

  // 4. LOADING CHECK TO RENDER
  if (isLoading) {
    return (
      <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'} text-foreground flex justify-center items-center`}>
        <p className="text-xl text-gray-400">Loading Strategies...</p>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'} text-foreground`}>
      <HeaderSection />
      <div className="max-w-7xl mx-auto px-4 py-6">
        <FilterSection
          selectedCategory={selectedCategory}
          setSelectedCategory={setSelectedCategory}
          filters={filters}
          setFilters={setFilters}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          sortBy={sortBy}
          setSortBy={setSortBy}
          showFilters={showFilters}
          setShowFilters={setShowFilters}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
        <StatsBar filteredStrategies={filteredStrategies} />
        <div className="flex gap-6">
          {showFilters && (
            <div className="w-64 flex-shrink-0">
              <FilterSidebar filters={filters} onFiltersChange={setFilters} />
            </div>
          )}
          <div className="flex-1">
            <Tabs defaultValue="browse" className="w-full">
              <TabsList className="grid w-full grid-cols-3 mb-6">
                <TabsTrigger value="browse">Browse All</TabsTrigger>
                <TabsTrigger value="trending">Trending</TabsTrigger>
                <TabsTrigger value="new">New Releases</TabsTrigger>
              </TabsList>
              <TabsContent value="browse" className="space-y-0">
                {filteredStrategies.length === 0 ? (
                  <div className={`text-center py-12 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">No strategies found matching your criteria</p>
                    <p className="text-sm mt-2">Try adjusting your search or filters</p>
                  </div>
                ) : (
                  <StrategyGrid
                    filteredStrategies={filteredStrategies}
                    viewMode={viewMode}
                    onSelectStrategy={setSelectedStrategy}
                  />
                )}
              </TabsContent>
              <TabsContent value="trending" className="space-y-0">
                <StrategyGrid
                  filteredStrategies={[...filteredStrategies]
                    .sort((a, b) => b.performance.totalReturn - a.performance.totalReturn)
                    .slice(0, 6)}
                  viewMode={viewMode}
                  onSelectStrategy={setSelectedStrategy}
                />
              </TabsContent>
              <TabsContent value="new" className="space-y-0">
                <StrategyGrid
                  filteredStrategies={[...filteredStrategies]
                    .sort((a, b) => new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime())
                    .slice(0, 6)}
                  viewMode={viewMode}
                  onSelectStrategy={setSelectedStrategy}
                />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
      {selectedStrategy && (
        <StrategyModal
          strategy={selectedStrategy}
          onClose={() => setSelectedStrategy(null)}
        />
      )}
    </div>
  );
}