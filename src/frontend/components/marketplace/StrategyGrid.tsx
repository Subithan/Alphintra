import StrategyVisualCard from './StrategyVisualCard';
import { Strategy } from './types';

interface StrategyGridProps {
  filteredStrategies: Strategy[];
  viewMode: 'grid' | 'list';
  onSelectStrategy: (strategy: Strategy) => void;
}

export default function StrategyGrid({ filteredStrategies, viewMode, onSelectStrategy }: StrategyGridProps) {
  return (
    <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4' : 'space-y-4'}>
      {filteredStrategies.map((strategy) => (
        <StrategyVisualCard 
          key={strategy.id} 
          strategy={strategy}
          viewMode={viewMode}
          onClick={() => onSelectStrategy(strategy)}
        />
      ))}
    </div>
  );
}