"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
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
  Scale,
  Search,
  SlidersHorizontal,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { getCurrentMonth, getMonthBounds } from "@/lib/period";

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

interface TransactionListResponse {
  items: Transaction[];
  total: number;
}

interface ReclassificationPayload {
  macro_categoria: string;
  natureza: string;
  subnatureza: string;
}

interface CatalogResponse {
  categories: string[];
  natures: string[];
  accounts: string[];
}

const NATURE_LABELS: Record<string, string> = {
  INCOME: "Receita",
  EXPENSE: "Despesa",
  TRANSFER: "Transferencia",
  INVESTMENT: "Investimento",
  DIVIDEND: "Dividendo",
};

interface GovernanceSummary {
  total_entrada: number;
  total_saida: number;
  resultado: number;
  pending_count: number;
  classified_count: number;
  ignored_count: number;
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

function TransactionsPageBody() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  const fallbackMonth = getCurrentMonth();
  const fallbackMonthBounds = getMonthBounds(fallbackMonth);

  const [startDate, setStartDate] = useState(() => searchParams.get("startDate") ?? fallbackMonthBounds.startDate);
  const [endDate, setEndDate] = useState(() => searchParams.get("endDate") ?? fallbackMonthBounds.endDate);
  const [account, setAccount] = useState(() => searchParams.get("account") ?? "all");
  const [category, setCategory] = useState(() => searchParams.get("category") ?? "all");
  // Sanitiza o valor da URL: aceita apenas ENTRADA | SAIDA (rejeita valores legados como CREDIT/DEBIT)
  const [natureza, setNatureza] = useState(() => {
    const v = searchParams.get("natureza") ?? "all";
    return ["ENTRADA", "SAIDA", "all"].includes(v) ? v : "all";
  });
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  const [catalog, setCatalog] = useState<CatalogResponse>({
    accounts: [],
    categories: [],
    natures: [],
  });
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [summary, setSummary] = useState({
    income: 0,
    expense: 0,
    balance: 0,
  });
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [form, setForm] = useState<ReclassificationPayload>(emptyPayload);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // Governance KPIs — atualizados junto com loadData (período-preciso)
  const [govSummary, setGovSummary] = useState<GovernanceSummary | null>(null);

  const currentPage = Math.floor(offset / limit) + 1;
  const hasPreviousPage = offset > 0;
  const hasNextPage = totalPages > 0 && currentPage < totalPages;
  const rangeStart = total > 0 ? offset + 1 : 0;
  const rangeEnd = total > 0 ? Math.min(offset + transactions.length, total) : 0;

  useEffect(() => {
    const nextParams = new URLSearchParams();

    nextParams.set("startDate", startDate);
    nextParams.set("endDate", endDate);

    if (account !== "all") {
      nextParams.set("account", account);
    }

    if (category !== "all") {
      nextParams.set("category", category);
    }

    if (natureza !== "all") {
      nextParams.set("natureza", natureza);
    }

    const nextQuery = nextParams.toString();

    if (nextQuery !== searchParams.toString()) {
      router.replace(nextQuery ? `${pathname}?${nextQuery}` : pathname, { scroll: false });
    }
  }, [account, category, endDate, natureza, pathname, router, searchParams, startDate]);

