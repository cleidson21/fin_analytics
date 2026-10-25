import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { formatCurrency } from '@/lib/utils';

interface AssetHistoryChartProps {
  data: Record<string, unknown>[];
}

export function AssetHistoryChart({ data }: AssetHistoryChartProps) {
  if (!data || data.length === 0) return null;

  return (
    <div className="w-full h-full min-h-[300px]">
      <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
          <XAxis 
            dataKey="date" 
            stroke="var(--chart-axis)"
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
            stroke="var(--chart-axis)"
            fontSize={12} 
            tickLine={false} 
            axisLine={false} 
            tickFormatter={(val) => `R$ ${val}`}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: 'var(--popover)', border: '1px solid var(--chart-grid)', borderRadius: '8px', color: 'var(--foreground)' }}
            itemStyle={{ color: 'var(--chart-1)' }}
            formatter={(value: unknown) => [formatCurrency(Number(value)), 'Cotação']}
            labelStyle={{ color: 'var(--chart-axis)', marginBottom: '4px' }}
          />
          <Area 
            type="monotone" 
            dataKey="close" 
            stroke="var(--chart-1)"
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
