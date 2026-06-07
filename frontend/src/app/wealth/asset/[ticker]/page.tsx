'use client';

import { useParams, useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { ChevronLeft, Wallet, TrendingUp, Layers, PieChart, Landmark } from 'lucide-react';


import { WealthSectionTitle } from '@/components/wealth/ui/WealthSectionTitle';
import { WealthKpiCard } from '@/components/wealth/ui/WealthKpiCard';
import { WealthChartCard } from '@/components/wealth/ui/WealthChartCard';
import { WealthTable } from '@/components/wealth/ui/WealthTable';
import { AssetHistoryChart } from '@/components/wealth/charts/AssetHistoryChart';

import { formatCurrency } from '@/lib/utils';

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
  market_data: {
    available: boolean;
    history: any[];
  };
  indicators: {
    available: boolean;
    indicators: Record<string, string>;
  };
  dividends: {
    items: any[];
    kpis: {
      total: number;
      last_12m: number;
      yoc: number;
    };
  };
  timeline: {
    date: string;
    title: string;
    description: string;
    type: string;
  }[];
}

export default function AssetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const ticker = params.ticker as string;

  const [data, setData] = useState<AssetDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const res = await fetch(`http://127.0.0.1:8000/api/v1/investments/asset/${ticker}`);
        if (!res.ok) throw new Error('Failed to fetch');
        const json = await res.json();
        if (mounted) {
          setData(json);
          setIsError(false);
        }
      } catch (err) {
        if (mounted) setIsError(true);
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    fetchData();
    return () => { mounted = false; };
  }, [ticker]);

  if (isLoading) {
    return (
      <>
        <div className="flex flex-col gap-6 p-6 animate-pulse">
          <div className="h-8 w-48 bg-white/5 rounded"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map(i => <div key={i} className="h-32 bg-white/5 rounded-xl"></div>)}
          </div>
          <div className="h-96 bg-white/5 rounded-xl"></div>
        </div>
      </>
    );
  }

  if (isError || !data) {
    return (
      <>
        <div className="p-6">
          <button onClick={() => router.back()} className="flex items-center text-[#8B92A5] hover:text-white transition-colors mb-6">
            <ChevronLeft size={20} className="mr-1" />
            Voltar
          </button>
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl">
            Erro ao carregar detalhes do ativo {ticker}.
          </div>
        </div>
      </>
    );
  }

  const { position, market_data, indicators, dividends, timeline } = data;

  return (
    <>
      <div className="flex flex-col gap-6 p-6">
        
        {/* Navegação Reversa */}
        <div className="flex items-center gap-2 text-sm text-[#8B92A5]">
          <button onClick={() => router.push('/wealth/patrimonio')} className="hover:text-white transition-colors">
            Wealth
          </button>
          <span>/</span>
          <button onClick={() => router.push('/wealth/patrimonio')} className="hover:text-white transition-colors">
            Patrimônio
          </button>
          <span>/</span>
          <span className="text-white font-medium">{ticker}</span>
        </div>

        {/* Bloco 1: Resumo do Ativo */}
        <div className="flex items-center justify-between">

        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <WealthKpiCard 
            title="Valor Atual" 
            value={formatCurrency(position.valor_atual)}
            icon={Wallet}
            sub={`Investido: ${formatCurrency(position.valor_investido)}`}
          />
          <WealthKpiCard 
            title="Ganho/Perda" 
            value={formatCurrency(position.ganho)}
            icon={TrendingUp}
            sub={`${((position.ganho / position.valor_investido) * 100).toFixed(2)}%`}
            subType="badge"
            subColor={position.ganho >= 0 ? "positive" : "negative"}
          />
          <WealthKpiCard 
            title="Quantidade" 
            value={position.quantidade.toString()}
            icon={Layers}
            sub={`Preço Médio: ${formatCurrency(position.preco_medio)}`}
          />
          <WealthKpiCard 
            title="Peso na Carteira" 
            value={`${position.peso.toFixed(2)}%`}
            icon={PieChart}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Bloco 2: Gráfico de Preço */}
          <div className="lg:col-span-2">
            <WealthChartCard title="Histórico de Preço">
              {market_data.available ? (
                <AssetHistoryChart data={market_data.history} />
              ) : (
                <div className="flex h-64 items-center justify-center text-[#8B92A5] bg-white/5 rounded-xl border border-white/10">
                  Cotação indisponível para este ativo.
                </div>
              )}
            </WealthChartCard>
          </div>

          {/* Bloco 3: Indicadores */}
          <div className="space-y-6">
            <WealthChartCard title="Indicadores">
              {indicators.available ? (
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(indicators.indicators).map(([key, val]) => (
                    <div key={key} className="bg-white/5 p-4 rounded-xl border border-white/10 flex flex-col items-center justify-center text-center">
                      <span className="text-[#8B92A5] text-xs font-medium uppercase tracking-wider mb-1">{key}</span>
                      <span className="text-white text-lg font-semibold">{val as string}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex h-32 items-center justify-center text-[#8B92A5] bg-white/5 rounded-xl border border-white/10">
                  Indicadores indisponíveis.
                </div>
              )}
            </WealthChartCard>

            {/* Bloco 6: Timeline */}
            <WealthChartCard title="Timeline Histórica">
              {timeline.length > 0 ? (
                <div className="space-y-4">
                  {timeline.map((event: any, idx: number) => (
                    <div key={idx} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className="w-2 h-2 rounded-full bg-[#4ecf98]"></div>
                        {idx < timeline.length - 1 && <div className="w-px h-full bg-white/10 my-1"></div>}
                      </div>
                      <div className="pb-4">
                        <div className="text-xs text-[#8B92A5] mb-1">{event.date}</div>
                        <div className="text-sm font-medium text-white">{event.title}</div>
                        <div className="text-sm text-[#8B92A5]">{event.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-[#8B92A5] text-sm text-center py-4">
                  Nenhum evento histórico encontrado.
                </div>
              )}
            </WealthChartCard>
          </div>
        </div>

        {/* Bloco 4: Proventos */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <WealthChartCard title="Proventos Recebidos" tableMode>
              <WealthTable
                data={dividends.items}
                pageSize={12}
                columns={[
                  { header: "Data", accessorKey: "data", className: "text-[#8B92A5]" },
                  { header: "Tipo", cell: (item: any) => <span className="bg-white/10 px-2 py-1 rounded text-xs">{item.tipo}</span> },
                  { header: "Valor", cell: (item: any) => formatCurrency(item.valor), align: "right", className: "text-[#4ecf98] font-medium" }
                ]}
              />
            </WealthChartCard>
          </div>
          
          <div className="flex flex-col gap-6">
            <WealthKpiCard title="Total Recebido" value={formatCurrency(dividends.kpis.total)} icon={Landmark} />
            <WealthKpiCard title="Yield on Cost (YoC)" value={`${dividends.kpis.yoc.toFixed(2)}%`} icon={TrendingUp} />
            <WealthKpiCard title="Últimos 12 Pagamentos" value={formatCurrency(dividends.kpis.last_12m)} icon={Wallet} />
          </div>
        </div>

        {/* Bloco 5: Negócios Realizados */}
        <WealthChartCard title="Negócios Realizados">
          <div className="flex h-32 items-center justify-center text-[#8B92A5] bg-white/5 rounded-xl border border-white/10 text-sm">
            Histórico de negociações será disponibilizado em futura atualização.
          </div>
        </WealthChartCard>

      </div>
    </>
  );
}
