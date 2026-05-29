"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowDownRight,
  ArrowRightLeft,
  ArrowUpRight,
  Building2,
  CalendarRange,
  ChevronLeft,
  ChevronRight,
  Filter,
  Save,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

interface Transaction {
  id: string;
  date: string;
  description: string;
  category: string;
  natureza: string;
  subnatureza: string;
  account: string;
  amount: number | string;
}

interface ReclassificationPayload {
  macro_categoria: string;
  natureza: string;
  subnatureza: string;
}

const emptyPayload: ReclassificationPayload = {
  macro_categoria: "",
  natureza: "",
  subnatureza: "",
};

type TransactionKind = "income" | "expense" | "transfer" | "other";

function normalizeText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase()
    .trim();
}

function classifyTransaction(natureza: string): TransactionKind {
  const normalized = normalizeText(natureza);

  if (["INCOME", "RECEITA", "CREDIT", "CREDITO", "CRÉDITO"].includes(normalized)) {
    return "income";
  }

  if (["EXPENSE", "DESPESA", "DEBIT", "DEBITO", "DÉBITO"].includes(normalized)) {
    return "expense";
  }

  if (["TRANSFER", "TRANSFERENCIA", "TRANSFERÊNCIA", "TRANSFERENCIA ENTRE CONTAS"].includes(normalized)) {
    return "transfer";
  }

  return "other";
}

