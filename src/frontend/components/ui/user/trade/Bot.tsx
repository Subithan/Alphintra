
import { Button } from '@/components/ui/button'; // Assuming you use a Button component
import { useState } from 'react';
import { Play, Square, X } from 'lucide-react';

export default function Bot() {
  const [selectedBot, setSelectedBot] = useState('Bot Alpha');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [amount, setAmount] = useState(50);
  
  const botOptions = ['Bot Alpha', 'Bot Beta', 'Bot Gamma'];

  // Bot descriptions
  const botDescriptions: Record<string, string> = {
    'Bot Alpha': 'A conservative trading bot that focuses on stable returns with minimal risk. Uses advanced technical indicators to identify low-volatility opportunities.',
    'Bot Beta': 'A balanced trading bot that combines growth potential with risk management. Employs both trend-following and mean-reversion strategies.',
    'Bot Gamma': 'An aggressive trading bot designed for maximum returns. Utilizes high-frequency trading strategies and leverages market volatility.'
  };

  const handleStart = () => {
    setIsModalOpen(true);
  };

  const handleConfirmStart = () => {
    console.log(`Starting ${selectedBot} with ${amount}% of capital`);
    // TODO: Make API call to start the bot
    // Example: POST to /api/trading/bot/start with { userId: 2, strategyId: 1, amount: amount }
    setIsModalOpen(false);
  };

  const handleEnd = () => {
    console.log(`Ending ${selectedBot}`);
    // TODO: Make API call to stop the bot
    // Example: POST to /api/trading/bots/stop
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setAmount(50); 
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
            <Button onClick={handleStart} className='bg-[#0b9981] hover:bg-[#0b9981] hover:scale-105'>
              <Play className="w-4 h-4 mr-2" />
              Start
            </Button>
            <Button onClick={handleEnd} variant="destructive" className='hover:scale-105'>
              <Square className="w-4 h-4 mr-2" />
              End
            </Button>
          </div>
        </div>

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
                    This will allocate {amount}% of your available capital to {selectedBot}.
                  </p>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="flex gap-3 p-6 border-t border-border">
                <Button
                  onClick={handleCloseModal}
                  variant="outline"
                  className="flex-1 border-gray-400 dark:border-gray-600"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleConfirmStart}
                  className="flex-1 bg-[#0b9981] hover:bg-[#0b9981] hover:scale-105"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Start Bot
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

  );
}