  useEffect(() => {
    let active = true;

    async function loadCatalog() {
      try {
        const [categoriesResponse, accountsResponse] = await Promise.allSettled([
          fetchFromAPI<{ name: string }[]>("/categories"),
          fetchFromAPI<{ name: string }[]>("/accounts")
        ]);

        if (!active) {
          return;
        }

        const cats = categoriesResponse.status === "fulfilled" && categoriesResponse.value 
          ? categoriesResponse.value.map(c => c.name) 
          : [];
          
        const accs = accountsResponse.status === "fulfilled" && accountsResponse.value 
          ? accountsResponse.value.map(a => a.name) 
          : [];

        setCatalog({
          categories: cats,
          accounts: accs,
          natures: ["INCOME", "EXPENSE", "TRANSFER", "INVESTMENT", "DIVIDEND"]
        });
      } catch (err) {
        console.warn("[catalog fallback] Failed to load catalog data.", err);
      }
    }

    loadCatalog();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadData() {
      setLoading(true);
      setError(null);

      try {
        if (startDate > endDate) {
          setTransactions([]);
          setTotal(0);
          setTotalPages(0);
          setSummary({ income: 0, expense: 0, balance: 0 });
          return;
        }

        // Usa /governance/transactions que suporta todos os filtros
        const query = new URLSearchParams({
          start_date: startDate,
          end_date: endDate,
          page: String(Math.floor(offset / limit) + 1),
          page_size: String(limit),
        });

        // Filtro de categoria (nome da categoria RAW)
        if (category !== "all") {
          query.set("category", category);
        }

        // Filtro de tipo: ENTRADA | SAIDA mapeados para economic_classification
        if (natureza !== "all") {
          query.set("economic_classification", natureza);
        }

        const data = await fetchFromAPI<{ items: any[]; total: number }>(
          `/governance/transactions?${query.toString()}`
        );

        if (!active) return;

        const items: any[] = data?.items || [];

        // Mapeia do formato { raw: {...}, governance: {...} } para Transaction
        const mappedItems = items.map((t: any) => ({
          id: `${t.raw?.provider}::${t.raw?.external_id}`,
          // Trunca para YYYY-MM-DD (descarta componente de hora se vier como DateTime)
          date: (t.raw?.date ?? "").slice(0, 10),
          description: t.raw?.description ?? "",
          category: t.raw?.category ?? "",
          natureza: t.governance?.economic_classification ?? "",
          subnatureza: t.raw?.type ?? "",
          // Preferência: account_name (nome legível), fallback para account_external_id
          account: t.raw?.account_name || t.raw?.account_external_id || "—",
          amount: t.raw?.amount ?? 0,
          // campos extras para cor/filtro
          economic_classification: t.governance?.economic_classification ?? "",
          governance_status: t.governance?.governance_status ?? "PENDING",
        }));

        setTransactions(mappedItems);
        setTotal(data?.total ?? mappedItems.length);
        setTotalPages(Math.ceil((data?.total ?? mappedItems.length) / limit));

        // KPIs com os mesmos filtros da tabela — refletem exatamente o que está visível
        const summaryParams = new URLSearchParams({
          start_date: startDate,
          end_date: endDate,
        });
        if (natureza !== "all") summaryParams.set("economic_classification", natureza);
        if (category !== "all") summaryParams.set("category", category);

        const summaryData = await fetchFromAPI<GovernanceSummary>(
          `/governance/summary?${summaryParams.toString()}`
        );
        if (active && summaryData) {
          setGovSummary(summaryData);
          setSummary({
            income:  summaryData.total_entrada,
            expense: summaryData.total_saida,
            balance: summaryData.resultado,
          });
        }

        if (!data) {
          setError("Não foi possível carregar o extrato.");
        }
      } catch (err) {
        if (!active) return;
        console.error("[transactions] loadData error:", err);
        setTransactions([]);
        setTotal(0);
        setTotalPages(0);
        setSummary({ income: 0, expense: 0, balance: 0 });
        setError("Não foi possível carregar o extrato.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadData();

    return () => {
      active = false;
    };
  }, [account, category, endDate, limit, natureza, offset, startDate]);

  // Deduplica contas
  const accountOptions = [...new Set(catalog.accounts)];
  // Categorias dinâmicas das transações carregadas
  const categoryOptions = useMemo(() => {
    const cats = transactions.map(t => t.category).filter(Boolean);
    return [...new Set(cats)].sort();
  }, [transactions]);

  // Tipos simplificados: ENTRADA / SAIDA (mapeados de economic_classification)
  const DIRECTION_OPTIONS = [
    { value: "ENTRADA", label: "Entrada" },
    { value: "SAIDA",   label: "Saída"  },
  ];

  const filteredTransactions = useMemo(() => {
    const term = normalizeText(searchTerm);
    return transactions.filter((tx) => {
      const matchesSearch =
        !term ||
        [tx.description, tx.category, tx.natureza, tx.subnatureza, tx.account, tx.date]
          .join(" ")
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .toUpperCase()
          .includes(term);

      return matchesSearch;
    });
  }, [searchTerm, transactions]);

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

  const handleStartDateChange = (value: string) => {
    setStartDate(value);
    setOffset(0);
  };

  const handleEndDateChange = (value: string) => {
    setEndDate(value);
    setOffset(0);
  };

  const handleAccountChange = (value: string) => {
    setAccount(value);
    setOffset(0);
  };

  const handleCategoryChange = (value: string) => {
    setCategory(value);
    setOffset(0);
  };

  const handleNaturezaChange = (value: string) => {
    setNatureza(value);
    setOffset(0);
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

  void openReclassification;

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
    <PageLayout title="Transacoes" subtitle="Extrato classificado com filtros e indicadores de governanca." hideTitle={true}>

      {/* KPI strip — valores refletem o filtro ativo */}
      <div className="mb-6 rounded-3xl border border-white/10 bg-white/5 p-5 shadow-2xl shadow-black/20 backdrop-blur">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4 mb-4">
          <article className="rounded-3xl border border-emerald-500/20 bg-black/20 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Entradas</p>
            <div className="mt-3 flex items-end justify-between gap-3">
              <p className="text-2xl font-semibold tracking-tight text-emerald-300">
                {formatCurrency(summary.income)}
              </p>
              <TrendingUp className="size-5 text-emerald-300" />
            </div>
          </article>
          <article className="rounded-3xl border border-rose-500/20 bg-black/20 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Saídas</p>
            <div className="mt-3 flex items-end justify-between gap-3">
              <p className="text-2xl font-semibold tracking-tight text-rose-300">
                {formatCurrency(summary.expense)}
              </p>
              <TrendingDown className="size-5 text-rose-300" />
            </div>
          </article>
          <article className={`rounded-3xl border ${summary.balance >= 0 ? "border-cyan-500/20" : "border-rose-500/20"} bg-black/20 p-4`}>
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Resultado</p>
            <div className="mt-3 flex items-end justify-between gap-3">
              <p className={`text-2xl font-semibold tracking-tight ${summary.balance >= 0 ? "text-cyan-300" : "text-rose-300"}`}>
                {formatCurrency(summary.balance)}
              </p>
              <Scale className="size-5 text-cyan-300" />
            </div>
          </article>
          <article className="rounded-3xl border border-amber-500/20 bg-black/20 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Pendentes</p>
            <div className="mt-3 flex items-end justify-between gap-3">
              <p className="text-2xl font-semibold tracking-tight text-amber-300">
                {govSummary?.pending_count ?? 0}
              </p>
              <AlertTriangle className="size-5 text-amber-300" />
            </div>
          </article>
        </div>
        {(govSummary?.pending_count ?? 0) > 0 && (
          <div className="flex items-center justify-between rounded-2xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
            <span className="text-xs text-amber-300">
              <strong>{govSummary!.pending_count}</strong> transações aguardam classificação em Governança
            </span>
            <Link href="/governance/classify" className="text-xs font-semibold text-amber-400 hover:text-amber-300 transition-colors">
              Classificar agora &rarr;
            </Link>
          </div>
        )}
      </div>

      <section className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-2xl shadow-black/20 backdrop-blur">
        {/* Linha de contagem + pesquisa */}
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between mb-5">
          <label className="flex flex-1 items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-zinc-400">
            <Search className="size-4" />
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Pesquisar por descrição, categoria, conta..."
              className="w-full bg-transparent text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
            />
          </label>
          <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-300 whitespace-nowrap">
            <ArrowRightLeft className="size-4 text-cyan-300" />
            <span>{filteredTransactions.length} movimentações</span>
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
              value={startDate}
              onChange={(event) => handleStartDateChange(event.target.value)}
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
              value={endDate}
              onChange={(event) => handleEndDateChange(event.target.value)}
              className="w-full bg-transparent text-zinc-100 outline-none"
            />
          </label>

          <label className="space-y-2 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-400">
            <span className="text-xs uppercase tracking-[0.2em] text-zinc-500">Conta</span>
            <select
              value={account}
              onChange={(event) => handleAccountChange(event.target.value)}
              className="w-full bg-transparent text-zinc-100 outline-none [&>option]:bg-zinc-950 [&>option]:text-zinc-100"
            >
              <option value="all">Todas as contas</option>
              {accountOptions.map((accountOption) => (
                <option key={accountOption} value={accountOption}>
                  {accountOption}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-400">
            <span className="text-xs uppercase tracking-[0.2em] text-zinc-500">Categoria</span>
            <select
              value={category}
              onChange={(event) => handleCategoryChange(event.target.value)}
              className="w-full bg-transparent text-zinc-100 outline-none [&>option]:bg-zinc-950 [&>option]:text-zinc-100"
            >
              <option value="all">Todas as categorias</option>
              {categoryOptions.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </label>
        </div>

        {/* Filtro Tipo - simplificado: Entrada / Saida */}
        <div className="mt-3 flex flex-wrap items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-400">
          <span className="text-xs uppercase tracking-[0.2em] text-zinc-500">Tipo</span>
          <button
            onClick={() => handleNaturezaChange("all")}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              natureza === "all" ? "bg-zinc-700 text-white" : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Todos
          </button>
          <button
            onClick={() => handleNaturezaChange("ENTRADA")}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              natureza === "ENTRADA" ? "bg-emerald-900 text-emerald-300 border border-emerald-700" : "text-zinc-400 hover:text-emerald-400"
            }`}
          >
            Entrada
          </button>
          <button
            onClick={() => handleNaturezaChange("SAIDA")}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              natureza === "SAIDA" ? "bg-rose-900 text-rose-300 border border-rose-700" : "text-zinc-400 hover:text-rose-400"
            }`}
          >
            Saída
          </button>
          <div className="ml-auto flex items-center gap-2 text-xs text-zinc-500">
            <Filter className="size-3" />
            {filteredTransactions.length} resultado{filteredTransactions.length !== 1 ? "s" : ""}
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

        <div className="mt-4 overflow-hidden rounded-3xl border border-white/10">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="bg-black/25 text-left text-xs uppercase tracking-[0.18em] text-zinc-500">
                <tr>
                  <th className="px-4 py-3 w-[35%]">Descrição</th>
                  <th className="px-4 py-3 w-[20%]">Categoria</th>
                  <th className="px-4 py-3 w-[8%]">Tipo</th>
                  <th className="px-4 py-3 w-[15%]">Conta</th>
                  <th className="px-4 py-3 w-[12%]">Data</th>
                  <th className="px-4 py-3 w-[10%] text-right">Valor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10 bg-white/5">
                {loading ? (
                  <tr>
                    <td className="px-4 py-6 text-zinc-400" colSpan={5}>
                      A carregar extrato...
                    </td>
                  </tr>
                ) : filteredTransactions.length === 0 ? (
                  <tr>
                    <td className="px-4 py-6 text-zinc-400" colSpan={5}>
                      Nenhuma transação encontrada.
                    </td>
                  </tr>
                ) : (
                  filteredTransactions.map((tx) => {
                    const amountValue = Number(tx.amount) || 0;
                    const amountAbs = Math.abs(amountValue);

                    // categoryLabel — formata para display
                    const categoryLabel = (tx.category ?? "")
                      .replace(/_/g, " ")
                      .toLowerCase()
                      .replace(/\b\w/g, (c) => c.toUpperCase());

                    // Formata data DD/MM/YY — guarda contra null/undefined
                    const rawDate = tx.date ?? "";
                    const dateParts = rawDate.split("-");
                    const formattedDate =
                      dateParts.length === 3
                        ? `${dateParts[2]}/${dateParts[1]}/${dateParts[0].slice(2)}`
                        : rawDate || "—";

                    // Cor/badge pela classification de governança
                    const ec = (tx as any).economic_classification as string;
                    const isPending = (tx as any).governance_status === "PENDING";
                    const isEntrada = ec === "ENTRADA";
                    const isSaida   = ec === "SAIDA";
                    const isIgnorar = ec === "IGNORAR";

                    const valueColorClass = isEntrada ? "text-[#4ecf98]"
                      : isSaida            ? "text-[#e97070]"
                      : isPending          ? "text-amber-400"
                      : "text-zinc-400";
                    const valuePrefix = isEntrada ? "+" : "";
                    const typeBadgeLabel = isEntrada ? "Entrada"
                      : isSaida  ? "Saída"
                      : isIgnorar ? "Ignorar"
                      : isPending ? "Pendente" : "—";
                    const typeBadgeCls = isEntrada
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-700/30"
                      : isSaida
                      ? "bg-rose-500/10 text-rose-400 border border-rose-700/30"
                      : isIgnorar
                      ? "bg-zinc-500/10 text-zinc-400 border border-zinc-700/30"
                      : "bg-amber-500/10 text-amber-400 border border-amber-700/30";

                    return (
                      <tr key={tx.id} className="group transition-colors hover:bg-white/5">
                        {/* Descrição */}
                        <td className="px-4 py-4">
                          <p className="truncate max-w-xs text-sm text-white">{tx.description}</p>
                          <p className="text-[11px] text-zinc-600 mt-0.5 truncate">{tx.subnatureza}</p>
                        </td>
                        {/* Categoria */}
                        <td className="px-4 py-4">
                          <span className="text-sm text-zinc-300">{categoryLabel || "—"}</span>
                        </td>
                        {/* Tipo badge compacto */}
                        <td className="px-4 py-4">
                          <span className={`inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-full ${typeBadgeCls}`}>
                            {typeBadgeLabel}
                          </span>
                        </td>
                        {/* Conta */}
                        <td className="px-4 py-4 text-sm text-neutral-500">{tx.account}</td>
                        {/* Data */}
                        <td className="px-4 py-4 text-sm text-neutral-500 whitespace-nowrap">{formattedDate}</td>
                        {/* Valor */}
                        <td className="px-4 py-4 text-right">
                          <span className={`text-sm font-medium ${valueColorClass}`}>
                            {valuePrefix}{formatCurrency(amountAbs)}
                          </span>
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
            <span>Página {currentPage}</span>
            <span className="text-zinc-600">|</span>
            <span>
              {rangeStart} a {rangeEnd}
            </span>
            <span className="text-zinc-600">|</span>
            <span>{total} no total</span>
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

export default function TransactionsPage() {
  return (
    <Suspense fallback={<div className="p-6 text-sm text-zinc-400">A carregar extrato...</div>}>
      <TransactionsPageBody />
    </Suspense>
  );
}