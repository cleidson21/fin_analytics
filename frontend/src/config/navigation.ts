import {
  BarChart3,
  Building2,
  CreditCard,
  HeartPulse,
  LayoutDashboard,
  LineChart,
  PieChart,
  Receipt,
  Settings,
  Tag,
  Target,
  TrendingUp,
  Database,
  Upload,
  ShieldCheck,
  History,
  UserCircle,
} from "lucide-react";

type SearchParamsLike = {
  get(name: string): string | null;
  toString(): string;
};

// GOVERNANCE_TABS removido pois os sub-módulos ganharam rotas próprias

export const SIDEBAR_NAV = [
  { name: "Controle Financeiro", href: "/", icon: LayoutDashboard },
  { name: "Investimentos", href: "/wealth", icon: LineChart },
  { name: "Inteligência Patrimonial", href: "/wealth-intelligence", icon: Target },
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
    { name: "Perfil", href: "/profile", icon: UserCircle },
    { name: "Contas", href: "/accounts", icon: Building2 },
  ],
  wealthIntelligence: [
    { name: "Visão geral", href: "/wealth-intelligence", icon: LayoutDashboard },
    { name: "Metas", href: "/wealth-intelligence/goals", icon: Target },
    { name: "Saúde Financeira", href: "/wealth-intelligence/health", icon: HeartPulse },
    { name: "Planejamento", href: "/wealth-intelligence/planning", icon: LineChart },
    { name: "Independência Financeira", href: "/wealth-intelligence/fire", icon: Target },
  ],
} as const;

export function getTabsForPath(pathname: string) {
  if (pathname.startsWith("/wealth-intelligence") || pathname.startsWith("/goals")) return SECTION_TABS.wealthIntelligence;
  if (pathname.startsWith("/wealth")) return SECTION_TABS.wealth;
  if (pathname.startsWith("/governance")) return SECTION_TABS.governance;
  if (pathname.startsWith("/settings") || pathname.startsWith("/accounts") || pathname.startsWith("/profile")) return SECTION_TABS.settings;

  // /cashflow e /transactions compartilham as tabs de dashboard
  return SECTION_TABS.dashboard;
}

export function isSidebarNavigationActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return (
      pathname === "/" ||
      pathname.startsWith("/transactions") ||
      pathname.startsWith("/categories") ||
      pathname.startsWith("/installments")
    );
  }
  if (href === "/governance") return pathname.startsWith("/governance");
  if (href === "/wealth-intelligence") {
    return pathname.startsWith("/wealth-intelligence") || pathname.startsWith("/goals");
  }
  if (href === "/wealth") return pathname === "/wealth" || pathname.startsWith("/wealth/");
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function isNavigationTabActive(
  pathname: string,
  href: string,
  tabHrefs: readonly string[],
): boolean {
  const activePath = pathname.startsWith("/wealth/asset")
    ? "/wealth/allocation"
    : pathname;

  if (activePath.startsWith("/goals") && href === "/wealth-intelligence/goals") return true;

  if (activePath === href) return true;

  const exactTabExists = tabHrefs.includes(activePath);
  if (exactTabExists) return false;

  const isSectionBase = href === "/" || href === "/wealth" || href === "/governance";
  const hasMoreSpecificMatch = tabHrefs.some(
    (candidate) =>
      candidate !== href &&
      candidate !== "/" &&
      activePath.startsWith(`${candidate}/`),
  );

  if (isSectionBase) {
    const insideSection = href === "/" ? activePath.startsWith("/") : activePath.startsWith(`${href}/`);
    return insideSection && !hasMoreSpecificMatch;
  }

  return activePath.startsWith(`${href}/`);
}

export function buildHrefWithSearchParams(pathname: string, searchParams: SearchParamsLike) {
  const queryString = searchParams.toString();
  return queryString ? `${pathname}?${queryString}` : pathname;
}

export function buildPeriodAwareTabHref(
  currentPathname: string,
  targetHref: string,
  searchParams: SearchParamsLike,
): string {
  const periodRoutes = new Set([
    "/wealth-intelligence",
    "/wealth-intelligence/health",
  ]);
  if (periodRoutes.has(currentPathname) && periodRoutes.has(targetHref)) {
    return buildHrefWithSearchParams(targetHref, searchParams);
  }
  return targetHref;
}