function getNaturezaLabel(kind: TransactionKind, fallback: string) {
  switch (kind) {
    case "income":
      return "Receita";
    case "expense":
      return "Despesa";
    case "transfer":
      return "Transferência";
    default:
      return fallback || "Não classificada";
  }
}

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [selectedAccount, setSelectedAccount] = useState("all");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedNatureza, setSelectedNatureza] = useState("all");
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [form, setForm] = useState<ReclassificationPayload>(emptyPayload);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadData() {
      setLoading(true);
      setError(null);

      const query = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
      });

      const data = await fetchFromAPI<Transaction[]>(`/transactions?${query.toString()}`);

      if (!active) {
        return;
      }

      setTransactions(data || []);

      if (!data) {
        setError("Não foi possível carregar o extrato.");
      }

      setLoading(false);
    }

    loadData();
    return () => {
      active = false;
    };
  }, [limit, offset]);

  const accountOptions = useMemo(() => {
    return Array.from(new Set(transactions.map((tx) => tx.account).filter(Boolean))).sort((left, right) =>
      left.localeCompare(right, "pt-BR")
    );
  }, [transactions]);

  const categoryOptions = useMemo(() => {
    return Array.from(new Set(transactions.map((tx) => tx.category).filter(Boolean))).sort((left, right) =>
      left.localeCompare(right, "pt-BR")
    );
  }, [transactions]);

  const filteredTransactions = useMemo(() => {
    const term = normalizeText(searchTerm);

    return transactions.filter((tx) => {
      const kind = classifyTransaction(tx.natureza);
      const matchesSearch =
        !term ||
        [tx.description, tx.category, tx.natureza, tx.subnatureza, tx.account, tx.date]
          .join(" ")
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .toUpperCase()
          .includes(term);
      const matchesDateRange = (!periodStart || tx.date >= periodStart) && (!periodEnd || tx.date <= periodEnd);
      const matchesAccount = selectedAccount === "all" || tx.account === selectedAccount;
      const matchesCategory = selectedCategory === "all" || tx.category === selectedCategory;
      const matchesNatureza = selectedNatureza === "all" || kind === selectedNatureza;

      return matchesSearch && matchesDateRange && matchesAccount && matchesCategory && matchesNatureza;
    });
  }, [periodEnd, periodStart, searchTerm, selectedAccount, selectedCategory, selectedNatureza, transactions]);

  const summary = useMemo(() => {
    return filteredTransactions.reduce(
      (accumulator, tx) => {
        const amount = Math.abs(Number(tx.amount) || 0);
        const kind = classifyTransaction(tx.natureza);

        if (kind === "income") {
          accumulator.income += amount;
          accumulator.net += amount;
        } else if (kind === "expense") {
          accumulator.expenses += amount;
          accumulator.net -= amount;
        } else if (kind === "other") {
          const signedAmount = Number(tx.amount) || 0;

          if (signedAmount >= 0) {
            accumulator.income += amount;
            accumulator.net += amount;
          } else {
            accumulator.expenses += amount;
            accumulator.net -= amount;
          }
        }

        return accumulator;
      },
      {
        income: 0,
        expenses: 0,
        net: 0,
      }
    );
  }, [filteredTransactions]);

  const pageLabel = useMemo(() => {
    return offset / limit + 1;
  }, [limit, offset]);

  const hasNextPage = transactions.length === limit;
  const hasPreviousPage = offset > 0;

  const goToPreviousPage = () => {
    if (!hasPreviousPage) {
      return;
    }

    setOffset((current) => Math.max(current - limit, 0));
  };

  const goToNextPage = () => {
    if (!hasNextPage) {
      return;
    }

    setOffset((current) => current + limit);
  };

  const openReclassification = (tx: Transaction) => {
    setSelectedTransaction(tx);
    setForm({
      macro_categoria: tx.category,
      natureza: tx.natureza,
      subnatureza: tx.subnatureza,
    });
    setMessage(null);
  };

  const cancelReclassification = () => {
    setSelectedTransaction(null);
    setForm(emptyPayload);
  };

  const handleReclassify = async () => {
    if (!selectedTransaction) {
      return;
    }

    if (!form.macro_categoria.trim() || !form.natureza.trim() || !form.subnatureza.trim()) {
      setMessage("Preencha macro_categoria, natureza e subnatureza.");
      return;
    }

    setSaving(true);
    const result = await fetchFromAPI<{ status: string; message: string }>(
      `/transactions/${selectedTransaction.id}/reclassify`,
      {
        method: "PATCH",
        body: JSON.stringify(form),
      }
    );
    setSaving(false);

    if (!result) {
      setMessage("Não foi possível reclassificar a transação.");
      return;
    }

    setTransactions((current) =>
      current.map((tx) =>
        tx.id === selectedTransaction.id
          ? {
              ...tx,
              category: form.macro_categoria,
              natureza: form.natureza,
              subnatureza: form.subnatureza,
            }
          : tx
      )
    );
    setMessage(result.message);
    cancelReclassification();
  };

  return (
    <PageLayout title="Transações" subtitle="Entrada e saída de capital com hierarquia fiscal e auditoria.">
      <section className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-2xl shadow-black/20 backdrop-blur">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-zinc-500">Sprint 2</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-50">Base de dados e auditoria</h2>
            <p className="mt-2 max-w-2xl text-sm text-zinc-400">
              Revise a taxonomia, filtre o extrato e reclassifique transações diretamente no backend.
            </p>
          </div>

          <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-300">
            <ArrowRightLeft className="size-4 text-cyan-300" />
            <span>{filteredTransactions.length} transações visíveis</span>
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <article className="rounded-3xl border border-white/10 bg-black/20 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Total de Receitas</p>
            <div className="mt-3 flex items-end justify-between gap-3">
              <p className="text-2xl font-semibold tracking-tight text-emerald-300">{formatCurrency(summary.income)}</p>
              <ArrowUpRight className="size-5 text-emerald-300" />
            </div>
          </article>

          <article className="rounded-3xl border border-white/10 bg-black/20 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Total de Despesas</p>
            <div className="mt-3 flex items-end justify-between gap-3">
              <p className="text-2xl font-semibold tracking-tight text-rose-300">{formatCurrency(summary.expenses)}</p>
              <ArrowDownRight className="size-5 text-rose-300" />
            </div>
          </article>

          <article className="rounded-3xl border border-white/10 bg-black/20 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Saldo Líquido</p>
            <div className="mt-3 flex items-end justify-between gap-3">
              <p className={`text-2xl font-semibold tracking-tight ${summary.net >= 0 ? "text-cyan-300" : "text-rose-300"}`}>
                {formatCurrency(summary.net)}
              </p>
              <SlidersHorizontal className="size-5 text-cyan-300" />
            </div>
          </article>

          <article className="rounded-3xl border border-white/10 bg-black/20 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Movimentações</p>
            <div className="mt-3 flex items-end justify-between gap-3">
              <p className="text-2xl font-semibold tracking-tight text-zinc-50">{filteredTransactions.length}</p>
              <Building2 className="size-5 text-zinc-400" />
            </div>
          </article>
        </div>

        <div className="mt-6 grid gap-3 xl:grid-cols-2">
          <label className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-zinc-400">
            <Search className="size-4" />
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Pesquisar por descrição, categoria, natureza ou conta"
              className="w-full bg-transparent text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
            />
          </label>

          <div className="flex items-center gap-3 rounded-2xl border border-dashed border-white/10 bg-black/10 px-4 py-3 text-sm text-zinc-400">
            <Filter className="size-4" />
            Filtros funcionais com paginação real por limit e offset
          </div>
        </div>

        <div className="mt-3 grid gap-3 lg:grid-cols-2 xl:grid-cols-4">
          <label className="space-y-2 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-400">
            <span className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-zinc-500">
              <CalendarRange className="size-4" />
              Período inicial
            </span>
            <input
              type="date"
              value={periodStart}
              onChange={(event) => setPeriodStart(event.target.value)}
              className="w-full bg-transparent text-zinc-100 outline-none"
            />
          </label>

          <label className="space-y-2 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-400">
            <span className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-zinc-500">
              <CalendarRange className="size-4" />
              Período final
            </span>
            <input
              type="date"
              value={periodEnd}
              onChange={(event) => setPeriodEnd(event.target.value)}
              className="w-full bg-transparent text-zinc-100 outline-none"
            />
          </label>

          <label className="space-y-2 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-400">
            <span className="text-xs uppercase tracking-[0.2em] text-zinc-500">Conta</span>
            <select
              value={selectedAccount}
              onChange={(event) => setSelectedAccount(event.target.value)}
              className="w-full bg-transparent text-zinc-100 outline-none"
            >
              <option value="all">Todas as contas</option>
              {accountOptions.map((account) => (
                <option key={account} value={account}>
                  {account}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-400">
            <span className="text-xs uppercase tracking-[0.2em] text-zinc-500">Categoria</span>
            <select
              value={selectedCategory}
              onChange={(event) => setSelectedCategory(event.target.value)}
              className="w-full bg-transparent text-zinc-100 outline-none"
            >
              <option value="all">Todas as categorias</option>
              {categoryOptions.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-400">
          <label className="flex flex-1 min-w-[220px] items-center gap-3 text-zinc-400">
            <span className="text-xs uppercase tracking-[0.2em] text-zinc-500">Tipo</span>
            <select
              value={selectedNatureza}
              onChange={(event) => setSelectedNatureza(event.target.value)}
              className="min-w-0 flex-1 bg-transparent text-zinc-100 outline-none"
            >
              <option value="all">Todos os tipos</option>
              <option value="income">Receita</option>
              <option value="expense">Despesa</option>
              <option value="transfer">Transferência</option>
              <option value="other">Não classificada</option>
            </select>
          </label>

          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-zinc-500">
            <Filter className="size-4" />
            {limit} por página
          </div>
        </div>

        {message ? (
          <div className="mt-4 rounded-2xl border border-cyan-500/20 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-100">
            {message}
          </div>
        ) : null}

        {error ? (
          <div className="mt-4 rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
            {error}
          </div>
        ) : null}

        {selectedTransaction ? (
          <div className="mt-6 rounded-3xl border border-emerald-500/20 bg-emerald-500/10 p-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-emerald-200/80">Reclassificação</p>
                <h3 className="mt-2 text-lg font-semibold text-zinc-50">{selectedTransaction.description}</h3>
                <p className="mt-1 text-sm text-zinc-300">{selectedTransaction.date} • {selectedTransaction.account}</p>
              </div>

              <Button variant="ghost" size="sm" onClick={cancelReclassification} className="self-start">
                <X className="mr-2 size-4" />
                Fechar
              </Button>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-3">
              <label className="space-y-2 text-sm text-zinc-300">
                <span className="block text-xs uppercase tracking-[0.2em] text-zinc-500">Macro categoria</span>
                <input
                  value={form.macro_categoria}
                  onChange={(event) => setForm((current) => ({ ...current, macro_categoria: event.target.value }))}
                  className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-zinc-100 outline-none focus:border-emerald-400/50"
                />
              </label>

              <label className="space-y-2 text-sm text-zinc-300">
                <span className="block text-xs uppercase tracking-[0.2em] text-zinc-500">Natureza</span>
                <input
                  value={form.natureza}
                  onChange={(event) => setForm((current) => ({ ...current, natureza: event.target.value }))}
                  className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-zinc-100 outline-none focus:border-emerald-400/50"
                />
              </label>

              <label className="space-y-2 text-sm text-zinc-300">
                <span className="block text-xs uppercase tracking-[0.2em] text-zinc-500">Subnatureza</span>
                <input
                  value={form.subnatureza}
                  onChange={(event) => setForm((current) => ({ ...current, subnatureza: event.target.value }))}
                  className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-zinc-100 outline-none focus:border-emerald-400/50"
                />
              </label>
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-3">
              <Button onClick={handleReclassify} disabled={saving} className="bg-emerald-500 text-emerald-950 hover:bg-emerald-400">
                <Save className="mr-2 size-4" />
                {saving ? "Salvando..." : "Salvar reclassificação"}
              </Button>
              <span className="text-xs text-zinc-400">A ação chama PATCH /transactions/{selectedTransaction.id}/reclassify.</span>
            </div>
          </div>
        ) : null}

        <div className="mt-6 overflow-hidden rounded-3xl border border-white/10">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="bg-black/25 text-left text-xs uppercase tracking-[0.18em] text-zinc-500">
                <tr>
                  <th className="px-4 py-3">Data</th>
                  <th className="px-4 py-3">Descrição</th>
                  <th className="px-4 py-3">Classificação</th>
                  <th className="px-4 py-3">Conta</th>
                  <th className="px-4 py-3 text-right">Valor</th>
                  <th className="px-4 py-3 text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10 bg-white/5">
                {loading ? (
                  <tr>
                    <td className="px-4 py-6 text-zinc-400" colSpan={6}>
                      A carregar extrato...
                    </td>
                  </tr>
                ) : filteredTransactions.length === 0 ? (
                  <tr>
                    <td className="px-4 py-6 text-zinc-400" colSpan={6}>
                      Nenhuma transação encontrada.
                    </td>
                  </tr>
                ) : (
                  filteredTransactions.map((tx) => {
                    const amountValue = Number(tx.amount) || 0;
                    const amountAbs = Math.abs(amountValue);
                    const kind = classifyTransaction(tx.natureza);
                    const badgeLabel = getNaturezaLabel(kind, tx.natureza);
                    const toneClasses =
                      kind === "income"
                        ? "bg-emerald-500/15 text-emerald-200"
                        : kind === "expense"
                          ? "bg-rose-500/15 text-rose-200"
                          : kind === "transfer"
                            ? "bg-cyan-500/15 text-cyan-200"
                            : "bg-zinc-500/15 text-zinc-200";
                    const badgeIcon =
                      kind === "income" ? (
                        <ArrowUpRight className="size-3.5" />
                      ) : kind === "expense" ? (
                        <ArrowDownRight className="size-3.5" />
                      ) : (
                        <ArrowRightLeft className="size-3.5" />
                      );

                    return (
                      <tr key={tx.id} className="group transition-colors hover:bg-white/5">
                        <td className="px-4 py-4 text-zinc-300">{tx.date}</td>
                        <td className="px-4 py-4 text-zinc-100">{tx.description}</td>
                        <td className="px-4 py-4">
                          <div className="flex flex-col gap-1">
                            <span className={`inline-flex w-fit items-center gap-1 rounded-full border border-white/10 px-2.5 py-1 text-xs font-medium ${toneClasses}`}>
                              {badgeIcon}
                              {badgeLabel}
                              {tx.subnatureza ? ` • ${tx.subnatureza}` : ""}
                            </span>
                            <span className="text-xs text-zinc-500">{tx.category}</span>
                          </div>
                        </td>
                        <td className="px-4 py-4 text-zinc-300">{tx.account}</td>
                        <td className="px-4 py-4 text-right">
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-medium ${toneClasses}`}
                          >
                            {badgeIcon}
                            {formatCurrency(amountAbs)}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openReclassification(tx)}
                            className="text-zinc-400 opacity-100 transition-colors hover:text-emerald-300 group-hover:text-emerald-300"
                          >
                            Reclassificar
                          </Button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-3 rounded-3xl border border-white/10 bg-black/20 px-4 py-4 text-sm text-zinc-400 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <span>{filteredTransactions.length} transações nesta página</span>
            <span className="text-zinc-600">|</span>
            <span>Página {pageLabel}</span>
            <span className="text-zinc-600">|</span>
            <span>{offset + 1} a {offset + transactions.length}</span>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={goToPreviousPage} disabled={!hasPreviousPage || loading}>
              <ChevronLeft className="mr-2 size-4" />
              Anterior
            </Button>
            <Button variant="ghost" size="sm" onClick={goToNextPage} disabled={!hasNextPage || loading}>
              Próxima
              <ChevronRight className="ml-2 size-4" />
            </Button>
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
