import { Star, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useTheme } from './useTheme';
import { Strategy } from './types';

interface StrategyVisualCardProps {
  strategy: Strategy;
  onClick: () => void;
}

export default function StrategyVisualCard({ strategy, onClick }: StrategyVisualCardProps) {
  const { theme } = useTheme();

  const getGradientStyle = (colors: string[]) => ({
    background: `linear-gradient(135deg, ${colors.join(', ')})`,
  });

  const getThumbnailContent = () => {
    switch (strategy.thumbnail) {
      case 'bull-rider':
        return (
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center">
              <div className="text-4xl mb-2">₿</div>
              <div className="text-xl font-bold text-white mb-1">{strategy.name}</div>
              <div className="text-3xl font-black text-white">{strategy.description}</div>
            </div>
          </div>
        );
      case 'bear-trader':
        return (
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center">
              <div className="text-4xl mb-2">₿</div>
              <div className="text-xl font-bold text-white mb-1">{strategy.name}</div>
              <div className="text-3xl font-black text-white">{strategy.description}</div>
            </div>
          </div>
        );
      case 'market-reversal':
        return (
          <div className="relative w-full h-full flex flex-col items-center justify-center p-4">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center w-full">
              <div className="text-4xl font-black text-white mb-2">MARKET REVERSAL</div>
              <div className="flex items-center justify-center gap-2 mb-2">
                <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-sm">🐺</span>
                </div>
                <span className="text-lg font-bold text-white">WOLF AI</span>
              </div>
            </div>
          </div>
        );
      case 'ai-confirmation':
        return (
          <div className="relative w-full h-full flex flex-col items-center justify-center p-4">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center w-full">
              <div className="text-4xl font-black text-white mb-2">AI CONFIRMATION</div>
              <div className="flex items-center justify-center gap-2 mb-2">
                <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-sm">🐺</span>
                </div>
                <span className="text-lg font-bold text-white">WOLF AI</span>
              </div>
            </div>
          </div>
        );
      case 'dip-raider':
        return (
          <div className="relative w-full h-full flex items-center justify-center p-4">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center">
              <div className="text-5xl font-black text-white leading-tight">
                DIP<br/>RAIDER
              </div>
            </div>
          </div>
        );
      default:
        const timeframe = strategy.thumbnail === 'apex-5min' ? '5 MINUTES' : 
                         strategy.thumbnail === 'apex-4h' ? '4 HOURS' : '1 MINUTE';
        return (
          <div className="relative w-full h-full flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-gradient-to-br from-gray-700 via-gray-800 to-gray-900"></div>
            <div className="relative z-10 text-center">
              <div className="text-4xl font-black text-white mb-2">APEX AI<br/>TREND</div>
              <div className="text-2xl font-bold text-white mb-4">{timeframe}</div>
              <div className="flex items-center justify-center gap-2">
                <span className="text-orange-500 font-bold">RYZE</span>
                <span className="text-white font-bold">×</span>
                <span className="text-red-500 font-bold">TRADE</span>
              </div>
            </div>
          </div>
        );
    }
  };

  const getRiskVariant = () => {
    switch (strategy.riskLevel) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'destructive';
      default:
        return 'default';
    }
  };

  return (
    <div 
      onClick={onClick}
      className={`rounded-lg overflow-hidden ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} border ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} hover:shadow-xl transition-all cursor-pointer hover:scale-105`}
    >
      {/* Thumbnail section */}
      <div className="relative h-48 w-full overflow-hidden">
        {getThumbnailContent()}
        {strategy.isVerified && (
          <div className="absolute top-2 right-2 w-8 h-8 bg-white/90 rounded-full flex items-center justify-center backdrop-blur-sm">
            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </div>

      {/* Minimal details section for card */}
      <div className="p-4">
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
};