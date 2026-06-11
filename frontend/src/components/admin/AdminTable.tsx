import React from "react";
import { Loader2 } from "lucide-react";

export interface ColumnDef<T> {
  key: string;
  header: string;
  renderCell?: (row: T) => React.ReactNode;
}

interface AdminTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  isLoading: boolean;
  emptyMessage?: string;
  keyExtractor: (row: T) => string;
}

export function AdminTable<T>({
  columns,
  data,
  isLoading,
  emptyMessage = "Nenhum registro encontrado.",
  keyExtractor,
}: AdminTableProps<T>) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-900/50">
      <div className="relative w-full overflow-auto">
        <table className="w-full caption-bottom text-sm">
          <thead className="[&_tr]:border-b border-slate-800">
            <tr className="border-b transition-colors hover:bg-slate-800/50">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="h-12 px-4 text-left align-middle font-medium text-zinc-400"
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="[&_tr:last-child]:border-0">
            {isLoading ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="h-24 text-center align-middle"
                >
                  <div className="flex items-center justify-center space-x-2 text-zinc-400">
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Carregando dados...</span>
                  </div>
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="h-24 text-center align-middle text-zinc-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row) => (
                <tr
                  key={keyExtractor(row)}
                  className="border-b border-slate-800 transition-colors hover:bg-slate-800/50 data-[state=selected]:bg-slate-800"
                >
                  {columns.map((col) => (
                    <td key={col.key} className="p-4 align-middle text-zinc-300">
                      {col.renderCell
                        ? col.renderCell(row)
                        : (row as Record<string, unknown>)[col.key] as React.ReactNode}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
