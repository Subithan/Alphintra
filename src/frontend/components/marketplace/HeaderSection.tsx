import { Button } from '@/components/ui/button';
import { useTheme } from './useTheme';

export default function HeaderSection() {
  const { theme } = useTheme();
  return (
    <div className={`${theme === 'dark' ? 'bg-slate-800' : 'bg-white'} border-b ${theme === 'dark' ? 'border-slate-700' : 'border-gray-200'} sticky top-0 z-10 shadow-lg`}>
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className={`text-3xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Strategy & Model Marketplace
            </h1>
            <p className={`text-lg ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'} mt-1`}>
              Discover and deploy AI-powered trading strategies from top developers
            </p>
          </div>
          <Button className="bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-black font-semibold">
            Become a Developer
          </Button>
        </div>
      </div>
    </div>
  );
}