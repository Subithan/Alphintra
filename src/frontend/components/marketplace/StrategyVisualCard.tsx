import { Star, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useTheme } from './useTheme';
import { Strategy } from './types';

interface StrategyVisualCardProps {
  strategy: Strategy;
  onClick: () => void;
  viewMode: 'grid' | 'list';
}

export default function StrategyVisualCard({ strategy, onClick, viewMode }: StrategyVisualCardProps) {
  const { theme } = useTheme();

  const getGradientStyle = (colors: string[]) => ({
    background: `linear-gradient(135deg, ${colors.join(', ')})`,
  });

  const getThumbnailContent = () => {
    // [Same as original]
  };

  const getRiskVariant = () => {
    // [Same as original]
  };

  const cardClass = viewMode === 'list' ? 'flex flex-row items-center' : 'flex flex-col';
  const thumbnailClass = viewMode === 'list' ? 'w-1/3 h-32' : 'h-48 w-full';

  return (
    <div 
      onClick={onClick}
      className={`${cardClass} rounded-lg overflow-hidden ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} border ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} hover:shadow-xl transition-all cursor-pointer hover:scale-105`}
    >
      <div className={`relative overflow-hidden ${thumbnailClass}`}>
        {getThumbnailContent()}
        {strategy.isVerified && (
          <div className="absolute top-2 right-2 w-8 h-8 bg-white/90 rounded-full flex items-center justify-center backdrop-blur-sm">
            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </div>

      <div className="p-4 flex-1">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className={`font-semibold text-sm ${theme === 'dark' ? 'text-white' : 'text-gray-900'} line-clamp-1`}>
              {strategy.name}
            </h3>
            <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} mb-1`}>
              By {strategy.creatorName}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-2">
          <Badge variant={getRiskVariant()}>
            {strategy.riskLevel.charAt(0).toUpperCase() + strategy.riskLevel.slice(1)} Risk
          </Badge>
        </div>

        <div className="flex items-center justify-between text-xs mb-3">
          <div className="flex items-center gap-1">
            <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
            <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>{strategy.rating} ({strategy.reviewCount})</span>
          </div>
          <div className="flex items-center gap-1">
            <Users className="h-3 w-3 text-gray-400" />
            <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>{strategy.subscriberCount}</span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className={`text-sm font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {strategy.performance.totalReturn}% Return
          </span>
          <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            {strategy.revenueSharePercentage}% Share
          </span>
        </div>
      </div>
    </div>
  );
}