"use client";

import { useState } from "react";
import { ClipboardPaste, Loader2, FileUp, ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { PageLayout } from "@/components/layout/PageLayout";
import { fetchFromAPI } from "@/lib/api";

interface ImportResponse {
  run_id: string;
  preview: Record<string, unknown>;
}

interface MyProfitPreview {
  detected_file_type?: string;
  total_rows?: number;
  period_start?: string;
  period_end?: string;
  tickers_found?: string[];
  errors?: string[];
  run_id?: string;
}

export default function GovernanceUploadPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"MYPROFIT" | "PIERRE">("MYPROFIT");
  
  // States para Pierre
  const [pierreText, setPierreText] = useState("");
  const [pierreSubmitting, setPierreSubmitting] = useState(false);
  const [pierreMessage, setPierreMessage] = useState<string | null>(null);
  const [pierreError, setPierreError] = useState<string | null>(null);

  // States para MyProfit
  const [myprofitFile, setMyprofitFile] = useState<File | null>(null);
  const [myprofitSubmitting, setMyprofitSubmitting] = useState(false);
  const [myprofitPreview, setMyprofitPreview] = useState<MyProfitPreview | null>(null);
  const [myprofitError, setMyprofitError] = useState<string | null>(null);
  
  // Submit Pierre
  async function handlePierreSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pierreSubmitting || pierreText.trim().length === 0) return;

    setPierreSubmitting(true);
    setPierreMessage(null);
    setPierreError(null);

    try {
      const response = await fetchFromAPI<ImportResponse>("/governance/import-pierre", {
        method: "POST",
        body: JSON.stringify({ raw_text: pierreText }),
      });

      if (!response) {
        setPierreError("Nao foi possivel enviar o CSV.");
        return;
      }

      setPierreMessage(`Importacao concluida. Run ID: ${response.run_id}`);
      setPierreText("");
      router.push(`/governance/review?run=${response.run_id}`);
    } catch (err) {
      setPierreError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setPierreSubmitting(false);
    }
  }

  // File drop handling
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setMyprofitFile(e.dataTransfer.files[0]);
      setMyprofitPreview(null);
      setMyprofitError(null);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setMyprofitFile(e.target.files[0]);
      setMyprofitPreview(null);
      setMyprofitError(null);
    }
  };

  // Submit MyProfit
  async function handleMyprofitSubmit() {
    if (!myprofitFile || myprofitSubmitting) return;

    setMyprofitSubmitting(true);
    setMyprofitError(null);

    try {
      const text = await myprofitFile.text();
      const payload = {
        raw_text: text,
        file_name: myprofitFile.name
      };

      const response = await fetchFromAPI<ImportResponse>("/governance/import-myprofit", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (!response) {
        setMyprofitError("Não foi possível processar o arquivo MyProfit.");
        return;
      }

      setMyprofitPreview({ ...(response.preview as MyProfitPreview), run_id: response.run_id });
    } catch (err) {
      setMyprofitError(err instanceof Error ? err.message : "Erro ao processar MyProfit");
    } finally {
      setMyprofitSubmitting(false);
    }
  }

  return (
    <PageLayout 
      title="Nova Importação" 
      subtitle="Importe extratos do Pierre ou MyProfit" 
      hideTitle={true}
      breadcrumb={
        <div className="text-sm font-medium text-zinc-500 flex items-center gap-2">
          <Link href="/governance" className="hover:text-white transition-colors">Governança</Link>
          <span>/</span>
          <span className="text-zinc-300">Importações</span>
        </div>
      }
    >
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link 
          href="/governance"
          className="inline-flex items-center text-sm font-medium text-zinc-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="mr-2 w-4 h-4" />
          Voltar para Dashboard
        </Link>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab("MYPROFIT")}
            className={`rounded-full px-6 py-2 text-sm font-medium transition ${
              activeTab === "MYPROFIT" ? "bg-emerald-600 text-white" : "bg-white/5 text-zinc-400 hover:text-white"
            }`}
          >
            MyProfit
          </button>
          <button
            onClick={() => setActiveTab("PIERRE")}
            className={`rounded-full px-6 py-2 text-sm font-medium transition ${
              activeTab === "PIERRE" ? "bg-emerald-600 text-white" : "bg-white/5 text-zinc-400 hover:text-white"
            }`}
          >
            Pierre
          </button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto w-full">
        {activeTab === "PIERRE" && (
          <section className="rounded-md border border-slate-800 bg-slate-900/50 p-8 shadow-sm">
            <div className="mb-6 flex items-center gap-3">
              <ClipboardPaste className="h-5 w-5 text-emerald-300" />
              <h2 className="text-xl font-semibold text-zinc-100">Colar CSV do Pierre</h2>
            </div>
            <form onSubmit={handlePierreSubmit} className="space-y-4">
              <textarea
                value={pierreText}
                onChange={(e) => setPierreText(e.target.value)}
                rows={12}
                placeholder="Cole aqui as novas linhas do Extrato Pierre Processado.csv"
                className="w-full rounded-md border border-slate-800 bg-slate-900 p-4 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-500 focus:border-emerald-400/50"
              />
              <Button
                variant="admin"
                type="submit"
                disabled={pierreSubmitting || pierreText.trim().length === 0}
                className="w-full"
              >
                {pierreSubmitting ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : null}
                Processar Dados Pierre
              </Button>
            </form>
            {pierreMessage && <p className="mt-4 text-sm text-emerald-300">{pierreMessage}</p>}
            {pierreError && <p className="mt-4 text-sm text-red-400">{pierreError}</p>}
          </section>
        )}

        {activeTab === "MYPROFIT" && (
          <section className="rounded-md border border-slate-800 bg-slate-900/50 p-8 shadow-sm">
            <div className="mb-6 flex items-center gap-3">
              <FileUp className="h-5 w-5 text-emerald-300" />
              <h2 className="text-xl font-semibold text-zinc-100">Upload de Arquivo (MyProfit)</h2>
            </div>

            {!myprofitPreview ? (
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className="flex flex-col items-center justify-center rounded-md border-2 border-dashed border-slate-800 bg-slate-900/50 p-16 text-center transition hover:border-emerald-500/50 cursor-pointer"
                onClick={() => document.getElementById("fileInput")?.click()}
              >
                <FileUp className="mb-4 h-10 w-10 text-emerald-500/50" />
                <p className="text-base font-medium text-zinc-300">Arraste o arquivo CSV aqui</p>
                <p className="mt-2 text-sm text-zinc-500">Ou clique para procurar em seu computador</p>
                <input id="fileInput" type="file" accept=".csv" className="hidden" onChange={handleFileSelect} />
              </div>
            ) : null}

            {myprofitFile && !myprofitPreview && (
              <div className="mt-6 flex items-center justify-between rounded-md border border-emerald-500/20 bg-emerald-500/5 p-4">
                <div className="flex items-center gap-3">
                  <FileUp className="h-5 w-5 text-emerald-400" />
                  <span className="text-sm font-medium text-zinc-200">{myprofitFile.name}</span>
                </div>
                <Button variant="admin" onClick={handleMyprofitSubmit} disabled={myprofitSubmitting}>
                  {myprofitSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Validar Arquivo"}
                </Button>
              </div>
            )}

            {myprofitError && (
              <div className="mt-6 rounded-md border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400">
                {myprofitError}
              </div>
            )}

            {myprofitPreview && (
              <div className="mt-6 space-y-6 rounded-md border border-slate-800 bg-slate-900 p-6">
                <div className="border-b border-slate-800 pb-4">
                  <h3 className="text-lg font-medium text-zinc-100">Resultado da Validação</h3>
                  <p className="text-sm text-zinc-400 mt-1">Nenhum dado foi gravado definitivamente ainda.</p>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                  <div className="rounded-md border border-slate-800 bg-slate-900/50 p-4">
                    <span className="block text-zinc-500 mb-1">Arquivo Detectado</span>
                    <span className="font-medium text-zinc-200">{myprofitPreview.detected_file_type}</span>
                  </div>
                  <div className="rounded-md border border-slate-800 bg-slate-900/50 p-4">
                    <span className="block text-zinc-500 mb-1">Total de Linhas</span>
                    <span className="font-medium text-zinc-200">{myprofitPreview.total_rows}</span>
                  </div>
                  <div className="rounded-md border border-slate-800 bg-slate-900/50 p-4">
                    <span className="block text-zinc-500 mb-1">Período</span>
                    <span className="font-medium text-zinc-200">{myprofitPreview.period_start || '-'} a {myprofitPreview.period_end || '-'}</span>
                  </div>
                </div>
                
                {myprofitPreview.tickers_found && myprofitPreview.tickers_found.length > 0 && (
                  <div>
                    <span className="block text-sm text-zinc-500 mb-2">Tickers Identificados:</span>
                    <div className="flex flex-wrap gap-2">
                      {myprofitPreview.tickers_found.map((t: string) => (
                        <span key={t} className="rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-zinc-300">{t}</span>
                      ))}
                    </div>
                  </div>
                )}

                {myprofitPreview.errors && myprofitPreview.errors.length > 0 && (
                  <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                    <strong className="text-sm text-red-400 block mb-2">Atenção - Erros Encontrados:</strong>
                    <ul className="list-inside list-disc text-sm text-red-300/80 space-y-1">
                      {myprofitPreview.errors.map((e: string, i: number) => <li key={i}>{e}</li>)}
                    </ul>
                  </div>
                )}

                <div className="mt-8 flex gap-4">
                  <Button 
                    onClick={() => { setMyprofitFile(null); setMyprofitPreview(null); }} 
                    variant="admin-outline" 
                    className="flex-1 text-red-400 border-red-500/30 hover:bg-red-500/10 hover:text-red-300 h-12"
                  >
                    Descartar Arquivo
                  </Button>
                  <Button 
                    variant="admin"
                    onClick={() => router.push(`/governance/review?run=${myprofitPreview.run_id}`)} 
                    className="flex-1 bg-emerald-600 hover:bg-emerald-500 h-12 text-base"
                  >
                    Ir para Revisão Completa
                  </Button>
                </div>
              </div>
            )}
          </section>
        )}
      </div>
    </PageLayout>
  );
}
