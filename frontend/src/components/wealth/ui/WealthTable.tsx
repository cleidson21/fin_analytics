import { cn } from "@/lib/utils";
import { ReactNode, useState } from "react";

interface Column<T> {
  header: string;
  accessorKey?: keyof T;
  cell?: (item: T) => ReactNode;
  align?: "left" | "center" | "right";
  className?: string | ((item: T) => string);
  headerClassName?: string;
}

interface WealthTableProps<T> {
  data: T[];
  columns: Column<T>[];
  className?: string;
  emptyMessage?: string;
  pageSize?: number;
  rowClassName?: string | ((item: T, index: number) => string);
  isLoading?: boolean;
}

export function WealthTable<T>({ data, columns, className, emptyMessage = "Nenhum dado encontrado.", pageSize, rowClassName, isLoading }: WealthTableProps<T>) {
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = pageSize ? Math.ceil(data.length / pageSize) : 1;
  const displayData = pageSize ? data.slice((currentPage - 1) * pageSize, currentPage * pageSize) : data;
  return (
    <div className={cn("w-full overflow-x-auto rounded-xl border border-border", className)}>
      <table className="w-full text-left">
        <thead>
          <tr>
            {columns.map((col, i) => (
              <th 
                key={i} 
                className={cn(
                  "border-b border-border px-2 pb-2 pt-3 text-[10px] font-normal uppercase tracking-[0.08em] text-muted-foreground sm:px-3",
                  col.align === "right" && "text-right",
                  col.align === "center" && "text-center",
                  typeof col.className === "string" ? col.className : undefined,
                  col.headerClassName
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center">
                <div className="flex flex-col items-center justify-center space-y-3 opacity-50">
                  <div className="w-5 h-5 border-2 border-border border-t-white/80 rounded-full animate-spin" />
                  <span className="text-[13px] text-muted-foreground">Carregando dados...</span>
                </div>
              </td>
            </tr>
          ) : displayData.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-[13px] text-muted-foreground">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            displayData.map((row, rowIndex) => (
              <tr 
                key={rowIndex} 
                className={cn(
                  "border-b border-border last:border-0 hover:bg-muted/25 transition-colors cursor-default",
                  typeof rowClassName === "function" ? rowClassName(row, rowIndex) : rowClassName
                )}
              >
                {columns.map((col, colIndex) => (
                  <td 
                    key={colIndex} 
                    className={cn(
                      "whitespace-nowrap px-2 py-3 text-[13px] text-muted-foreground sm:px-3",
                      col.align === "right" && "text-right",
                      col.align === "center" && "text-center",
                      typeof col.className === "function" ? col.className(row) : col.className
                    )}
                  >
                    {col.cell 
                      ? col.cell(row) 
                      : col.accessorKey 
                        ? (row[col.accessorKey] as ReactNode) 
                        : null}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-border">
          <span className="text-xs text-muted-foreground">
            Página {currentPage} de {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-xs font-medium text-foreground bg-muted/35 border border-border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-muted/50 transition-colors"
            >
              Anterior
            </button>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-xs font-medium text-foreground bg-muted/35 border border-border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-muted/50 transition-colors"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
