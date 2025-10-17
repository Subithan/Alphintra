import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface FilterSidebarProps {
  filters: { assetType: string; riskLevel: string; priceRange: string; rating: number; verificationStatus: string };
  onFiltersChange: (filters: any) => void;
}

export default function FilterSidebar({ filters, onFiltersChange }: FilterSidebarProps) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Asset Type</label>
        <Select value={filters.assetType} onValueChange={(v) => onFiltersChange({ ...filters, assetType: v })}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="cryptocurrency">Cryptocurrency</SelectItem>
            <SelectItem value="equities">Equities</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Risk Level</label>
        <Select value={filters.riskLevel} onValueChange={(v) => onFiltersChange({ ...filters, riskLevel: v })}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="low">Low</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="high">High</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Min Rating</label>
        <Slider
          value={[filters.rating]}
          onValueChange={(v) => onFiltersChange({ ...filters, rating: v[0] })}
          min={0}
          max={5}
          step={0.5}
        />
        <p className="text-sm mt-1">{filters.rating}</p>
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Verification Status</label>
        <Select value={filters.verificationStatus} onValueChange={(v) => onFiltersChange({ ...filters, verificationStatus: v })}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="PENDING">Pending</SelectItem>
            <SelectItem value="APPROVED">Approved</SelectItem>
            <SelectItem value="REJECTED">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}