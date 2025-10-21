import { Button } from '@/components/ui/button';
import { useState, useEffect } from 'react';
import { Play, Square, X } from 'lucide-react';
import { tradingApi } from '@/lib/api/trading-api';
import { getUserId } from '@/lib/auth';

export default function Bot() {
  const [selectedBot, setSelectedBot] = useState('Bot Alpha');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [amount, setAmount] = useState(50);
  const [selectedCoin, setSelectedCoin] = useState('BTC/USDT');
  const [userId, setUserId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showStopConfirm, setShowStopConfirm] = useState(false);
  const [hasRunningBot, setHasRunningBot] = useState(false);
  const [checkingBots, setCheckingBots] = useState(true);
  
  const botOptions = ['Untitled Model', 'Subi'
  ];
  const coinOptions = [
    'BTC/USDT',
    'ETH/USDT',
    'BNB/USDT',
    'SOL/USDT',
    'XRP/USDT',
    'ADA/USDT',
    'DOGE/USDT',
    'MATIC/USDT',
    'DOT/USDT',
    'AVAX/USDT',
    'LINK/USDT',
    'UNI/USDT',
    'ATOM/USDT',
    'ETC/USDT',
    'LTC/USDT'
  ];

  // Bot descriptions
  const botDescriptions: Record<string, string> = {
    'Untiled Model': 'A conservative trading bot that focuses on stable returns with minimal risk. Uses advanced technical indicators to identify low-volatility opportunities.',
    'Subi': 'A balanced trading bot that combines growth potential with risk management. Employs both trend-following and mean-reversion strategies.',
   
  };

  // Map bot names to strategy IDs
  const botStrategyMap: Record<string, number> = {
    'Untiled Model': 1,
    'Subi': 1
  };

  useEffect(() => {
    const currentUserId = getUserId();
    setUserId(currentUserId);
    
    // Check for running bots
    if (currentUserId) {
      checkForRunningBots(currentUserId);
    }
  }, []);

  const checkForRunningBots = async (userId: number) => {
    try {
      setCheckingBots(true);
      const bots = await tradingApi.getAllBots(userId);
      const runningBot = bots.find(bot => bot.status === 'RUNNING');
      setHasRunningBot(!!runningBot);
    } catch (err) {
      console.error('Failed to check for running bots:', err);
    } finally {
      setCheckingBots(false);
    }
  };

  const handleStart = () => {
    if (hasRunningBot) {
      setError('You already have a running bot. Please stop it before starting a new one.');
      setTimeout(() => setError(null), 5000);
      return;
    }
    
    setError(null);
    setSuccessMessage(null);
    setIsModalOpen(true);
  };

  const handleConfirmStart = async () => {
    if (!userId) {
      setError('User not authenticated');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const strategyId = botStrategyMap[selectedBot];
      console.log(`Starting ${selectedBot} with ${amount}% of capital on ${selectedCoin}`);
      
      const response = await tradingApi.startBot({
        userId: userId,
        strategyId: strategyId,
        symbol: selectedCoin,
        capitalAllocation: amount
      });

      console.log('Bot started successfully:', response);
      setIsModalOpen(false);
      setSuccessMessage(`${selectedBot} started successfully on ${selectedCoin}!`);
      setHasRunningBot(true); // Update state to reflect new running bot
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
      
    } catch (err: any) {
      console.error('Failed to start bot:', err);
      setError(err.message || 'Failed to start bot. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEnd = async () => {
    setShowStopConfirm(true);
  };

  const handleConfirmStop = async () => {
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);
    setShowStopConfirm(false);

    try {
      console.log(`Stopping all bots`);
      const response = await tradingApi.stopAllBots();
      console.log('Bots stopped successfully:', response);
      setSuccessMessage(`${response.message} (${response.botsStoppedCount} bot${response.botsStoppedCount !== 1 ? 's' : ''} stopped)`);
      setHasRunningBot(false); // Update state to reflect no running bots
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
      
    } catch (err: any) {
      console.error('Failed to stop bots:', err);
      setError(err.message || 'Failed to stop bots. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setAmount(50);
    setSelectedCoin('BTC/USDT');
    setError(null);
  };

  return (
      <div>
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          {/* Dropdown */}
          <select
            value={selectedBot}
            onChange={(e) => setSelectedBot(e.target.value)}
            className="border border-gray-100 bg-background p-2 rounded-md text-sm w-[500px]"
          >
            {botOptions.map((bot) => (
              <option key={bot} value={bot}>
                {bot}
              </option>
            ))}
          </select>

          {/* Buttons */}
          <div className="flex gap-2">
            <Button 
              onClick={handleStart} 
              disabled={isLoading || !userId || checkingBots || hasRunningBot}
              className='bg-[#0b9981] hover:bg-[#0b9981] hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed'
              title={hasRunningBot ? 'Stop the current bot before starting a new one' : 'Start trading bot'}
            >
              <Play className="w-4 h-4 mr-2" />
              {hasRunningBot ? 'Bot Running' : 'Start'}
            </Button>
            <Button 
              onClick={handleEnd} 
              disabled={isLoading || !userId || !hasRunningBot}
              variant="destructive" 
              className='hover:scale-105'
            >
              <Square className="w-4 h-4 mr-2" />
              End
            </Button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-3 p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-md">
            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {successMessage && (
          <div className="mt-3 p-3 bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 rounded-md">
            <p className="text-sm text-green-800 dark:text-green-200">{successMessage}</p>
          </div>
        )}

        {/* Stop Confirmation Modal */}
        {showStopConfirm && (
          <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-background border border-border rounded-lg shadow-xl max-w-md w-full mx-4">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-border">
                <h2 className="text-xl font-semibold text-red-600 dark:text-red-400">Stop All Bots</h2>
                <button
                  onClick={() => setShowStopConfirm(false)}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-6">
                <p className="text-sm text-muted-foreground mb-4">
                  Are you sure you want to stop all running trading bots? This action will halt all active trading operations.
                </p>
              </div>

              {/* Modal Footer */}
              <div className="flex gap-3 p-6 border-t border-border">
                <Button
                  onClick={() => setShowStopConfirm(false)}
                  variant="outline"
                  disabled={isLoading}
                  className="flex-1 border-gray-400 dark:border-gray-600"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleConfirmStop}
                  disabled={isLoading}
                  variant="destructive"
                  className="flex-1 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <span className="animate-spin mr-2">⏳</span>
                      Stopping...
                    </>
                  ) : (
                    <>
                      <Square className="w-4 h-4 mr-2" />
                      Stop All Bots
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-background border border-border rounded-lg shadow-xl max-w-md w-full mx-4">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-border">
                <h2 className="text-xl font-semibold">Start {selectedBot}</h2>
                <button
                  onClick={handleCloseModal}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-6 space-y-6">
                {/* Bot Description */}
                <div>
                  <h3 className="text-sm font-medium mb-2">Description</h3>
                  <p className="text-sm text-muted-foreground">
                    {botDescriptions[selectedBot]}
                  </p>
                </div>

                {/* Coin Selection */}
                <div>
                  <label className="text-sm font-medium mb-2 block">Trading Pair</label>
                  <select
                    value={selectedCoin}
                    onChange={(e) => setSelectedCoin(e.target.value)}
                    className="w-full border border-gray-300 dark:border-gray-600 bg-background p-2.5 rounded-md text-sm focus:ring-2 focus:ring-[#0b9981] focus:border-transparent"
                  >
                    {coinOptions.map((coin) => (
                      <option key={coin} value={coin}>
                        {coin}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Amount Slider */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Capital Allocation</label>
                    <span className="text-sm font-semibold text-[#0b9981]">{amount}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={amount}
                    onChange={(e) => setAmount(Number(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 accent-[#0b9981]"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>0%</span>
                    <span>50%</span>
                    <span>100%</span>
                  </div>
                </div>

                {/* Info Message */}
                <div className="bg-muted p-3 rounded-md">
                  <p className="text-xs text-muted-foreground">
                    This will allocate {amount}% of your available capital to {selectedBot} trading {selectedCoin}.
                  </p>
                </div>

                {/* Error Message in Modal */}
                {error && (
                  <div className="p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-md">
                    <p className="text-xs text-red-800 dark:text-red-200">{error}</p>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="flex gap-3 p-6 border-t border-border">
                <Button
                  onClick={handleCloseModal}
                  variant="outline"
                  disabled={isLoading}
                  className="flex-1 border-gray-400 dark:border-gray-600"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleConfirmStart}
                  disabled={isLoading || !userId}
                  className="flex-1 bg-[#0b9981] hover:bg-[#0b9981] hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <span className="animate-spin mr-2">⏳</span>
                      Starting...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Start Bot
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

  );
}
