import { Search, Filter, Grid, List } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useTheme } from './useTheme';

interface FilterSectionProps {
  selectedCategory: string;
  setSelectedCategory: (value: string) => void;
  filters: { assetType: string; riskLevel: string; priceRange: string; rating: number; verificationStatus: string };
  setFilters: (filters: any) => void;
  searchQuery: string;
  setSearchQuery: (value: string) => void;
  sortBy: string;
  setSortBy: (value: string) => void;
  showFilters: boolean;
  setShowFilters: (value: boolean) => void;
  viewMode: 'grid' | 'list';
  setViewMode: (value: 'grid' | 'list') => void;
}

export default function FilterSection({
  selectedCategory, setSelectedCategory, filters, setFilters, searchQuery, setSearchQuery, sortBy, setSortBy, showFilters, setShowFilters, viewMode, setViewMode
}: FilterSectionProps) {
  const { theme } = useTheme();

  return (
    <div className="flex flex-col lg:flex-row gap-4 mb-6">
      <div className="flex-1 relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
        <Input
          placeholder="Search strategies, developers, or keywords..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10 h-12"
        />
      </div>
      
      <div className="flex flex-wrap gap-3">
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="momentum">Momentum</SelectItem>
            <SelectItem value="mean-reversion">Mean Reversion</SelectItem>
            <SelectItem value="trend">Trend Following</SelectItem>
            <SelectItem value="arbitrage">Arbitrage</SelectItem>
          </SelectContent>
        </Select>

        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="popularity">Most Popular</SelectItem>
            <SelectItem value="roi-desc">Highest ROI</SelectItem>
            <SelectItem value="rating">Top Rated</SelectItem>
            <SelectItem value="price-asc">Price: Low to High</SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2"
        >
          <Filter className="h-4 w-4" />
          Filters
        </Button>

        <div className="flex border rounded-lg overflow-hidden">
          <Button
            variant={viewMode === 'grid' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('grid')}
            className="rounded-none"
          >
            <Grid className={`h-4 w-4 ${viewMode === 'grid' ? 'text-white' : 'text-gray-600'}`} />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('list')}
            className="rounded-none"
          >
            <List className={`h-4 w-4 ${viewMode === 'list' ? 'text-white' : 'text-gray-600'}`} />
          </Button>
        </div>
      </div>
    </div>
  );
}