"use client";

import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, ClipboardPaste, Loader2, RefreshCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";

interface ImportStatusItem {
  source_line_no: number;
  description: string;
}

interface ImportStatusResponse {
  last_items: ImportStatusItem[];
  next_line: number;
}

interface ImportResponse {
  run_id: string;
  preview: {
    items: Array<{
      date: string;
      description: string;
      amount: number;
      status: string;
    }>;
  };
}

export const dynamic = "force-dynamic";

export default function GovernanceImportPage() {
  const [status, setStatus] = useState<ImportStatusResponse | null>(null);
  const [rawText, setRawText] = useState("");
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadStatus() {
    setLoadingStatus(true);
    const data = await fetchFromAPI<ImportStatusResponse>("/governance/import-status");
    setStatus(data);
    setLoadingStatus(false);
  }

  useEffect(() => {
    loadStatus();
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting || rawText.trim().length === 0) {
      return;
    }

    setSubmitting(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetchFromAPI<ImportResponse>("/governance/import-pierre", {
        method: "POST",
        body: JSON.stringify({ raw_text: rawText }),
      });

      if (!response) {
        setError("Nao foi possivel enviar o CSV. Verifique o conteudo colado e tente novamente.");
        return;
      }

      setMessage(`Importacao concluida. Run ${response.run_id} com ${response.preview.items.length} itens de preview.`);
      setRawText("");
      await loadStatus();
    } finally {
      setSubmitting(false);
    }
  }

  const lastItems = status?.last_items ?? [];

  return (
    <PageLayout title="Importacao Pierre" subtitle="Cole apenas linhas novas do CSV. O operador e unico." hideTitle={true}>
      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-[0_20px_80px_rgba(0,0,0,0.25)]">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 text-amber-300" />
          <div className="space-y-2">
            <p className="text-sm uppercase tracking-[0.2em] text-zinc-400">Estado operacional</p>
            {loadingStatus ? (
              <p className="text-sm text-zinc-300">A carregar ultimos itens importados...</p>
            ) : (
              <>
                <p className="text-sm text-zinc-100">
                  Ultimos itens importados:{" "}
                  {lastItems.length > 0
                    ? lastItems.map((item) => `${item.source_line_no} - ${item.description}`).join(" | ")
                    : "Nenhum item encontrado."}
                </p>
                <p className="text-lg font-semibold text-emerald-300">
                  Proxima linha esperada: {status?.next_line ?? 1}
                </p>
              </>
            )}
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-[0_20px_80px_rgba(0,0,0,0.25)]">
        <div className="mb-4 flex items-center gap-2">
          <ClipboardPaste className="h-4 w-4 text-emerald-300" />
          <h2 className="text-lg font-semibold text-white">Colar CSV do Pierre</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            value={rawText}
            onChange={(event) => setRawText(event.target.value)}
            rows={16}
            placeholder={"Cole aqui as novas linhas do Extrato Pierre Processado.csv"}
            className="min-h-72 w-full rounded-2xl border border-white/10 bg-black/30 p-4 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-500 focus:border-emerald-400/50"
          />

          <div className="flex flex-wrap items-center gap-3">
            <Button
              type="submit"
              disabled={submitting || rawText.trim().length === 0}
              className="gap-2 bg-emerald-600 text-white shadow-lg shadow-emerald-950/30 hover:bg-emerald-500 hover:text-white"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
              {submitting ? "A importar..." : "Importar Dados"}
            </Button>

            <Button variant="outline" type="button" onClick={loadStatus} disabled={loadingStatus || submitting} className="gap-2">
              <RefreshCcw className="h-4 w-4" />
              Recarregar estado
            </Button>
          </div>
        </form>

        {message ? (
          <p className="mt-4 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">
            {message}
          </p>
        ) : null}

        {error ? (
          <p className="mt-4 rounded-2xl border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm text-red-200">
            {error}
          </p>
        ) : null}
      </section>
    </PageLayout>
  );
}