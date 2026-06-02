"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { getTabsForPath } from "@/config/navigation";

const TAB_COLORS: Record<string, string> = {
  "/":              "#4ecf98",  // Visão geral — verde
  "/transactions":  "#7EB8F7",  // Transações — azul
  "/installments":  "#f5a623",  // Parcelamentos — âmbar
  "/subscriptions": "#b794f4",  // Assinaturas — violeta
  "/categories":    "#f687b3",  // Categorias — rosa
  "/governance":         "#94a3b8",  // Revisão de Dados — cinza-azulado
  "/governance/import":  "#94a3b8",  // Importação CSV — mesma cor da secção
};

export function TopNav() {
  const pathname = usePathname();

  const tabs = getTabsForPath(pathname);
  if (!tabs || tabs.length === 0) {
    return null;
  }

  return (
    <div className="flex justify-center pt-8 pb-0">
      <nav className="flex min-w-0 items-center gap-1 overflow-x-auto rounded-full bg-white/[0.03] p-1">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href || (tab.href !== "/" && pathname.startsWith(tab.href + "/"));
          const dotColor = TAB_COLORS[tab.href];

          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={cn(
                "flex cursor-pointer items-center gap-1.5 rounded-full px-4 py-1.5 text-sm transition-colors",
                isActive
                  ? "bg-[#1a1a1a] font-medium"
                  : "text-neutral-600 hover:text-neutral-400"
              )}
              style={isActive && dotColor ? { color: dotColor } : undefined}
            >
              <span
                className={cn("h-[7px] w-[7px] flex-shrink-0 rounded-full", !isActive && "opacity-30")}
                style={{ background: dotColor }}
              />
              {tab.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}