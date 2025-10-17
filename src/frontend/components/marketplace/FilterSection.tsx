import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface FilterSectionProps {
  selectedCategory: string;
  setSelectedCategory: (value: string) => void;
  filters: { assetType: string; riskLevel: string; priceRange: string; rating: number; verificationStatus: string };
  setFilters: (filters: any) => void;
}

export default function FilterSection({ selectedCategory, setSelectedCategory, filters, setFilters }: FilterSectionProps) {
  return (
    <div className="flex flex-wrap gap-3 mb-6">
      <Select value={selectedCategory} onValueChange={setSelectedCategory}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="All sorted" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All sorted</SelectItem>
          <SelectItem value="momentum">Momentum</SelectItem>
          <SelectItem value="mean-reversion">Mean Reversion</SelectItem>
          <SelectItem value="trend">Trend Following</SelectItem>
          <SelectItem value="arbitrage">Arbitrage</SelectItem>
        </SelectContent>
      </Select>

      <Select value={filters.assetType} onValueChange={(value) => setFilters({ ...filters, assetType: value })}>
        <SelectTrigger className="w-52">
          <SelectValue placeholder="Free & paid Strategies" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Free & paid Strategies</SelectItem>
          <SelectItem value="free">Free Only</SelectItem>
          <SelectItem value="paid">Paid Only</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}