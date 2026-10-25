"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { LogOut, User, ChevronDown, ShieldCheck } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  buildPeriodAwareTabHref,
  getTabsForPath,
  isNavigationTabActive,
} from "@/config/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { ThemeSwitcher } from "@/components/ui/ThemeSwitcher";

const TAB_COLORS: Record<string, string> = {
  "/wealth-intelligence/planning": "#c4b5fd",
  "/wealth-intelligence/fire": "#c4b5fd",
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
  "/wealth-intelligence":      "#b794f4",  // Visão geral patrimonial — violeta
  "/wealth-intelligence/health": "#7EB8F7", // Saúde Financeira — azul
  "/wealth-intelligence/goals": "#4ecf98", // Metas — verde
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
          "flex items-center gap-2.5 rounded-full border py-1 pl-1 pr-3 text-sm transition-all duration-200 focus-visible:ring-2 focus-visible:ring-ring motion-reduce:transition-none",
          open
            ? "border-border bg-accent shadow-lg"
            : "border-border bg-card hover:bg-accent"
        )}
      >
        {/* Avatar */}
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 text-[11px] font-bold text-white shadow-sm">
          {initials}
        </span>
        <span className="hidden font-medium text-foreground sm:block">{firstName}</span>
        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 text-muted-foreground transition-transform duration-200 motion-reduce:transition-none",
            open && "rotate-180"
          )}
        />
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-56 overflow-hidden rounded-2xl border border-border bg-popover text-popover-foreground shadow-2xl shadow-black/20">
          {/* User info header */}
          <div className="flex items-center gap-3 border-b border-border px-4 py-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 text-[13px] font-bold text-white">
              {initials}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-foreground">
                {user.name || "Usuário"}
              </p>
              <p className="truncate text-[11px] text-muted-foreground">{user.email}</p>
            </div>
          </div>

          {/* Role badge */}
          <div className="border-b border-border px-4 py-2.5">
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
              className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring"
            >
              <User className="h-4 w-4 text-muted-foreground" />
              Meu perfil
            </Link>
            <button
              onClick={() => { setOpen(false); logout(); }}
              className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-destructive transition-colors hover:bg-destructive/10 focus-visible:ring-2 focus-visible:ring-destructive"
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
  const searchParams = useSearchParams();

  const tabs = getTabsForPath(pathname);
  if (!tabs) {
    return null;
  }

  return (
    <div className="relative flex flex-col gap-3 px-4 pt-4 sm:px-6 lg:block lg:pt-8">
      <nav aria-label="Navegação da seção" className="relative z-10 flex w-full min-w-0 items-center gap-1 overflow-x-auto rounded-full border border-border bg-card p-1 shadow-sm lg:mx-auto lg:w-fit">
        {tabs.map((tab) => {
          const isActive = isNavigationTabActive(
            pathname,
            tab.href,
            tabs.map((candidate) => candidate.href),
          );

          const dotColor = TAB_COLORS[tab.href];

          return (
            <Link
              key={tab.name}
              href={buildPeriodAwareTabHref(pathname, tab.href, searchParams)}
              className={cn(
                "flex cursor-pointer items-center gap-1.5 rounded-full px-4 py-1.5 text-sm transition-all duration-200 focus-visible:ring-2 focus-visible:ring-ring motion-reduce:transition-none",
                isActive
                  ? "bg-accent font-semibold text-accent-foreground shadow-sm ring-1 ring-inset ring-border"
                  : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              )}
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
      <div className="order-first flex items-center justify-end gap-2 lg:absolute lg:right-6 lg:top-6 lg:z-20">
        <ThemeSwitcher compact />
        <UserMenu />
      </div>
    </div>
  );
}
