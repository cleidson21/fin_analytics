"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { getTabsForPath } from "@/config/navigation";
import { useAuth } from "@/contexts/AuthContext";

const TAB_COLORS: Record<string, string> = {
  "/":              "#4ecf98",  // Visão geral — verde
  "/transactions":  "#7EB8F7",  // Transações — azul
  "/installments":  "#f5a623",  // Parcelamentos — âmbar
  "/categories":    "#f687b3",  // Categorias — rosa
  "/cashflow":                "#22c55e",  // Fluxo de Caixa — verde
  "/governance":               "#94a3b8",  // Dashboard de Governança
  "/governance/classify":      "#b794f4",  // Pierre Finance — violeta
  "/governance/data":          "#7EB8F7",  // MyProfit — azul
  "/governance/imports":       "#4ecf98",  // Nova Importação — verde
  "/governance/database":      "#94a3b8",  // Saneamento — slate
  "/governance/audit":         "#f687b3",  // Auditoria — rosa
  "/wealth":                   "#94a3b8",  // Resumo — neutro
  "/wealth/patrimonio":        "#4ecf98",  // Patrimônio — verde
  "/wealth/allocation":        "#f5a623",  // Alocação — âmbar
  "/wealth/dividends":         "#f687b3",  // Dividendos — rosa
  "/wealth/evolution":         "#7EB8F7",  // Evolução — azul
  "/profile":                  "#f687b3",  // Perfil — rosa
  "/settings":                 "#94a3b8",  // Geral — slate
  "/accounts":                 "#4ecf98",  // Contas — verde
};

export function TopNav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const tabs = getTabsForPath(pathname);
  if (!tabs || tabs.length === 0) {
    return null;
  }

  return (
    <div className="flex justify-center pt-8 pb-0">
      <nav className="flex min-w-0 items-center gap-1 overflow-x-auto rounded-full bg-white/[0.03] p-1 relative z-10">
        {tabs.map((tab) => {
          let activePath = pathname;
          if (pathname.startsWith("/wealth/asset")) {
            activePath = "/wealth/allocation";
          }
          
          let isActive = activePath === tab.href;

          if (!tabs.some(t => t.href === activePath)) {
             if (tab.href !== "/" && tab.href !== "/wealth" && tab.href !== "/governance" && activePath.startsWith(tab.href + "/")) {
                isActive = true;
             } else {
                 const isBaseTab = tab.href === "/" || tab.href === "/wealth" || tab.href === "/governance";
                 // Only highlight base tab if NO other tab is a prefix match
                 const hasOtherPrefixMatch = tabs.some(t => t.href !== tab.href && t.href !== "/" && activePath.startsWith(t.href + "/"));
                 if (isBaseTab && activePath.startsWith(tab.href === "/" ? "/" : tab.href + "/") && !hasOtherPrefixMatch) {
                    isActive = true;
                 }
             }
          }

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

      {user && (
        <div className="absolute right-8 top-8 flex items-center gap-4 text-sm z-20">
          <div className="text-zinc-400">
            <span className="font-medium text-zinc-300">{user.role}</span>{" "}
            {user.name ?? user.email}
          </div>
          <button
            onClick={() => logout()}
            className="text-red-400 hover:text-red-300 font-medium transition-colors"
          >
            Logout
          </button>
        </div>
      )}
    </div>
  );
}