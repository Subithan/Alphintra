'use client';

import React, { useState, useMemo } from 'react';
import HeaderSection from '@/components/marketplace/HeaderSection';
import FilterSection from '@/components/marketplace/FilterSection';
import StrategyGrid from '@/components/marketplace/StrategyGrid';
import StrategyModal from '@/components/marketplace/StrategyModal';
import { Strategy } from '@/components/marketplace/types';
import mockStrategies from '@/components/marketplace/mockStrategies';
import { useTheme } from '@/components/marketplace/useTheme';

export default function MarketplacePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('popularity');
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [filters, setFilters] = useState({
    assetType: 'all',
    riskLevel: 'all',
    priceRange: 'all',
    rating: 0,
    verificationStatus: 'all',
  });

  const filteredStrategies = useMemo(() => {
    return mockStrategies
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
      })
      .sort((a, b) => {
        switch (sortBy) {
          case 'roi-desc':
            return b.performance.totalReturn - a.performance.totalReturn;
          case 'rating':
            return b.rating - a.rating;
          case 'price-asc':
            const priceA = a.price === 'free' ? 0 : a.price;
            const priceB = b.price === 'free' ? 0 : b.price;
            return priceA - priceB;
          case 'popularity':
            return b.subscriberCount - a.subscriberCount;
          default:
            return 0;
        }
      });
  }, [searchQuery, selectedCategory, filters, sortBy]);

  return (
    <div className={`min-h-screen ${useTheme().theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <HeaderSection />
      <div className="max-w-7xl mx-auto px-4 py-6">
        <FilterSection 
          selectedCategory={selectedCategory} 
          setSelectedCategory={setSelectedCategory}
          filters={filters}
          setFilters={setFilters}
        />
        <StrategyGrid 
          filteredStrategies={filteredStrategies} 
          setSelectedStrategy={setSelectedStrategy} 
        />
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

//subithan code

// 'use client';

// import React, { useState, useMemo } from 'react';
// import { Search, Filter, TrendingUp, Star, Users, Download, ChevronDown, Grid, List } from 'lucide-react';
// import { Input } from '@/components/ui/input';
// import { Button } from '@/components/ui/button';
// import { Badge } from '@/components/ui/badge';
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
// import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
// import StrategyCard from '@/components/marketplace/StrategyCard';
// import FilterSidebar from '@/components/marketplace/FilterSidebar';
// import { useTheme } from 'next-themes';

// interface Strategy {
//   id: string;
//   name: string;
//   developer: string;
//   description: string;
//   roi: number;
//   roiChange: number;
//   tradingPairs: string[];
//   rating: number;
//   reviews: number;
//   downloads: number;
//   price: number | 'free';
//   riskLevel: 'low' | 'medium' | 'high';
//   category: string;
//   assetType: string;
//   version: string;
//   lastUpdated: string;
//   backtestResults: {
//     totalReturn: number;
//     sharpeRatio: number;
//     maxDrawdown: number;
//     winRate: number;
//   };
//   isPro: boolean;
//   isVerified: boolean;
// }

// const mockStrategies: Strategy[] = [
//   {
//     id: '1',
//     name: 'Quantum Momentum Pro',
//     developer: 'AlgoMaster',
//     description: 'Advanced momentum strategy using quantum-inspired algorithms for crypto markets',
//     roi: 142.5,
//     roiChange: 12.3,
//     tradingPairs: ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'],
//     rating: 4.8,
//     reviews: 247,
//     downloads: 1523,
//     price: 99,
//     riskLevel: 'medium',
//     category: 'Momentum',
//     assetType: 'Cryptocurrency',
//     version: '2.1.0',
//     lastUpdated: '2024-01-15',
//     backtestResults: {
//       totalReturn: 142.5,
//       sharpeRatio: 2.3,
//       maxDrawdown: -8.5,
//       winRate: 67.2
//     },
//     isPro: true,
//     isVerified: true
//   },
//   {
//     id: '2',
//     name: 'Mean Reversion Master',
//     developer: 'TradeWiz',
//     description: 'Statistical mean reversion strategy with adaptive parameters',
//     roi: 89.7,
//     roiChange: -2.1,
//     tradingPairs: ['AAPL', 'MSFT', 'GOOGL'],
//     rating: 4.6,
//     reviews: 156,
//     downloads: 892,
//     price: 'free',
//     riskLevel: 'low',
//     category: 'Mean Reversion',
//     assetType: 'Stocks',
//     version: '1.5.2',
//     lastUpdated: '2024-01-10',
//     backtestResults: {
//       totalReturn: 89.7,
//       sharpeRatio: 1.8,
//       maxDrawdown: -5.2,
//       winRate: 72.5
//     },
//     isPro: false,
//     isVerified: true
//   },
//   {
//     id: '3',
//     name: 'AI Grid Trading Bot',
//     developer: 'CryptoBot Labs',
//     description: 'Machine learning enhanced grid trading with dynamic adjustments',
//     roi: 215.8,
//     roiChange: 8.7,
//     tradingPairs: ['BTC/USD', 'ETH/USD'],
//     rating: 4.9,
//     reviews: 312,
//     downloads: 2156,
//     price: 149,
//     riskLevel: 'high',
//     category: 'Grid Trading',
//     assetType: 'Cryptocurrency',
//     version: '3.0.1',
//     lastUpdated: '2024-01-18',
//     backtestResults: {
//       totalReturn: 215.8,
//       sharpeRatio: 2.7,
//       maxDrawdown: -12.3,
//       winRate: 58.9
//     },
//     isPro: true,
//     isVerified: true
//   }
// ];

// export default function MarketplacePage() {
//   const { theme } = useTheme();
//   const [searchQuery, setSearchQuery] = useState('');
//   const [selectedCategory, setSelectedCategory] = useState('all');
//   const [sortBy, setSortBy] = useState('popularity');
//   const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
//   const [showFilters, setShowFilters] = useState(false);
//   const [filters, setFilters] = useState({
//     assetType: 'all',
//     riskLevel: 'all',
//     priceRange: 'all',
//     rating: 0
//   });

//   const filteredStrategies = useMemo(() => {
//     return mockStrategies.filter(strategy => {
//       const matchesSearch = strategy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
//                            strategy.developer.toLowerCase().includes(searchQuery.toLowerCase()) ||
//                            strategy.description.toLowerCase().includes(searchQuery.toLowerCase());
      
//       const matchesCategory = selectedCategory === 'all' || strategy.category.toLowerCase() === selectedCategory.toLowerCase();
//       const matchesAssetType = filters.assetType === 'all' || strategy.assetType.toLowerCase() === filters.assetType.toLowerCase();
//       const matchesRiskLevel = filters.riskLevel === 'all' || strategy.riskLevel === filters.riskLevel;
//       const matchesRating = strategy.rating >= filters.rating;

//       return matchesSearch && matchesCategory && matchesAssetType && matchesRiskLevel && matchesRating;
//     }).sort((a, b) => {
//       switch (sortBy) {
//         case 'roi-desc':
//           return b.roi - a.roi;
//         case 'roi-asc':
//           return a.roi - b.roi;
//         case 'rating':
//           return b.rating - a.rating;
//         case 'price-asc':
//           const priceA = a.price === 'free' ? 0 : a.price;
//           const priceB = b.price === 'free' ? 0 : b.price;
//           return priceA - priceB;
//         case 'price-desc':
//           const priceA2 = a.price === 'free' ? 0 : a.price;
//           const priceB2 = b.price === 'free' ? 0 : b.price;
//           return priceB2 - priceA2;
//         default:
//           return b.downloads - a.downloads;
//       }
//     });
//   }, [searchQuery, selectedCategory, filters, sortBy]);

//   return (
//     <div className={`min-h-screen ${theme === 'dark' ? 'bg-slate-900' : 'bg-gray-100'}`}>
//       {/* Header */}
//       <div className={`${theme === 'dark' ? 'bg-slate-800' : 'bg-white'} border-b ${theme === 'dark' ? 'border-slate-700' : 'border-gray-200'} sticky top-0 z-10 shadow-lg`}>
//         <div className="max-w-7xl mx-auto px-4 py-6">
//           <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
//             <div>
//               <h1 className={`text-3xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
//                 Strategy & Model Marketplace
//               </h1>
//               <p className={`text-lg ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'} mt-1`}>
//                 Discover and deploy AI-powered trading strategies from top developers
//               </p>
//             </div>
//             <Button className="bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-black font-semibold">
//               Become a Developer
//             </Button>
//           </div>
//         </div>
//       </div>

//       <div className="max-w-7xl mx-auto px-4 py-6">
//         {/* Search and Controls */}
//         <div className="flex flex-col lg:flex-row gap-4 mb-6">
//           <div className="flex-1 relative">
//             <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
//             <Input
//               placeholder="Search strategies, developers, or keywords..."
//               value={searchQuery}
//               onChange={(e) => setSearchQuery(e.target.value)}
//               className="pl-10 h-12"
//             />
//           </div>
          
//           <div className="flex flex-wrap gap-3">
//             <Select value={selectedCategory} onValueChange={setSelectedCategory}>
//               <SelectTrigger className="w-48">
//                 <SelectValue placeholder="All Categories" />
//               </SelectTrigger>
//               <SelectContent>
//                 <SelectItem value="all">All Categories</SelectItem>
//                 <SelectItem value="momentum">Momentum</SelectItem>
//                 <SelectItem value="mean-reversion">Mean Reversion</SelectItem>
//                 <SelectItem value="grid-trading">Grid Trading</SelectItem>
//                 <SelectItem value="arbitrage">Arbitrage</SelectItem>
//               </SelectContent>
//             </Select>

//             <Select value={sortBy} onValueChange={setSortBy}>
//               <SelectTrigger className="w-40">
//                 <SelectValue />
//               </SelectTrigger>
//               <SelectContent>
//                 <SelectItem value="popularity">Most Popular</SelectItem>
//                 <SelectItem value="roi-desc">Highest ROI</SelectItem>
//                 <SelectItem value="roi-asc">Lowest ROI</SelectItem>
//                 <SelectItem value="rating">Top Rated</SelectItem>
//                 <SelectItem value="price-asc">Price: Low to High</SelectItem>
//                 <SelectItem value="price-desc">Price: High to Low</SelectItem>
//               </SelectContent>
//             </Select>

//             <Button
//               variant="outline"
//               onClick={() => setShowFilters(!showFilters)}
//               className="flex items-center gap-2"
//             >
//               <Filter className="h-4 w-4" />
//               Filters
//             </Button>

//             <div className="flex border rounded-lg overflow-hidden">
//               <Button
//                 variant={viewMode === 'grid' ? 'default' : 'ghost'}
//                 size="sm"
//                 onClick={() => setViewMode('grid')}
//                 className="rounded-none"
//               >
//                 <Grid className="h-4 w-4" />
//               </Button>
//               <Button
//                 variant={viewMode === 'list' ? 'default' : 'ghost'}
//                 size="sm"
//                 onClick={() => setViewMode('list')}
//                 className="rounded-none"
//               >
//                 <List className="h-4 w-4" />
//               </Button>
//             </div>
//           </div>
//         </div>

//         {/* Stats Bar */}
//         <div className="flex flex-wrap gap-6 mb-6">
//           <div className="flex items-center gap-2">
//             <div className="w-3 h-3 bg-green-500 rounded-full"></div>
//             <span className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'}`}>
//               {filteredStrategies.length} strategies found
//             </span>
//           </div>
//           <div className="flex items-center gap-2">
//             <TrendingUp className="h-4 w-4 text-blue-500" />
//             <span className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'}`}>
//               Avg ROI: 149.3%
//             </span>
//           </div>
//           <div className="flex items-center gap-2">
//             <Star className="h-4 w-4 text-yellow-500" />
//             <span className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'}`}>
//               Avg Rating: 4.7/5
//             </span>
//           </div>
//         </div>

//         <div className="flex gap-6">
//           {/* Filter Sidebar */}
//           {showFilters && (
//             <div className="w-64 flex-shrink-0">
//               <FilterSidebar filters={filters} onFiltersChange={setFilters} />
//             </div>
//           )}

//           {/* Main Content */}
//           <div className="flex-1">
//             <Tabs defaultValue="browse" className="w-full">
//               <TabsList className="grid w-full grid-cols-3 mb-6">
//                 <TabsTrigger value="browse">Browse All</TabsTrigger>
//                 <TabsTrigger value="trending">Trending</TabsTrigger>
//                 <TabsTrigger value="new">New Releases</TabsTrigger>
//               </TabsList>

//               <TabsContent value="browse" className="space-y-0">
//                 {filteredStrategies.length === 0 ? (
//                   <div className={`text-center py-12 ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'}`}>
//                     <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
//                     <p className="text-lg">No strategies found matching your criteria</p>
//                     <p className="text-sm mt-2">Try adjusting your search or filters</p>
//                   </div>
//                 ) : (
//                   <div className={viewMode === 'grid' 
//                     ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6' 
//                     : 'space-y-4'
//                   }>
//                     {filteredStrategies.map((strategy) => (
//                       <StrategyCard
//                         key={strategy.id}
//                         strategy={strategy}
//                         viewMode={viewMode}
//                       />
//                     ))}
//                   </div>
//                 )}
//               </TabsContent>

//               <TabsContent value="trending" className="space-y-0">
//                 <div className={viewMode === 'grid' 
//                   ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6' 
//                   : 'space-y-4'
//                 }>
//                   {filteredStrategies
//                     .filter(s => s.roiChange > 0)
//                     .slice(0, 6)
//                     .map((strategy) => (
//                       <StrategyCard
//                         key={strategy.id}
//                         strategy={strategy}
//                         viewMode={viewMode}
//                       />
//                     ))}
//                 </div>
//               </TabsContent>

//               <TabsContent value="new" className="space-y-0">
//                 <div className={viewMode === 'grid' 
//                   ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6' 
//                   : 'space-y-4'
//                 }>
//                   {filteredStrategies
//                     .sort((a, b) => new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime())
//                     .slice(0, 6)
//                     .map((strategy) => (
//                       <StrategyCard
//                         key={strategy.id}
//                         strategy={strategy}
//                         viewMode={viewMode}
//                       />
//                     ))}
//                 </div>
//               </TabsContent>
//             </Tabs>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }