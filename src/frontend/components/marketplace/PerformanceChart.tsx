'use client';

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { useTheme } from 'next-themes';

// Mock performance data
const performanceData = [
  { date: '2023-01', value: 0, benchmark: 0 },
  { date: '2023-02', value: 8.5, benchmark: 3.2 },
  { date: '2023-03', value: 15.2, benchmark: 5.8 },
  { date: '2023-04', value: 12.8, benchmark: 7.1 },
  { date: '2023-05', value: 22.6, benchmark: 9.5 },
  { date: '2023-06', value: 35.4, benchmark: 12.8 },
  { date: '2023-07', value: 42.1, benchmark: 15.2 },
  { date: '2023-08', value: 38.9, benchmark: 18.6 },
  { date: '2023-09', value: 55.7, benchmark: 22.1 },
  { date: '2023-10', value: 68.3, benchmark: 24.5 },
  { date: '2023-11', value: 82.6, benchmark: 27.8 },
  { date: '2023-12', value: 95.4, benchmark: 31.2 },
  { date: '2024-01', value: 142.5, benchmark: 35.6 }
];

const drawdownData = [
  { date: '2023-01', drawdown: 0 },
  { date: '2023-02', drawdown: -2.1 },
  { date: '2023-03', drawdown: -1.5 },
  { date: '2023-04', drawdown: -4.2 },
  { date: '2023-05', drawdown: -0.8 },
  { date: '2023-06', drawdown: -0.3 },
  { date: '2023-07', drawdown: -2.6 },
  { date: '2023-08', drawdown: -5.8 },
  { date: '2023-09', drawdown: -1.2 },
  { date: '2023-10', drawdown: -0.5 },
  { date: '2023-11', drawdown: -0.9 },
  { date: '2023-12', drawdown: -3.1 },
  { date: '2024-01', drawdown: -8.5 }
];

const PerformanceChart: React.FC = () => {
  const { theme } = useTheme();

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className={`p-3 rounded-lg shadow-lg border ${
          theme === 'dark' 
            ? 'bg-gray-800 border-gray-700 text-white' 
            : 'bg-white border-gray-200 text-gray-900'
        }`}>
          <p className="font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}: {entry.value.toFixed(1)}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Performance vs Benchmark */}
      <div>
        <h4 className={`text-lg font-semibold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
          Performance vs S&P 500 Benchmark
        </h4>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={performanceData}>
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke={theme === 'dark' ? '#374151' : '#e5e7eb'} 
              />
              <XAxis 
                dataKey="date" 
                stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
                fontSize={12}
              />
              <YAxis 
                stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
                fontSize={12}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#10b981"
                strokeWidth={3}
                dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
                name="Strategy"
              />
              <Line
                type="monotone"
                dataKey="benchmark"
                stroke="#6b7280"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: '#6b7280', strokeWidth: 2, r: 3 }}
                name="S&P 500"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-6 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-green-500"></div>
            <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Strategy Performance
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-gray-500" style={{backgroundImage: 'linear-gradient(to right, #6b7280 50%, transparent 50%)', backgroundSize: '8px 1px'}}></div>
            <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              S&P 500 Benchmark
            </span>
          </div>
        </div>
      </div>

      {/* Drawdown Chart */}
      <div>
        <h4 className={`text-lg font-semibold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
          Drawdown Analysis
        </h4>
        <div className="h-60">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={drawdownData}>
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke={theme === 'dark' ? '#374151' : '#e5e7eb'} 
              />
              <XAxis 
                dataKey="date" 
                stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
                fontSize={12}
              />
              <YAxis 
                stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
                fontSize={12}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="drawdown"
                stroke="#ef4444"
                fill="#ef444420"
                strokeWidth={2}
                name="Drawdown"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-2 mt-4">
          <div className="w-4 h-3 bg-red-500 bg-opacity-20 border border-red-500"></div>
          <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            Maximum Drawdown: -8.5%
          </span>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="text-center p-4 rounded-lg bg-green-50 dark:bg-green-900/20">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400 mb-1">
            2.3
          </div>
          <div className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            Sharpe Ratio
          </div>
        </div>
        
        <div className="text-center p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-1">
            2.1
          </div>
          <div className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            Profit Factor
          </div>
        </div>
        
        <div className="text-center p-4 rounded-lg bg-purple-50 dark:bg-purple-900/20">
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-1">
            67.2%
          </div>
          <div className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            Win Rate
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceChart;