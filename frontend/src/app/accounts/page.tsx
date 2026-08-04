"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import { TopNav } from "@/components/layout/TopNav";
import { useAccounts } from "@/hooks/useAccounts";
import { AccountDTO } from "@/types/entities";

const ACCOUNT_TYPE_LABEL: Record<string, string> = {
  BANK: "Conta Bancária",
  CREDIT_CARD: "Cartão de Crédito",
  INVESTMENT: "Investimento",
  LOAN: "Empréstimo",
  WALLET: "Carteira Digital",
};

function AccountCard({ account }: { account: AccountDTO }) {
  const typeLabel = ACCOUNT_TYPE_LABEL[account.type] ?? account.type;
  const isCredit = account.type === "CREDIT_CARD";
  const balance = account.balance ?? 0;

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 hover:bg-white/[0.05] transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-sm font-medium text-zinc-100">{account.name}</p>
          {account.institution && (
            <p className="text-xs text-zinc-500 mt-0.5">
              {account.institution.name}
            </p>
          )}
        </div>
        <span
          className={`text-[10px] font-medium px-2 py-0.5 rounded-full ring-1 ring-inset ${
            account.is_active
              ? "bg-emerald-400/10 text-emerald-400 ring-emerald-400/20"
              : "bg-zinc-500/10 text-zinc-500 ring-zinc-500/20"
          }`}
        >
          {account.is_active ? "Ativa" : "Inativa"}
        </span>
      </div>

      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs text-zinc-500 mb-0.5">{typeLabel}</p>
          <p className="text-xs text-zinc-600">{account.provider}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-zinc-500 mb-0.5">Saldo</p>
          <p
            className={`text-base font-semibold tabular-nums ${
              isCredit
                ? balance < 0
                  ? "text-red-400"
                  : "text-zinc-300"
                : "text-zinc-100"
            }`}
          >
            {account.currency_code}{" "}
            {balance.toLocaleString("pt-BR", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function AccountsPage() {
  const { data: accounts, isLoading, error } = useAccounts();

  return (
    <>
      <PageLayout>
        <div className="mb-8">
          <h1 className="text-xl font-semibold text-zinc-100">Contas</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Visão geral das suas contas financeiras conectadas.
          </p>
        </div>

        {isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-28 rounded-2xl bg-white/[0.03] animate-pulse"
              />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-red-400 text-sm">
            {error}
          </div>
        )}

        {!isLoading && !error && accounts.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-zinc-500 text-sm">Nenhuma conta encontrada.</p>
            <p className="text-zinc-600 text-xs mt-1">
              Conecte um Provider para sincronizar suas contas.
            </p>
          </div>
        )}

        {!isLoading && !error && accounts.length > 0 && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {accounts.map((account) => (
                <AccountCard key={account.id} account={account} />
              ))}
            </div>
            <p className="mt-4 text-xs text-zinc-600">
              {accounts.length} conta{accounts.length !== 1 ? "s" : ""}{" "}
              encontrada{accounts.length !== 1 ? "s" : ""}.
            </p>
          </>
        )}
      </PageLayout>
    </>
  );
}
