import StrategyVisualCard from './StrategyVisualCard';
import { Strategy } from './types';

interface StrategyGridProps {
  filteredStrategies: Strategy[];
  setSelectedStrategy: (strategy: Strategy) => void;
  viewMode: 'grid' | 'list';
}

export default function StrategyGrid({ filteredStrategies, setSelectedStrategy, viewMode }: StrategyGridProps) {
  return (
    <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4' : 'flex flex-col space-y-4'}>
      {filteredStrategies.map((strategy) => (
        <StrategyVisualCard 
          key={strategy.id} 
          strategy={strategy}
          onClick={() => setSelectedStrategy(strategy)}
          viewMode={viewMode}
        />
      ))}
    </div>
  );
}