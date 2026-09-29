import { cn } from "@/lib/utils";
import { AlertCircle, RefreshCw } from "lucide-react";
import { ReactNode } from "react";

interface WealthChartCardProps {
  title: string | React.ReactNode;
  children: ReactNode;
  isLoading?: boolean;
  isError?: boolean;
  onRetry?: () => void;
  className?: string;
  action?: ReactNode;
  /** Modo tabela: desativa altura mínima e posicionamento absoluto do conteúdo */
  tableMode?: boolean;
  /** Modo flex: renderiza filhos em flex (sem absolute), para painéis laterais dinâmicos */
  flexMode?: boolean;
}

export function WealthChartCard({
  title,
  children,
  isLoading,
  isError,
  onRetry,
  className,
  action,
  tableMode = false,
  flexMode = false,
}: WealthChartCardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl p-5 flex flex-col transition-all duration-200",
        flexMode ? "overflow-visible" : "",
        className
      )}
      style={{
        background: "rgba(26,26,26,0.9)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      {/* Header */}
      <div className="flex justify-between items-center mb-5 flex-shrink-0">
        <h3
          className="text-sm font-medium"
          style={{ color: "#d1d5db" }}
        >
          {title}
        </h3>
        {action && <div>{action}</div>}
      </div>

      {/* Content */}
      {tableMode ? (
        // Modo tabela: sem altura mínima fixa, o card cresce com o conteúdo
        <div className="w-full">
          {isLoading ? (
            <div className="h-32 w-full rounded-xl animate-pulse" style={{ background: "rgba(255,255,255,0.03)" }} />
          ) : isError ? (
            <div className="flex flex-col items-center justify-center gap-3 py-10" style={{ color: "#6b7280" }}>
              <AlertCircle size={28} style={{ opacity: 0.5 }} />
              <p className="text-sm">Dados indisponíveis no momento.</p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg transition-colors"
                  style={{ background: "rgba(255,255,255,0.05)", color: "#9ca3af" }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.09)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
                >
                  <RefreshCw size={12} />
                  Tentar novamente
                </button>
              )}
            </div>
          ) : (
            <div className="animate-in fade-in duration-300">{children}</div>
          )}
        </div>
      ) : flexMode ? (
        // Modo flex: filho controla seu próprio layout, sem absolute, overflow visível para popups
        <div className="flex-1 w-full flex flex-col overflow-visible" style={{ minHeight: 200 }}>
          {isLoading ? (
            <div className="w-full h-full rounded-xl animate-pulse" style={{ background: "rgba(255,255,255,0.03)", minHeight: 200 }} />
          ) : isError ? (
            <div className="flex flex-col items-center justify-center gap-3 py-10" style={{ color: "#6b7280" }}>
              <AlertCircle size={28} style={{ opacity: 0.5 }} />
              <p className="text-sm">Dados indisponíveis no momento.</p>
            </div>
          ) : (
            <div className="flex-1 flex flex-col overflow-visible animate-in fade-in duration-300">{children}</div>
          )}
        </div>
      ) : (
        // Modo gráfico: conteúdo posicionado de forma absoluta para Recharts funcionar
        <div className="flex-1 relative min-h-[200px] w-full h-full flex flex-col">
          {isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-full h-full rounded-xl animate-pulse" style={{ background: "rgba(255,255,255,0.03)" }} />
            </div>
          ) : isError ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3" style={{ color: "#6b7280" }}>
              <AlertCircle size={28} style={{ opacity: 0.5 }} />
              <p className="text-sm">Dados indisponíveis no momento.</p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg transition-colors"
                  style={{ background: "rgba(255,255,255,0.05)", color: "#9ca3af" }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.09)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
                >
                  <RefreshCw size={12} />
                  Tentar novamente
                </button>
              )}
            </div>
          ) : (
            <div className="absolute inset-0 w-full h-full animate-in fade-in duration-300">{children}</div>
          )}
        </div>
      )}
    </div>
  );
}
