import { Star, X, Twitter } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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
    switch (strategy.thumbnail) {
      case 'bull-rider':
      case 'bear-trader':
        return (
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center">
              <div className="text-6xl mb-4">₿</div>
              <div className="text-3xl font-bold text-white mb-2">{strategy.name}</div>
              <div className="text-5xl font-black text-white">{strategy.description}</div>
            </div>
          </div>
        );
      default:
        return (
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center">
              <div className="text-4xl font-bold text-white">{strategy.name}</div>
              <div className="text-2xl font-medium text-white mt-2">{strategy.description}</div>
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

        <div className="relative w-full h-48 sm:h-56 md:h-64 lg:h-72">
          {getThumbnailContent()}
        </div>

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
            <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Creator</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.creatorName}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Category</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.category}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Asset Type</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.assetType}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Trading Pairs</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.tradingPairs.join(', ')}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Verification</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.verificationStatus}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Last Updated</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.lastUpdated}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Price</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.price === 'free' ? 'Free' : `$${strategy.price.toFixed(2)}`}</dd>
              </div>
            </dl>
          </div>

          <div className="mb-4">
            <h3 className={`text-lg sm:text-xl font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>Performance</h3>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Total Return</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.performance.totalReturn}%</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Annualized Return</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.performance.annualizedReturn}%</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Max Drawdown</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.performance.maxDrawdown}%</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Sharpe Ratio</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.performance.sharpeRatio}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Win Rate</dt>
                <dd className={`mt-1 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{strategy.performance.winRate}%</dd>
              </div>
            </dl>
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
            Buy {strategy.price === 'free' ? 'Free' : `$${strategy.price.toFixed(2)}`}
          </Button>

          <p className={`text-xs sm:text-sm text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} mb-4`}>
            Price includes 1 month of updates.
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
}