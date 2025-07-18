
import { Button } from '@/components/ui/button'; // Assuming you use a Button component
import { useState } from 'react';
import { Play, Square } from 'lucide-react';

export default function Bot() {
  const [selectedBot, setSelectedBot] = useState('Bot Alpha');
  const botOptions = ['Bot Alpha', 'Bot Beta', 'Bot Gamma'];

  const handleStart = () => {
    console.log(`Starting ${selectedBot}`);
  };

  const handleEnd = () => {
    console.log(`Ending ${selectedBot}`);
  };

  return (
      <div>
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          {/* Dropdown */}
          <select
            value={selectedBot}
            onChange={(e) => setSelectedBot(e.target.value)}
            className="border border-input bg-background p-2 rounded-md text-sm w-[500px]"
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
      </div>

  );
}
