import {
  BarChart3,
  Building2,
  CreditCard,
  LayoutDashboard,
  LineChart,
  PieChart,
  Receipt,
  Settings,
  Tag,
  Target,
  TrendingUp,
  Tv,
  Database,
  FileSearch,
  Upload,
} from "lucide-react";
type SearchParamsLike = {
  toString(): string;
};

export const GOVERNANCE_TABS = [
  { name: "Auditoria", href: "/governance/audit", dotColor: "bg-rose-500" },
  { name: "Saneamento", href: "/governance/database", dotColor: "bg-zinc-500" },
  { name: "Dados", href: "/governance/data", dotColor: "bg-blue-500" },
] as const;

export const SIDEBAR_NAV = [
  { name: "Controle Financeiro", href: "/", icon: LayoutDashboard },
  { name: "Investimentos", href: "/wealth", icon: LineChart },
  { name: "Metas", href: "/goals", icon: Target },
  { name: "Governança", href: "/governance", icon: Receipt },
] as const;

export const SECONDARY_NAV = [{ name: "Configurações", href: "/settings", icon: Settings }] as const;

export const SECTION_TABS = {
  dashboard: [
    { name: "Visão Geral", href: "/", icon: LayoutDashboard },
    { name: "Transações", href: "/transactions", icon: Receipt },
    { name: "Categorias", href: "/categories", icon: Tag },
    { name: "Assinaturas", href: "/subscriptions", icon: Tv },
    { name: "Parcelamentos", href: "/installments", icon: CreditCard },
  ],
  wealth: [
    { name: "Resumo", href: "/wealth", icon: LayoutDashboard },
    { name: "Patrimônio", href: "/wealth/patrimonio", icon: PieChart },
    { name: "Alocação", href: "/wealth/allocation", icon: TrendingUp },
    { name: "Dividendos", href: "/wealth/dividends", icon: BarChart3 },
    { name: "Evolução", href: "/wealth/evolution", icon: LineChart },
  ],
  governance: [
    { name: "Dashboard", href: "/governance", icon: LayoutDashboard },
    {
      name: "Nova Importação",
      href: "/governance/imports",
      icon: Upload,
    },
    {
      name: "Administração do Banco",
      href: "/governance/database",
      icon: Database,
    },
    {
      name: "Auditoria",
      href: "/governance/audit",
      icon: FileSearch,
    },
    {
      name: "Dados",
      href: "/governance/data",
      icon: Receipt,
    },
  ],
  settings: [
    { name: "Geral", href: "/settings", icon: Settings },
    { name: "Perfil", href: "/profile", icon: Settings },
    { name: "Contas", href: "/accounts", icon: Building2 },
  ],
  goals: [],
} as const;

export function getTabsForPath(pathname: string) {
  if (pathname.startsWith("/wealth")) return SECTION_TABS.wealth;
  if (pathname.startsWith("/governance")) return SECTION_TABS.governance;
  if (pathname.startsWith("/goals")) return SECTION_TABS.goals;
  if (pathname.startsWith("/settings") || pathname.startsWith("/accounts") || pathname.startsWith("/profile")) return SECTION_TABS.settings;

  return SECTION_TABS.dashboard;
}

export function buildHrefWithSearchParams(pathname: string, searchParams: SearchParamsLike) {
  const queryString = searchParams.toString();

  return queryString ? `${pathname}?${queryString}` : pathname;
}
