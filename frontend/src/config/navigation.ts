import {
  BarChart3,
  Flame,
  LayoutDashboard,
  LineChart,
  PieChart,
  Receipt,
  Settings,
  Tag,
  Target,
  TrendingUp,
  Tv,
} from "lucide-react";

export const SIDEBAR_NAV = [
  { name: "Controle Financeiro", href: "/", icon: LayoutDashboard },
  { name: "Investimentos", href: "/wealth", icon: LineChart },
  { name: "Metas", href: "/goals", icon: Target },
  { name: "Importações", href: "/imports", icon: Receipt },
  { name: "Perfil", href: "/profile", icon: Settings },
] as const;

export const SECONDARY_NAV = [{ name: "Configurações", href: "/settings", icon: Settings }] as const;

export const SECTION_TABS = {
  dashboard: [
    { name: "Visão Geral", href: "/", icon: LayoutDashboard },
    { name: "Transações", href: "/transactions", icon: Receipt },
    { name: "Categorias", href: "/categories", icon: Tag },
    { name: "Assinaturas", href: "/subscriptions", icon: Tv },
    { name: "Parcelamentos", href: "/installments", icon: BarChart3 },
    { name: "Heatmap", href: "/heatmap", icon: Flame },
  ],
  wealth: [
    { name: "Patrimônio", href: "/wealth", icon: PieChart },
    { name: "Alocação", href: "/wealth/allocation", icon: TrendingUp },
    { name: "Dividendos", href: "/wealth/dividends", icon: BarChart3 },
    { name: "Evolução", href: "/wealth/evolution", icon: LineChart },
  ],
  transactions: [],
  goals: [],
} as const;

export function getTabsForPath(pathname: string) {
  if (pathname.startsWith("/wealth")) return SECTION_TABS.wealth;
  if (pathname.startsWith("/transactions")) return SECTION_TABS.transactions;
  if (pathname.startsWith("/goals")) return SECTION_TABS.goals;

  return SECTION_TABS.dashboard;
}
