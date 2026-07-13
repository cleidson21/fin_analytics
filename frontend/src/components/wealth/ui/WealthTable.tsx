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
    <div className={cn("w-full overflow-x-auto rounded-xl border border-white/[0.05]", className)}>
      <table className="w-full text-left">
        <thead>
          <tr>
            {columns.map((col, i) => (
              <th 
                key={i} 
                className={cn(
                  "px-4 pb-2 pt-3 text-[10px] tracking-[0.08em] uppercase text-neutral-500 font-normal border-b border-white/[0.05]",
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
                  <div className="w-5 h-5 border-2 border-white/20 border-t-white/80 rounded-full animate-spin" />
                  <span className="text-[13px] text-neutral-400">Carregando dados...</span>
                </div>
              </td>
            </tr>
          ) : displayData.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-[13px] text-neutral-500">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            displayData.map((row, rowIndex) => (
              <tr 
                key={rowIndex} 
                className={cn(
                  "border-b border-white/[0.03] last:border-0 hover:bg-white/[0.015] transition-colors cursor-default",
                  typeof rowClassName === "function" ? rowClassName(row, rowIndex) : rowClassName
                )}
              >
                {columns.map((col, colIndex) => (
                  <td 
                    key={colIndex} 
                    className={cn(
                      "px-4 py-3 text-[13px] text-neutral-400",
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
        <div className="flex items-center justify-between px-4 py-3 border-t border-white/[0.05]">
          <span className="text-xs text-neutral-500">
            Página {currentPage} de {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-xs font-medium text-white bg-white/[0.03] border border-white/[0.05] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/[0.06] transition-colors"
            >
              Anterior
            </button>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-xs font-medium text-white bg-white/[0.03] border border-white/[0.05] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/[0.06] transition-colors"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
