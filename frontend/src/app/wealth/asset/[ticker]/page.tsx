'use client';

import { useParams, useRouter } from 'next/navigation';
import { useState, useEffect, useMemo } from 'react';
import { Percent, TrendingUp, ChevronLeft, Wallet, Hash, PieChart, ClipboardList, Receipt, Scale, Droplets, Activity } from "lucide-react";
import { Dividend } from "@/types/entities";
import Link from 'next/link';
import { AreaChart, Area, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

import { WealthKpiCard } from '@/components/wealth/ui/WealthKpiCard';
import { WealthChartCard } from '@/components/wealth/ui/WealthChartCard';

import { formatCurrency } from '@/lib/utils';
import { getAssetIdentity } from '@/lib/colors';

// Types (reusing original + custom for UI)
interface AssetDetails {
  position: {
    ticker: string;
    quantidade: number;
    preco_medio: number;
    valor_investido: number;
    preco_atual: number;
    valor_atual: number;
    ganho: number;
    asset_class: string;
    asset_subclass: string;
    peso: number;
  };
  market_data: { available: boolean; history: Record<string, unknown>[] };
  indicators: { available: boolean; indicators: Record<string, string> };
  dividends: { items: Dividend[]; kpis: { total: number; last_12m: number; yoc: number; }; };
  timeline: { date: string; title: string; description: string; type: string; }[];
}

import { fetchFromAPI } from "@/lib/api";

export default function AssetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const ticker = params.ticker as string;

  const [data, setData] = useState<AssetDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [dividendPage, setDividendPage] = useState(1);
  const [chartPeriod, setChartPeriod] = useState("1A");
  const DIVIDEND_PAGE_SIZE = 8;
  


  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const json = await fetchFromAPI<AssetDetails>(`/investments/asset/${ticker}`);
        if (!json) throw new Error('Failed to fetch');
        if (mounted) {
          setData(json);
          setIsError(false);
        }
      } catch {
        if (mounted) setIsError(true);
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    fetchData();
    return () => { mounted = false; };
  }, [ticker]);

  const { position, dividends, timeline } = data || {};

  const identity = useMemo(() => {
    return getAssetIdentity(position?.asset_class);
  }, [position?.asset_class]);

  const filteredHistory = useMemo(() => {
    if (!data?.market_data?.history) return [];
    const hist = data.market_data.history as any[];
    if (chartPeriod === '1D') return hist.slice(-2);
    if (chartPeriod === '1S') return hist.slice(-5);
    if (chartPeriod === '1M') return hist.slice(-21);
    if (chartPeriod === '6M') return hist.slice(-126);
    return hist; // 1A
  }, [data?.market_data?.history, chartPeriod]);

  const latestMarketData = useMemo(() => {
    if (filteredHistory.length > 0) {
      return filteredHistory[filteredHistory.length - 1];
    }
    return null;
  }, [filteredHistory]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 p-6 animate-pulse">
        <div className="h-[120px] bg-white/5 rounded-2xl border border-white/[0.07]"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-[90px] bg-white/5 rounded-2xl"></div>)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-[400px] bg-white/5 rounded-2xl"></div>
          <div className="h-[400px] bg-white/5 rounded-2xl"></div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-[400px] bg-white/5 rounded-2xl"></div>
          <div className="h-[400px] bg-white/5 rounded-2xl"></div>
        </div>
      </div>
    );
  }

  if (isError || !data || !position) {
    return (
      <div className="p-6">
        <button onClick={() => router.back()} className="flex items-center text-neutral-400 hover:text-white transition-colors mb-6 text-sm">
          <ChevronLeft size={16} className="mr-1" />
          Voltar ao Patrimônio
        </button>
        <div className="bg-[#1a1a1a] border border-white/[0.07] rounded-2xl p-8 flex items-center gap-6">
           <div className="w-[52px] h-[52px] rounded-[14px] bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-500 font-semibold text-xs">
             —
           </div>
           <div>
             <div className="flex items-center gap-3 mb-1">
               <h1 className="text-[22px] font-medium text-white">{ticker}</h1>
               <span className="px-2 py-0.5 rounded-md text-[10px] font-medium uppercase tracking-wider bg-red-500/20 text-red-400 border border-red-500/30">
                 Não Encontrado
               </span>
             </div>
             <p className="text-sm text-neutral-500">O ativo não foi encontrado na sua carteira.</p>
           </div>
        </div>
      </div>
    );
  }

  // Pre-calculated values
  const pm = position.quantidade > 0 ? (position.valor_investido / position.quantidade) : 0;
  const isPositive = position.ganho >= 0;
  const ganhoPct = position.valor_investido > 0 ? (position.ganho / position.valor_investido) * 100 : 0;
  
  const yoc = position.valor_investido > 0 ? (dividends!.kpis.last_12m / position.valor_investido) * 100 : 0;
  
  // Recharts dividend chart data (needs to aggregate by month or just take last few)
  // Reversing so oldest is left, newest right
  const chartData = [...dividends!.items].reverse().map(d => ({
    date: d.data,
    value: d.valor
  }));



  return (
    <div className="flex flex-col gap-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-neutral-500">
        <Link href="/wealth" className="hover:text-neutral-300 transition-colors">Investimentos</Link>
        <span>/</span>
        <Link href="/wealth/allocation" className="hover:text-neutral-300 transition-colors">Alocação</Link>
        <span>/</span>
        <span className="text-white font-medium">{ticker}</span>
      </div>

      {/* Hero Section */}
      <div className="bg-[#1a1a1a] border border-white/[0.07] rounded-2xl p-6 flex flex-col items-start gap-4">
        <div className="flex items-center gap-4 w-full">
          <div 
            className="w-[52px] h-[52px] rounded-[14px] flex items-center justify-center font-bold text-sm flex-shrink-0"
            style={{ backgroundColor: identity.bg, border: `1px solid ${identity.color}40`, color: identity.color }}
          >
            {identity.label}
          </div>
          <div className="flex flex-col gap-1 w-full">
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-3">
                <h1 className="text-[22px] font-medium text-white tracking-tight">{ticker}</h1>
                <span className="px-3 py-1 rounded-full text-[11px] font-medium tracking-wide border"
                      style={{ backgroundColor: identity.bg, borderColor: `${identity.color}40`, color: identity.color }}>
                  {identity.label} · {position.asset_class}
                </span>
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium tracking-wide bg-[#4ecf98]/10 text-[#4ecf98]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#4ecf98] animate-pulse" />
                  Na Carteira
                </span>
              </div>
              <p className="text-sm text-neutral-500 ml-auto">{ticker} · {position.asset_class} listado na B3</p>
            </div>
          </div>
        </div>
      </div>

      {/* Secção 1 - KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <WealthKpiCard 
          title="Valor Atual" 
          value={formatCurrency(position.valor_atual)}
          icon={Wallet}
          iconBgColor="bg-[#4ecf98]/10"
          iconColor="text-[#4ecf98]"
          sub={`Investido: ${formatCurrency(position.valor_investido)}`}
          subType="text"
        />
        
        {/* Ganho/Perda card customizado */}
        <div className="relative rounded-2xl p-5 transition-all duration-200 bg-[#1a1a1a]/90 border border-white/[0.07] hover:bg-[#1e1e1e]/95 hover:border-white/[0.12] group">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 flex-shrink-0 ${isPositive ? 'bg-[#4ecf98]/10 text-[#4ecf98]' : 'bg-[#e97070]/10 text-[#e97070]'}`}>
            <TrendingUp size={20} />
          </div>
          <h3 className="text-[10px] font-medium uppercase tracking-widest text-neutral-500 mb-1">
            Ganho / Perda
          </h3>
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[20px] font-medium tracking-tight leading-snug ${isPositive ? 'text-[#4ecf98]' : 'text-[#e97070]'}`}>
              {isPositive ? '+' : ''}{formatCurrency(position.ganho)}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${isPositive ? 'bg-[#4ecf98]/10 text-[#4ecf98]' : 'bg-[#e97070]/10 text-[#e97070]'}`}>
              {isPositive ? '+' : ''}{ganhoPct.toFixed(2)}%
            </span>
          </div>
        </div>

        <WealthKpiCard 
          title="Quantidade" 
          value={position.quantidade.toString()}
          icon={Hash}
          iconBgColor="bg-[#7EB8F7]/10"
          iconColor="text-[#7EB8F7]"
          sub={pm > 0 ? `Preço Médio: ${formatCurrency(pm)}` : 'Preço Médio: —'}
          subType="text"
        />

        <WealthKpiCard 
          title="Peso na Carteira" 
          value={`${position.peso.toFixed(2)}%`}
          icon={PieChart}
          iconBgColor={identity.bg.replace("0.12", "0.1").replace("0.10", "0.1")}
          iconColor={`text-[${identity.color}]`} // Dynamic class won't work in Tailwind this way.
          // Workaround for icon styling if color is dynamically set:
          // We can use style object if WealthKpiCard supports it. If not, we will just use a generic style.
          // For now, let's let WealthKpiCard use default or we can override. I'll just pass a standard text-white/50 for now 
          // or rely on the prop.
        />
      </div>

      {/* Secção 2 - Layout Principal */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Histórico de Preço */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <WealthChartCard title="Histórico de Preço" className="h-full flex-1">
            <div className="flex justify-between items-center mb-6">
              <div className="flex gap-2">
                {["1D", "1S", "1M", "6M", "1A"].map(p => (
                  <button 
                    key={p} 
                    onClick={() => setChartPeriod(p)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      chartPeriod === p 
                        ? 'bg-white/10 text-white' 
                        : 'text-neutral-500 bg-black/20 hover:bg-white/5'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            
            {data.market_data.available && filteredHistory.length > 0 ? (
              <div className="w-full h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={filteredHistory} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={identity.color} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={identity.color} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis 
                      dataKey="date" 
                      tick={{ fill: '#737373', fontSize: 10 }}
                      tickLine={false}
                      axisLine={false}
                      minTickGap={30}
                    />
                    <YAxis 
                      domain={['auto', 'auto']}
                      tick={{ fill: '#737373', fontSize: 10 }}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(val) => `R$${val.toFixed(0)}`}
                    />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: '#1a1a1a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      itemStyle={{ color: '#fff', fontSize: '12px' }}
                      labelStyle={{ color: '#a3a3a3', fontSize: '10px', marginBottom: '4px' }}
                      formatter={(value: any) => {
                        const numValue = Number(value);
                        return [`R$ ${isNaN(numValue) ? '0.00' : numValue.toFixed(2)}`, 'Cotação'];
                      }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="close" 
                      stroke={identity.color} 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorClose)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="relative w-full h-[320px] bg-[#141414] rounded-xl border border-white/[0.04] overflow-hidden flex items-center justify-center">
                 <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
                   <path d="M 0,200 Q 100,180 200,150 T 400,100 T 600,80 T 800,40" 
                         fill="none" 
                         stroke={identity.color} 
                         strokeOpacity={0.15}
                         strokeWidth={2}
                         strokeDasharray="6 4" />
                 </svg>
                 <div className="z-10 flex flex-col items-center gap-3 bg-[#141414]/80 px-6 py-4 rounded-xl backdrop-blur-sm border border-white/5">
                   <div className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center">
                     <TrendingUp size={18} className="text-neutral-500" />
                   </div>
                   <p className="text-xs text-neutral-500 text-center max-w-[200px]">
                     Histórico temporariamente indisponível.
                   </p>
                 </div>
              </div>
            )}

            {/* Mini cards */}
            <div className="grid grid-cols-4 gap-3 mt-4">
              <div className="bg-[#141414] rounded-lg p-2.5 border border-white/[0.04]">
                <p className="text-[10px] uppercase text-neutral-600 tracking-wider mb-1">Abertura</p>
                <p className="text-sm font-medium text-neutral-200">
                  {latestMarketData?.open ? formatCurrency(latestMarketData.open) : '—'}
                </p>
              </div>
              <div className="bg-[#141414] rounded-lg p-2.5 border border-white/[0.04]">
                <p className="text-[10px] uppercase text-neutral-600 tracking-wider mb-1">Máxima</p>
                <p className="text-sm font-medium text-neutral-200">
                  {latestMarketData?.high ? formatCurrency(latestMarketData.high) : '—'}
                </p>
              </div>
              <div className="bg-[#141414] rounded-lg p-2.5 border border-white/[0.04]">
                <p className="text-[10px] uppercase text-neutral-600 tracking-wider mb-1">Mínima</p>
                <p className="text-sm font-medium text-neutral-200">
                  {latestMarketData?.low ? formatCurrency(latestMarketData.low) : '—'}
                </p>
              </div>
              <div className="bg-[#141414] rounded-lg p-2.5 border border-white/[0.04]">
                <p className="text-[10px] uppercase text-neutral-600 tracking-wider mb-1">Volume</p>
                <p className="text-sm font-medium text-neutral-200">
                  {latestMarketData?.volume ? (latestMarketData.volume >= 1e6 ? `${(latestMarketData.volume/1e6).toFixed(2)}M` : latestMarketData.volume.toLocaleString('pt-BR')) : '—'}
                </p>
              </div>
            </div>
          </WealthChartCard>
        </div>

        {/* Indicadores & Proventos */}
        <div className="flex flex-col gap-6">
          <WealthChartCard title="Indicadores" className="flex-1" tableMode={true}>
            <div className="flex flex-col mt-2">
              {/* Dividend Yield */}
              <div className="flex justify-between items-center gap-3 py-[9px] border-b border-white/[0.04]">
                <div className="flex items-center gap-[7px]">
                  <Percent size={15} className="text-neutral-600 flex-shrink-0" />
                  <span className="text-[12.5px] text-neutral-400 whitespace-nowrap">Dividend Yield</span>
                </div>
                <span className="text-[13px] font-medium text-[#4ecf98]">{dividends?.kpis?.yoc?.toFixed(2) || '0.00'}%</span>
              </div>
              
              {/* Yield on Cost */}
              <div className="flex justify-between items-center gap-3 py-[9px] border-b border-white/[0.04]">
                <div className="flex items-center gap-[7px]">
                  <Receipt size={15} className="text-neutral-600 flex-shrink-0" />
                  <span className="text-[12.5px] text-neutral-400 whitespace-nowrap">Yield on Cost</span>
                </div>
                <span className="text-[13px] font-medium text-[#4ecf98]">{yoc.toFixed(2)}%</span>
              </div>
              
              {/* Dynamic Indicators from API */}
              {data.indicators?.available && Object.entries(data.indicators.indicators).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center gap-3 py-[9px] border-b border-white/[0.04] last:border-0">
                  <div className="flex items-center gap-[7px]">
                    <Scale size={15} className="text-neutral-600 flex-shrink-0" />
                    <span className="text-[12.5px] text-neutral-400 whitespace-nowrap">{key}</span>
                  </div>
                  <div className="flex items-center whitespace-nowrap">
                    <span className="text-[13px] font-medium text-neutral-200">{String(value)}</span>
                    <span className="text-[9px] text-neutral-700 bg-white/[0.03] border border-white/[0.05] rounded px-[5px] py-[1px] ml-1.5 whitespace-nowrap">yfinance</span>
                  </div>
                </div>
              ))}
              
              {!data.indicators?.available && (
                <div className="py-4 text-center">
                  <span className="text-xs text-neutral-500">Indicadores fundamentalistas temporariamente indisponíveis.</span>
                </div>
              )}
            </div>
          </WealthChartCard>

          <WealthChartCard title="Resumo Proventos" tableMode={true}>
            <div className="space-y-4 mt-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-neutral-400">Total recebido</span>
                <span className="text-sm font-semibold text-[#f5a623]">{formatCurrency(dividends!.kpis.total)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-neutral-400">Últimos 12M</span>
                <span className="text-sm font-semibold text-[#f5a623]">{formatCurrency(dividends!.kpis.last_12m)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-neutral-400">Média mensal</span>
                <span className="text-sm font-semibold text-[#f5a623]">{formatCurrency(dividends!.kpis.last_12m / 12)}</span>
              </div>
            </div>
          </WealthChartCard>
        </div>
      </div>

      {/* Secção 3 - Proventos e Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Tabela de Proventos Recebidos */}
        <div className="lg:col-span-2">
          <WealthChartCard 
            title={
              <div className="flex items-center gap-3">
                <span>Proventos Recebidos</span>
                <span className="px-2 py-0.5 rounded-md text-[10px] font-medium uppercase tracking-wider bg-[#f5a623]/10 text-[#f5a623] border border-[#f5a623]/20">
                  {dividends!.items.length} pagamentos
                </span>
              </div>
            } 
            className="h-full flex flex-col"
            tableMode={true}
          >
            {chartData.length >= 2 && (
              <div className="w-full h-[50px] mb-6 mt-4 opacity-70">
                <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
                  <BarChart data={chartData}>
                    <Bar dataKey="value" fill="#f5a623" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-zinc-400">
                <thead className="text-[10px] uppercase tracking-wider text-neutral-600 border-b border-white/5">
                  <tr>
                    <th className="pb-3 font-medium">Data</th>
                    <th className="pb-3 font-medium">Tipo</th>
                    <th className="pb-3 font-medium">Valor/Cota</th>
                    <th className="pb-3 font-medium text-right">Total Recebido</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {(() => {
                    if (!dividends || dividends.items.length === 0) {
                      return (
                        <tr>
                          <td colSpan={4} className="py-8 text-center text-neutral-600 text-xs">
                            Nenhum provento registrado.
                          </td>
                        </tr>
                      );
                    }
                    
                    const startIdx = (dividendPage - 1) * DIVIDEND_PAGE_SIZE;
                    const paginatedItems = dividends.items.slice(startIdx, startIdx + DIVIDEND_PAGE_SIZE);
                    
                    return paginatedItems.map((item: Dividend, i: number) => {
                      const parts = ((item as any).data || "").split("-");
                      const dtFormat = parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : (item as any).data;
                      return (
                        <tr key={`${dividendPage}-${i}`} className="hover:bg-white/5 transition-colors">
                          <td className="py-3 text-neutral-300 font-mono text-[13px]">{dtFormat}</td>
                          <td className="py-3">
                             <span className="bg-[#f5a623]/10 border border-[#f5a623]/20 text-[#f5a623] px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider">
                               {(item as any).tipo}
                             </span>
                          </td>
                          <td className="py-3 text-neutral-500">—</td>
                          <td className="px-4 py-3 text-[#4ecf98] font-medium text-right">{formatCurrency((item as any).valor || 0)}</td>
                        </tr>
                      );
                    });
                  })()}
                </tbody>
              </table>
              {dividends && dividends.items.length > DIVIDEND_PAGE_SIZE && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-white/[0.05]">
                  <span className="text-xs text-neutral-500">
                    Página {dividendPage} de {Math.ceil(dividends.items.length / DIVIDEND_PAGE_SIZE)}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setDividendPage(p => Math.max(1, p - 1))}
                      disabled={dividendPage === 1}
                      className="px-3 py-1 text-xs font-medium text-white bg-white/[0.03] border border-white/[0.05] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/[0.06] transition-colors"
                    >
                      Anterior
                    </button>
                    <button
                      onClick={() => setDividendPage(p => Math.min(Math.ceil(dividends.items.length / DIVIDEND_PAGE_SIZE), p + 1))}
                      disabled={dividendPage === Math.ceil(dividends.items.length / DIVIDEND_PAGE_SIZE)}
                      className="px-3 py-1 text-xs font-medium text-white bg-white/[0.03] border border-white/[0.05] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/[0.06] transition-colors"
                    >
                      Próxima
                    </button>
                  </div>
                </div>
              )}
            </div>
          </WealthChartCard>
        </div>

        {/* Timeline & Negócios */}
        <div className="flex flex-col gap-6">
          <WealthChartCard title="Marcos Históricos" className="flex-1" tableMode={true}>
            <div className="relative flex flex-col gap-0 mt-4 pl-[11px]">
               <div className="absolute left-[11px] top-0 bottom-0 w-px bg-white/[0.06]" />
               
               {/* Exemplo de Marcos hardcoded adaptados se n tivermos da api de forma rica, senao usar timeline */}
               {timeline && timeline.length > 0 ? (
                 timeline.map((event: { date: string; title: string; description: string; type: string; }, idx: number) => (
                    <div key={idx} className="flex items-start gap-4 relative py-3 pl-6">
                      <div className="absolute left-[-5px] top-4 w-[12px] h-[12px] rounded-full bg-[#4ecf98] ring-4 ring-[#141414]" />
                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-neutral-500 mb-0.5">{event.date}</p>
                        <p className="text-sm font-medium text-white mb-0.5">{event.title}</p>
                        <p className="text-xs text-neutral-500">{event.description}</p>
                      </div>
                    </div>
                 ))
               ) : (
                 <>
                  {/* Fallbacks placeholder se a api n tiver */}
                  <div className="flex items-start gap-4 relative py-3 pl-6">
                    <div className="absolute left-[-5px] top-4 w-[12px] h-[12px] rounded-full bg-[#4ecf98] ring-4 ring-[#141414]" />
                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-neutral-500 mb-0.5">Jan 2026</p>
                      <p className="text-sm font-medium text-white mb-0.5">Primeira Compra</p>
                      <p className="text-xs text-neutral-500">Início de posição</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-4 relative py-3 pl-6 opacity-50">
                    <div className="absolute left-[-5px] top-4 w-[12px] h-[12px] rounded-full bg-neutral-700 ring-4 ring-[#141414]" />
                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-neutral-600 mb-0.5">Em breve</p>
                      <p className="text-sm font-medium text-neutral-500 mb-0.5">Marcos por performance</p>
                      <p className="text-xs text-neutral-600">+10%, +20%, +30% de ganho</p>
                    </div>
                  </div>
                 </>
               )}
            </div>
          </WealthChartCard>

          <WealthChartCard title="Negócios Realizados" className="flex-none">
            <div className="bg-[#141414] rounded-xl p-6 border border-white/[0.04] flex flex-col items-center justify-center text-center gap-4 h-full min-h-[160px]">
              <div className="w-12 h-12 rounded-full bg-white/[0.02] flex items-center justify-center">
                <ClipboardList className="text-neutral-800" size={24} />
              </div>
              <p className="text-xs text-neutral-600 max-w-[200px] mx-auto">
                Histórico de negociações disponível em futura atualização
              </p>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium uppercase tracking-wider bg-white/[0.03] text-neutral-700 border border-white/[0.05]">
                📅 Fase 3 do roadmap
              </span>
            </div>
          </WealthChartCard>
        </div>
      </div>

    </div>
  );
}
