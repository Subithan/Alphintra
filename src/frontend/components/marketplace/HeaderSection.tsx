import { useTheme } from './useTheme';

export default function HeaderSection() {
  const { theme } = useTheme();
  return (
    <div className={`${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} border-b ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Marketplace</span>
            <span className={`text-sm ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`}>&gt;</span>
            <span className={`text-sm font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>Strategies</span>
          </div>
        </div>
      </div>
    </div>
  );
}