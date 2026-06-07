import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { formatCurrency } from '@/lib/utils';

interface AssetHistoryChartProps {
  data: any[];
}

export function AssetHistoryChart({ data }: AssetHistoryChartProps) {
  if (!data || data.length === 0) return null;

  return (
    <div className="w-full h-full min-h-[300px]">
      <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4ecf98" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#4ecf98" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis 
            dataKey="date" 
            stroke="#8B92A5" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false} 
            tickFormatter={(val) => {
              // Exibe apenas o mês/ano ou ano dependendo da granularidade
              if (!val) return '';
              const parts = val.split('-');
              if (parts.length >= 2) return `${parts[1]}/${parts[0].substring(2)}`;
              return val;
            }}
          />
          <YAxis 
            stroke="#8B92A5" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false} 
            tickFormatter={(val) => `R$ ${val}`}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1A1D24', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
            itemStyle={{ color: '#4ecf98' }}
            formatter={(value: any) => [formatCurrency(value as number), 'Cotação']}
            labelStyle={{ color: '#8B92A5', marginBottom: '4px' }}
          />
          <Area 
            type="monotone" 
            dataKey="close" 
            stroke="#4ecf98" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#colorClose)" 
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
