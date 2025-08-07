import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts';
import { useTheme } from 'next-themes';

interface ChartData {
  name: string;
  value: number;
  color: string;
}

const data: ChartData[] = [
  { name: 'Completed', value: 41, color: '#ca8a04' }, // green-600
  { name: 'In Progress', value: 25, color: '#a16207' }, // green-700  
  { name: 'Pending', value: 34, color: '#e5e7eb' }, // gray-200 with stripes pattern
];

const RADIAN = Math.PI / 180;

const CustomLegend = ({ payload }: any) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  return (
    <div className="flex justify-center gap-6 mt-8">
      {payload?.map((entry: any, index: number) => (
        <div key={index} className="flex items-center gap-2">
          <div 
            className={`w-3 h-3 rounded-full ${
              entry.value === 'Pending' 
                ? 'bg-gray-200 bg-[repeating-linear-gradient(45deg,transparent,transparent_2px,#6b7280_2px,#6b7280_4px)]' 
                : ''
            }`}
            style={entry.value !== 'Pending' ? { backgroundColor: entry.color } : {}}
          />
          <span className="text-sm text-gray-600 font-medium">{entry.value}</span>
        </div>
      ))}
    </div>
  );
};

const renderCustomizedLabel = ({
  cx, cy, midAngle, innerRadius, outerRadius, percent
}: any) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return null; // We'll show the percentage in the center instead
};

export default function TicketPie() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const completedPercentage = data.find(item => item.name === 'Completed')?.value || 0;

  return (
    <div>
      <div className="relative">
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <defs>
              <pattern 
                id="pendingPattern" 
                patternUnits="userSpaceOnUse" 
                width="8" 
                height="8"
                patternTransform="rotate(45)"
              >
                <rect width="8" height="8" fill={isDark ? "#374151" : "#e5e7eb"} />
                <rect width="4" height="8" fill={isDark ? "#9ca3af" : "#6b7280"} />
              </pattern>
            </defs>

            <Pie
              data={data}
              cx="50%"
              cy="70%"
              labelLine={false}
              label={renderCustomizedLabel}
              outerRadius={100}
              innerRadius={65}
              dataKey="value"
              startAngle={180}
              endAngle={0}
            >
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.name === 'Pending' ? 'url(#pendingPattern)' : entry.color}
                  stroke={entry.name === 'Pending' ? '#6b7280' : entry.color}
                  strokeWidth={entry.name === 'Pending' ? 1 : 0}
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Center percentage */}
        <div className="absolute top-[75%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center">
          <div className="text-4xl font-bold text-gray-900 dark:text-white leading-none">
            {completedPercentage}%
          </div>
          <div className="text-sm text-gray-600 dark:text-white mt-1">
            Project Ended
          </div>
        </div>
      </div>

      {/* Legend */}
      <CustomLegend payload={[
        { value: 'Completed', color: '#ca8a04' },
        { value: 'In Progress', color: '#a16207' },
        { value: 'Pending', color: isDark ? '#374151' : '#e5e7eb' }
      ]} />
    </div>
  );
}
