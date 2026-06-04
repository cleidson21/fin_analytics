import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface Column<T> {
  header: string;
  accessorKey?: keyof T;
  cell?: (item: T) => ReactNode;
  align?: "left" | "center" | "right";
  className?: string | ((item: T) => string);
}

interface WealthTableProps<T> {
  data: T[];
  columns: Column<T>[];
  className?: string;
  emptyMessage?: string;
}

export function WealthTable<T>({ data, columns, className, emptyMessage = "Nenhum dado encontrado." }: WealthTableProps<T>) {
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
                  col.className
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-[13px] text-neutral-500">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr 
                key={rowIndex} 
                className="border-b border-white/[0.03] last:border-0 hover:bg-white/[0.015] transition-colors cursor-default"
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
    </div>
  );
}
