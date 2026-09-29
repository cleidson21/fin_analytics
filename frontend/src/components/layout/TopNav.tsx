"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { LogOut, User, ChevronDown, ShieldCheck } from "lucide-react";

import { cn } from "@/lib/utils";
import { getTabsForPath } from "@/config/navigation";
import { useAuth } from "@/contexts/AuthContext";

const TAB_COLORS: Record<string, string> = {
  "/wealth-intelligence/planning": "#c4b5fd",
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
  "/wealth-intelligence":      "#b794f4",  // Wealth Intelligence Dashboard — violeta
  "/wealth-intelligence/health": "#7EB8F7", // Saúde Financeira — azul
  "/goals":                    "#4ecf98",  // Metas — verde
  "/wealth":                   "#94a3b8",  // Resumo — neutro
  "/wealth/patrimonio":        "#4ecf98",  // Patrimônio — verde
  "/wealth/allocation":        "#f5a623",  // Alocação — âmbar
  "/wealth/dividends":         "#f687b3",  // Dividendos — rosa
  "/wealth/evolution":         "#7EB8F7",  // Evolução — azul
  "/profile":                  "#f687b3",  // Perfil — rosa
  "/settings":                 "#94a3b8",  // Geral — slate
  "/accounts":                 "#4ecf98",  // Contas — verde
};

function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  if (!user) return null;

  const initials = (user.name || user.email || "U")
    .split(" ")
    .slice(0, 2)
    .map((w: string) => w[0])
    .join("")
    .toUpperCase();

  const firstName = (user.name || user.email || "Usuário").split(" ")[0];

  return (
    <div ref={ref} className="relative z-20">
      {/* Trigger pill */}
      <button
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex items-center gap-2.5 rounded-full border py-1 pl-1 pr-3 text-sm transition-all duration-200",
          open
            ? "border-white/15 bg-white/[0.08] shadow-lg"
            : "border-white/[0.07] bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/12"
        )}
      >
        {/* Avatar */}
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 text-[11px] font-bold text-white shadow-sm">
          {initials}
        </span>
        <span className="font-medium text-zinc-200 hidden sm:block">{firstName}</span>
        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 text-zinc-500 transition-transform duration-200",
            open && "rotate-180"
          )}
        />
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-56 overflow-hidden rounded-2xl border border-white/[0.09] bg-zinc-950/95 shadow-2xl shadow-black/50 backdrop-blur-xl">
          {/* User info header */}
          <div className="flex items-center gap-3 border-b border-white/[0.06] px-4 py-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 text-[13px] font-bold text-white">
              {initials}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-zinc-100">
                {user.name || "Usuário"}
              </p>
              <p className="truncate text-[11px] text-zinc-500">{user.email}</p>
            </div>
          </div>

          {/* Role badge */}
          <div className="px-4 py-2.5 border-b border-white/[0.06]">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-400 ring-1 ring-inset ring-emerald-400/20">
              <ShieldCheck className="h-3 w-3" />
              {user.role}
            </span>
          </div>

          {/* Actions */}
          <div className="p-1.5">
            <Link
              href="/profile"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-zinc-300 transition-colors hover:bg-white/[0.05] hover:text-zinc-100"
            >
              <User className="h-4 w-4 text-zinc-500" />
              Meu perfil
            </Link>
            <button
              onClick={() => { setOpen(false); logout(); }}
              className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-rose-400 transition-colors hover:bg-rose-500/[0.08] hover:text-rose-300"
            >
              <LogOut className="h-4 w-4" />
              Sair da conta
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
export function TopNav() {
  const pathname = usePathname();

  const tabs = getTabsForPath(pathname);
  if (!tabs) {
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
                "flex cursor-pointer items-center gap-1.5 rounded-full px-4 py-1.5 text-sm transition-all duration-200",
                isActive
                  ? "font-semibold shadow-sm"
                  : "text-neutral-500 hover:text-neutral-300"
              )}
              style={
                isActive && dotColor
                  ? {
                      color: dotColor,
                      background: `${dotColor}14`,
                      boxShadow: `0 0 0 1px ${dotColor}25`,
                    }
                  : undefined
              }
            >
              <span
                className={cn("h-[7px] w-[7px] flex-shrink-0 rounded-full", !isActive && "opacity-25")}
                style={{ background: dotColor }}
              />
              {tab.name}
            </Link>
          );
        })}
      </nav>

      {/* User Menu — top right */}
      <div className="absolute right-6 top-6 z-20">
        <UserMenu />
      </div>
    </div>
  );
}
