"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "transactions", label: "Transações" },
  { id: "positions",    label: "Posições" },
  { id: "dividends",   label: "Dividendos" },
  { id: "categories",  label: "Categorias" },
];

export function DataTabsNav() {
  const searchParams = useSearchParams();
  // Se não houver tab na URL, transações é o padrão
  const currentTab = searchParams.get("tab") || "transactions";

  return (
    <div className="flex w-full overflow-x-auto border-b border-slate-800">
      <nav className="flex gap-6 px-1" aria-label="Tabs">
        {TABS.map((tab) => {
          const isActive = currentTab === tab.id;
          return (
            <Link
              key={tab.id}
              href={`/governance/data?tab=${tab.id}`}
              className={cn(
                "whitespace-nowrap border-b-2 py-3 px-1 text-sm font-medium transition-colors",
                isActive
                  ? "border-blue-500 text-blue-500"
                  : "border-transparent text-zinc-400 hover:border-zinc-700 hover:text-zinc-300"
              )}
              aria-current={isActive ? "page" : undefined}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
