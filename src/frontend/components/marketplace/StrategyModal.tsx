import { Star, X, Twitter } from 'lucide-react';
import { Badge, Button } from '@/components/ui';
import { useTheme } from './useTheme';
import { Strategy } from './types';

interface StrategyModalProps {
  strategy: Strategy;
  onClose: () => void;
}

export default function StrategyModal({ strategy, onClose }: StrategyModalProps) {
  const { theme } = useTheme();

  const getGradientStyle = (colors: string[]) => ({
    background: `linear-gradient(135deg, ${colors.join(', ')})`,
  });

  const getThumbnailContent = () => {
    // [Same as original implementation]
  };

  const getRiskVariant = () => {
    // [Same as original implementation]
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-md"></div>
      
      <div 
        className={`relative w-full max-w-md sm:max-w-lg md:max-w-xl lg:max-w-2xl ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} rounded-lg sm:rounded-xl md:rounded-2xl shadow-2xl overflow-hidden transform transition-all duration-300 ease-in-out`}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-2 right-2 z-20 w-8 h-8 flex items-center justify-center rounded-full bg-black/30 hover:bg-black/50 text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Responsive thumbnail section */}
        <div className="relative w-full h-48 sm:h-56 md:h-64 lg:h-72">
          {getThumbnailContent()}
        </div>

        {/* Scrollable content section */}
        <div className="p-4 sm:p-6 max-h-96 overflow-y-auto">
          <h2 className={`text-xl sm:text-2xl font-bold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {strategy.name}
          </h2>
          <p className={`text-sm sm:text-base ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} mb-4`}>
            {strategy.description}
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 mb-4">
            <div className="flex items-center gap-1 mb-2 sm:mb-0">
              <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Type:</span>
              <Badge className="bg-cyan-500 text-white">Strategy</Badge>
            </div>
            <div className="flex items-center gap-1">
              {[...Array(5)].map((_, i) => (
                <Star 
                  key={i} 
                  className={`h-4 w-4 sm:h-5 sm:w-5 ${i < Math.floor(strategy.rating) ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'}`}
                />
              ))}
              <span className={`text-sm ml-1 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                ({strategy.reviewCount})
              </span>
            </div>
          </div>

          <div className="mb-4">
            <h3 className={`text-lg sm:text-xl font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>Details</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm sm:text-base items-start">
              <p className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>Creator: {strategy.creatorName}</p>
              <p className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>Category: {strategy.category}</p>
              <p className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>Asset Type: {strategy.assetType}</p>
              <p className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>Trading Pairs: {strategy.tradingPairs.join(', ')}</p>
              <p className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>Verification: {strategy.verificationStatus}</p>
              <p className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>Last Updated: {strategy.lastUpdated}</p>
            </div>
          </div>

          <div className="mb-4">
            <h3 className={`text-lg sm:text-xl font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>Performance</h3>
            <div className="grid grid-cols-2 gap-2 text-sm sm:text-base items-start">
              <div className="flex flex-col">
                <span className={`font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Total Return</span>
                <span className={`${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{strategy.performance.totalReturn}%</span>
              </div>
              <div className="flex flex-col">
                <span className={`font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Annualized Return</span>
                <span className={`${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{strategy.performance.annualizedReturn}%</span>
              </div>
              <div className="flex flex-col">
                <span className={`font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Max Drawdown</span>
                <span className={`${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{strategy.performance.maxDrawdown}%</span>
              </div>
              <div className="flex flex-col">
                <span className={`font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Sharpe Ratio</span>
                <span className={`${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{strategy.performance.sharpeRatio}</span>
              </div>
              <div className="flex flex-col">
                <span className={`font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Win Rate</span>
                <span className={`${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{strategy.performance.winRate}%</span>
              </div>
            </div>
          </div>

          <div className="mb-4">
            <h3 className={`text-lg sm:text-xl font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>Usage</h3>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
              <p className={`text-sm sm:text-base ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>Subscribers: {strategy.subscriberCount}</p>
              <Badge variant={getRiskVariant()} className="mt-2 sm:mt-0">
                {strategy.riskLevel.charAt(0).toUpperCase() + strategy.riskLevel.slice(1)} Risk
              </Badge>
            </div>
          </div>

          <Button className="w-full bg-cyan-500 hover:bg-cyan-600 text-white mb-4">
            Use Strategy • {strategy.revenueSharePercentage}% Revenue Share
          </Button>

          <p className={`text-xs sm:text-sm text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} mb-4`}>
            Free to use with revenue share for creator.
          </p>

          <div className="flex justify-center">
            <button className="flex items-center gap-2 text-gray-400 hover:text-gray-600 transition-colors">
              <Twitter className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};