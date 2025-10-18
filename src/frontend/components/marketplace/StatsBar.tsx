import { TrendingUp, Star } from 'lucide-react';
import { Strategy } from './types';
import { useTheme } from './useTheme';

interface StatsBarProps {
  filteredStrategies: Strategy[];
}

export default function StatsBar({ filteredStrategies }: StatsBarProps) {
  const { theme } = useTheme();
  if (filteredStrategies.length === 0) return null;

  const avgRoi = (filteredStrategies.reduce((sum, s) => sum + s.performance.totalReturn, 0) / filteredStrategies.length).toFixed(1);
  const avgRating = (filteredStrategies.reduce((sum, s) => sum + s.rating, 0) / filteredStrategies.length).toFixed(1);

  return (
    <div className="flex flex-wrap gap-6 mb-6">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
        <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
          {filteredStrategies.length} strategies found
        </span>
      </div>
      <div className="flex items-center gap-2">
        <TrendingUp className="h-4 w-4 text-blue-500" />
        <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
          Avg ROI: {avgRoi}%
        </span>
      </div>
      <div className="flex items-center gap-2">
        <Star className="h-4 w-4 text-yellow-500" />
        <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
          Avg Rating: {avgRating}/5
        </span>
      </div>
    </div>
  );
}