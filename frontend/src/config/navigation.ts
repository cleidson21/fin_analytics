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
  Upload,
  ShieldCheck,
  History,
} from "lucide-react";

type SearchParamsLike = {
  toString(): string;
};

// GOVERNANCE_TABS removido pois os sub-módulos ganharam rotas próprias

export const SIDEBAR_NAV = [
  { name: "Controle Financeiro", href: "/", icon: LayoutDashboard },
  { name: "Investimentos", href: "/wealth", icon: LineChart },
  { name: "Metas", href: "/goals", icon: Target },
  { name: "Governança", href: "/governance", icon: ShieldCheck },
] as const;

export const SECONDARY_NAV = [{ name: "Configurações", href: "/settings", icon: Settings }] as const;

export const SECTION_TABS = {
  dashboard: [
    { name: "Visão Geral", href: "/", icon: LayoutDashboard },
    { name: "Transações", href: "/transactions", icon: Receipt },
    { name: "Categorias", href: "/categories", icon: Tag },
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
    { name: "Visão Geral",     href: "/governance",          icon: LayoutDashboard },
    { name: "Pierre Finance",  href: "/governance/classify", icon: ShieldCheck },
    { name: "MyProfit",        href: "/governance/data",     icon: Database },
    { name: "Importações",     href: "/governance/imports",  icon: Upload },
    { name: "Auditoria",       href: "/governance/audit",    icon: History },
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

  // /cashflow e /transactions compartilham as tabs de dashboard
  return SECTION_TABS.dashboard;
}

export function buildHrefWithSearchParams(pathname: string, searchParams: SearchParamsLike) {
  const queryString = searchParams.toString();
  return queryString ? `${pathname}?${queryString}` : pathname;
}
