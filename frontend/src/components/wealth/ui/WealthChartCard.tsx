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
        "flex flex-col rounded-2xl border border-border bg-card p-5 text-card-foreground shadow-sm transition-colors duration-200 hover:bg-accent/25 motion-reduce:transition-none",
        flexMode ? "overflow-visible" : "",
        className
      )}
    >
      {/* Header */}
      <div className="flex justify-between items-center mb-5 flex-shrink-0">
        <h3 className="text-sm font-medium text-foreground/90">
          {title}
        </h3>
        {action && <div>{action}</div>}
      </div>

      {/* Content */}
      {tableMode ? (
        // Modo tabela: sem altura mínima fixa, o card cresce com o conteúdo
        <div className="w-full">
          {isLoading ? (
            <div className="h-32 w-full animate-pulse rounded-xl bg-muted motion-reduce:animate-none" />
          ) : isError ? (
            <div className="flex flex-col items-center justify-center gap-3 py-10 text-muted-foreground">
              <AlertCircle size={28} style={{ opacity: 0.5 }} />
              <p className="text-sm">Dados indisponíveis no momento.</p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="flex items-center gap-2 rounded-lg bg-muted px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring"
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
            <div className="h-full min-h-[200px] w-full animate-pulse rounded-xl bg-muted motion-reduce:animate-none" />
          ) : isError ? (
            <div className="flex flex-col items-center justify-center gap-3 py-10 text-muted-foreground">
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
              <div className="h-full w-full animate-pulse rounded-xl bg-muted motion-reduce:animate-none" />
            </div>
          ) : isError ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-muted-foreground">
              <AlertCircle size={28} style={{ opacity: 0.5 }} />
              <p className="text-sm">Dados indisponíveis no momento.</p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="flex items-center gap-2 rounded-lg bg-muted px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring"
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
