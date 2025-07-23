'use client';

import React from 'react';
import { Star, DollarSign, TrendingUp, Shield } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { useTheme } from 'next-themes';

interface FilterSidebarProps {
  filters: {
    assetType: string;
    riskLevel: string;
    priceRange: string;
    rating: number;
  };
  onFiltersChange: (filters: any) => void;
}

const FilterSidebar: React.FC<FilterSidebarProps> = ({ filters, onFiltersChange }) => {
  const { theme } = useTheme();

  const handleFilterChange = (key: string, value: any) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const resetFilters = () => {
    onFiltersChange({
      assetType: 'all',
      riskLevel: 'all',
      priceRange: 'all',
      rating: 0
    });
  };

  return (
    <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} sticky top-24`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className={`text-lg ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            Filters
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={resetFilters} className="text-xs">
            Reset
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Asset Type Filter */}
        <div>
          <label className={`text-sm font-medium mb-3 block ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
            Asset Type
          </label>
          <Select value={filters.assetType} onValueChange={(value) => handleFilterChange('assetType', value)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Assets</SelectItem>
              <SelectItem value="cryptocurrency">Cryptocurrency</SelectItem>
              <SelectItem value="stocks">Stocks</SelectItem>
              <SelectItem value="forex">Forex</SelectItem>
              <SelectItem value="commodities">Commodities</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Risk Level Filter */}
        <div>
          <label className={`text-sm font-medium mb-3 block ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
            Risk Level
          </label>
          <div className="space-y-2">
            {['all', 'low', 'medium', 'high'].map((risk) => (
              <div key={risk} className="flex items-center">
                <input
                  type="radio"
                  id={`risk-${risk}`}
                  name="riskLevel"
                  value={risk}
                  checked={filters.riskLevel === risk}
                  onChange={(e) => handleFilterChange('riskLevel', e.target.value)}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <label 
                  htmlFor={`risk-${risk}`}
                  className={`ml-2 text-sm capitalize cursor-pointer ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}
                >
                  {risk === 'all' ? 'All Levels' : `${risk} Risk`}
                  {risk !== 'all' && (
                    <Shield className={`inline-block ml-1 h-3 w-3 ${
                      risk === 'low' ? 'text-green-500' : 
                      risk === 'medium' ? 'text-yellow-500' : 'text-red-500'
                    }`} />
                  )}
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Price Range Filter */}
        <div>
          <label className={`text-sm font-medium mb-3 block ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
            <DollarSign className="inline-block h-4 w-4 mr-1" />
            Price Range
          </label>
          <div className="space-y-2">
            {[
              { value: 'all', label: 'All Prices' },
              { value: 'free', label: 'Free Only' },
              { value: '0-50', label: '$0 - $50' },
              { value: '50-100', label: '$50 - $100' },
              { value: '100-200', label: '$100 - $200' },
              { value: '200+', label: '$200+' }
            ].map((price) => (
              <div key={price.value} className="flex items-center">
                <input
                  type="radio"
                  id={`price-${price.value}`}
                  name="priceRange"
                  value={price.value}
                  checked={filters.priceRange === price.value}
                  onChange={(e) => handleFilterChange('priceRange', e.target.value)}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <label 
                  htmlFor={`price-${price.value}`}
                  className={`ml-2 text-sm cursor-pointer ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}
                >
                  {price.label}
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Rating Filter */}
        <div>
          <label className={`text-sm font-medium mb-3 block ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
            <Star className="inline-block h-4 w-4 mr-1" />
            Minimum Rating
          </label>
          <div className="px-2">
            <Slider
              value={[filters.rating]}
              onValueChange={(value) => handleFilterChange('rating', value[0])}
              max={5}
              min={0}
              step={0.5}
              className="w-full"
            />
            <div className="flex justify-between text-xs mt-2">
              <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>0</span>
              <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                {filters.rating > 0 ? `${filters.rating}+ stars` : 'Any rating'}
              </span>
              <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>5</span>
            </div>
          </div>
        </div>

        {/* Quick Filters */}
        <div>
          <label className={`text-sm font-medium mb-3 block ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
            Quick Filters
          </label>
          <div className="space-y-2">
            <Button variant="outline" size="sm" className="w-full justify-start">
              <TrendingUp className="h-4 w-4 mr-2" />
              Top Performers
            </Button>
            <Button variant="outline" size="sm" className="w-full justify-start">
              <Star className="h-4 w-4 mr-2" />
              Highest Rated
            </Button>
            <Button variant="outline" size="sm" className="w-full justify-start">
              <Shield className="h-4 w-4 mr-2" />
              Verified Only
            </Button>
          </div>
        </div>

        {/* Popular Tags */}
        <div>
          <label className={`text-sm font-medium mb-3 block ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
            Popular Tags
          </label>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors">
              AI-Powered
            </Badge>
            <Badge variant="secondary" className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors">
              Scalping
            </Badge>
            <Badge variant="secondary" className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors">
              DeFi
            </Badge>
            <Badge variant="secondary" className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors">
              Backtested
            </Badge>
            <Badge variant="secondary" className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors">
              Multi-Asset
            </Badge>
            <Badge variant="secondary" className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors">
              Low Drawdown
            </Badge>
          </div>
        </div>

        {/* Applied Filters Summary */}
        {(filters.assetType !== 'all' || filters.riskLevel !== 'all' || filters.priceRange !== 'all' || filters.rating > 0) && (
          <div>
            <label className={`text-sm font-medium mb-3 block ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
              Applied Filters
            </label>
            <div className="space-y-2">
              {filters.assetType !== 'all' && (
                <Badge variant="default" className="mr-1 mb-1">
                  {filters.assetType}
                  <button 
                    onClick={() => handleFilterChange('assetType', 'all')}
                    className="ml-1 hover:bg-white/20 rounded-full"
                  >
                    ×
                  </button>
                </Badge>
              )}
              {filters.riskLevel !== 'all' && (
                <Badge variant="default" className="mr-1 mb-1">
                  {filters.riskLevel} risk
                  <button 
                    onClick={() => handleFilterChange('riskLevel', 'all')}
                    className="ml-1 hover:bg-white/20 rounded-full"
                  >
                    ×
                  </button>
                </Badge>
              )}
              {filters.priceRange !== 'all' && (
                <Badge variant="default" className="mr-1 mb-1">
                  {filters.priceRange === 'free' ? 'Free' : `$${filters.priceRange}`}
                  <button 
                    onClick={() => handleFilterChange('priceRange', 'all')}
                    className="ml-1 hover:bg-white/20 rounded-full"
                  >
                    ×
                  </button>
                </Badge>
              )}
              {filters.rating > 0 && (
                <Badge variant="default" className="mr-1 mb-1">
                  {filters.rating}+ stars
                  <button 
                    onClick={() => handleFilterChange('rating', 0)}
                    className="ml-1 hover:bg-white/20 rounded-full"
                  >
                    ×
                  </button>
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default FilterSidebar;