"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import { useAccounts } from "@/hooks/useAccounts";
import { AccountDTO } from "@/types/entities";
import {
  Building2,
  CreditCard,
  TrendingUp,
  Wallet,
  HandCoins,
  CircleDollarSign,
  RefreshCw,
  AlertCircle,
} from "lucide-react";

const ACCOUNT_TYPE_CONFIG: Record<
  string,
  { label: string; icon: React.ElementType; color: string; ring: string; bg: string }
> = {
  BANK: {
    label: "Conta Bancária",
    icon: Building2,
    color: "text-sky-400",
    ring: "ring-sky-400/20",
    bg: "bg-sky-400/10",
  },
  CREDIT_CARD: {
    label: "Cartão de Crédito",
    icon: CreditCard,
    color: "text-rose-400",
    ring: "ring-rose-400/20",
    bg: "bg-rose-400/10",
  },
  INVESTMENT: {
    label: "Investimento",
    icon: TrendingUp,
    color: "text-emerald-400",
    ring: "ring-emerald-400/20",
    bg: "bg-emerald-400/10",
  },
  LOAN: {
    label: "Empréstimo",
    icon: HandCoins,
    color: "text-amber-400",
    ring: "ring-amber-400/20",
    bg: "bg-amber-400/10",
  },
  WALLET: {
    label: "Carteira Digital",
    icon: Wallet,
    color: "text-violet-400",
    ring: "ring-violet-400/20",
    bg: "bg-violet-400/10",
  },
};

const DEFAULT_CONFIG = {
  label: "Conta",
  icon: CircleDollarSign,
  color: "text-zinc-400",
  ring: "ring-zinc-400/20",
  bg: "bg-zinc-400/10",
};

function AccountCard({ account }: { account: AccountDTO }) {
  const config = ACCOUNT_TYPE_CONFIG[account.type] ?? DEFAULT_CONFIG;
  const Icon = config.icon;
  const balance = account.balance ?? 0;
  const isCredit = account.type === "CREDIT_CARD";
  const isNegative = balance < 0;

  const balanceColor = isCredit
    ? isNegative
      ? "text-rose-400"
      : "text-zinc-300"
    : balance >= 0
    ? "text-emerald-400"
    : "text-rose-400";

  return (
    <div className="group relative flex flex-col gap-4 overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5 transition-all duration-200 hover:border-white/[0.12] hover:bg-white/[0.04]">
      {/* Watermark icon */}
      <div className="pointer-events-none absolute -right-3 -top-3 opacity-[0.04] group-hover:opacity-[0.07] transition-opacity">
        <Icon className="w-24 h-24" />
      </div>

      {/* Header */}
      <div className="flex items-start justify-between relative z-10">
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ring-1 ring-inset ${config.bg} ${config.ring}`}>
          <Icon className={`w-5 h-5 ${config.color}`} />
        </div>
        <span
          className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ring-1 ring-inset ${
            account.is_active
              ? "bg-emerald-400/10 text-emerald-400 ring-emerald-400/20"
              : "bg-zinc-500/10 text-zinc-500 ring-zinc-500/20"
          }`}
        >
          {account.is_active ? "Ativa" : "Inativa"}
        </span>
      </div>

      {/* Info */}
      <div className="relative z-10 flex-1 min-w-0">
        <p className="text-sm font-semibold text-zinc-100 truncate">{account.name}</p>
        {account.institution && (
          <p className="text-xs text-zinc-500 mt-0.5 truncate">{account.institution.name}</p>
        )}
        <div className="flex items-center gap-2 mt-1">
          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-md ${config.bg} ${config.color}`}>
            {config.label}
          </span>
          {account.provider && (
            <span className="text-[10px] text-zinc-600 uppercase tracking-wider">{account.provider}</span>
          )}
        </div>
      </div>

      {/* Balance */}
      <div className="relative z-10 flex items-end justify-between border-t border-white/[0.05] pt-3">
        <p className="text-[10px] uppercase tracking-wider text-zinc-600">Saldo</p>
        <p className={`text-lg font-bold tabular-nums ${balanceColor}`}>
          {account.currency_code}{" "}
          {balance.toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </p>
      </div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-white/[0.05] bg-white/[0.02] p-5 space-y-4 animate-pulse">
      <div className="flex justify-between">
        <div className="h-10 w-10 rounded-xl bg-white/[0.05]" />
        <div className="h-5 w-16 rounded-full bg-white/[0.05]" />
      </div>
      <div className="space-y-2">
        <div className="h-4 w-3/4 rounded bg-white/[0.05]" />
        <div className="h-3 w-1/2 rounded bg-white/[0.04]" />
      </div>
      <div className="flex justify-between border-t border-white/[0.05] pt-3">
        <div className="h-3 w-10 rounded bg-white/[0.04]" />
        <div className="h-5 w-24 rounded bg-white/[0.05]" />
      </div>
    </div>
  );
}

export default function AccountsPage() {
  const { data: accounts, isLoading, error } = useAccounts();

  // Group by type for summary
  const totalBalance = accounts.reduce((sum, a) => {
    if (a.type === "CREDIT_CARD") return sum;
    return sum + (a.balance ?? 0);
  }, 0);

  const activeCount = accounts.filter((a) => a.is_active).length;

  return (
    <PageLayout title="Contas">
      <div className="space-y-6 pb-12">

        {/* Summary bar */}
        {!isLoading && !error && accounts.length > 0 && (
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-3 rounded-2xl border border-white/[0.07] bg-white/[0.02] px-5 py-3">
              <Building2 className="w-4 h-4 text-zinc-500" />
              <div>
                <p className="text-[10px] uppercase tracking-wider text-zinc-600">Contas</p>
                <p className="text-sm font-semibold text-zinc-200">{activeCount} ativas de {accounts.length}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-2xl border border-white/[0.07] bg-white/[0.02] px-5 py-3">
              <CircleDollarSign className="w-4 h-4 text-emerald-500" />
              <div>
                <p className="text-[10px] uppercase tracking-wider text-zinc-600">Saldo total (excl. cartões)</p>
                <p className={`text-sm font-semibold tabular-nums ${totalBalance >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  R$ {totalBalance.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => <SkeletonCard key={i} />)}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-start gap-3 rounded-2xl border border-red-500/20 bg-red-500/[0.05] p-4">
            <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Empty */}
        {!isLoading && !error && accounts.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-white/[0.08] py-16 text-center">
            <Building2 className="w-8 h-8 text-zinc-700" />
            <div>
              <p className="text-sm font-medium text-zinc-400">Nenhuma conta encontrada</p>
              <p className="text-xs text-zinc-600 mt-1">
                Conecte um Provider para sincronizar suas contas financeiras.
              </p>
            </div>
          </div>
        )}

        {/* Grid */}
        {!isLoading && !error && accounts.length > 0 && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {accounts.map((account) => (
                <AccountCard key={account.id} account={account} />
              ))}
            </div>
            <p className="flex items-center gap-1.5 text-xs text-zinc-600">
              <RefreshCw className="w-3 h-3" />
              {accounts.length} conta{accounts.length !== 1 ? "s" : ""} sincronizada{accounts.length !== 1 ? "s" : ""} via Open Finance
            </p>
          </>
        )}
      </div>
    </PageLayout>
  );
}
