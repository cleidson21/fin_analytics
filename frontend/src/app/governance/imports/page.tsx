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

interface PreviewData {
  detected_file_type?: string;
  total_rows?: number;
  valid_rows?: number;
  invalid_rows?: number;
  period_start?: string;
  period_end?: string;
  tickers_found?: string[];
  errors?: string[];
  run_id?: string;
}

export default function GovernanceUploadPage() {
  const router = useRouter();
  const [sourceType, setSourceType] = useState<string>("MYPROFIT_PROVENTOS");
  
  const [rawText, setRawText] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const isPasteMode = sourceType === "PIERRE";

  // File drop handling
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
      setPreview(null);
      setErrorMsg(null);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setPreview(null);
      setErrorMsg(null);
    }
  };

  async function handleSubmit(event?: React.FormEvent) {
    if (event) event.preventDefault();
    
    if (isSubmitting) return;
    if (isPasteMode && rawText.trim().length === 0) return;
    if (!isPasteMode && !selectedFile) return;

    setIsSubmitting(true);
    setErrorMsg(null);
    setPreview(null);

    try {
      const formData = new FormData();
      formData.append("source_type", sourceType);
      
      if (isPasteMode) {
        formData.append("raw_text", rawText);
      } else if (selectedFile) {
        formData.append("file", selectedFile);
      }

      const response = await fetchFromAPI<ImportResponse>("/governance/imports/upload", {
        method: "POST",
        body: formData,
      });

      if (!response) {
        setErrorMsg("Não foi possível processar o arquivo.");
        return;
      }

      setPreview({ ...(response.preview as PreviewData), run_id: response.run_id });
      
      // If it's paste mode, we might just want to show preview or redirect
      if (isPasteMode) {
        router.push(`/governance/review?run=${response.run_id}`);
      }
      
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <PageLayout 
      title="Nova Importação" 
      subtitle="Selecione a origem e envie os dados" 
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
      </div>

      <div className="max-w-4xl mx-auto w-full">
        <section className="rounded-md border border-slate-800 bg-slate-900/50 p-8 shadow-sm">
          <div className="mb-8">
            <label className="block text-sm font-medium text-zinc-400 mb-2">Origem dos Dados</label>
            <select
              value={sourceType}
              onChange={(e) => {
                setSourceType(e.target.value);
                setPreview(null);
                setErrorMsg(null);
                setSelectedFile(null);
                setRawText("");
              }}
              className="w-full sm:w-1/2 rounded-md border border-slate-800 bg-slate-900 p-3 text-sm text-zinc-100 outline-none transition focus:border-emerald-400/50"
            >
              <option value="MYPROFIT_PROVENTOS">MyProfit - Proventos (CSV)</option>
              <option value="MYPROFIT_EVOLUCAO">MyProfit - Evolução (CSV)</option>
              <option value="NUBANK_CONTA">Nubank - Conta Corrente (CSV)</option>
              <option value="NUBANK_FATURA">Nubank - Fatura do Cartão (CSV)</option>
              <option value="B3">B3 - Extrato Área do Investidor (XLSX/CSV)</option>
              <option value="PIERRE">Pierre - Extrato Processado (Texto)</option>
            </select>
          </div>

          {isPasteMode ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="mb-6 flex items-center gap-3">
                <ClipboardPaste className="h-5 w-5 text-emerald-300" />
                <h2 className="text-xl font-semibold text-zinc-100">Colar Extrato</h2>
              </div>
              <textarea
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                rows={12}
                placeholder="Cole aqui as linhas copiadas..."
                className="w-full rounded-md border border-slate-800 bg-slate-900 p-4 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-500 focus:border-emerald-400/50"
              />
              <Button
                variant="admin"
                type="submit"
                disabled={isSubmitting || rawText.trim().length === 0}
                className="w-full"
              >
                {isSubmitting ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : null}
                Processar e Importar
              </Button>
            </form>
          ) : (
            <div>
              <div className="mb-6 flex items-center gap-3">
                <FileUp className="h-5 w-5 text-emerald-300" />
                <h2 className="text-xl font-semibold text-zinc-100">Upload de Arquivo</h2>
              </div>

              {!preview ? (
                <div
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                  className="flex flex-col items-center justify-center rounded-md border-2 border-dashed border-slate-800 bg-slate-900/50 p-16 text-center transition hover:border-emerald-500/50 cursor-pointer"
                  onClick={() => document.getElementById("fileInput")?.click()}
                >
                  <FileUp className="mb-4 h-10 w-10 text-emerald-500/50" />
                  <p className="text-base font-medium text-zinc-300">Arraste o arquivo CSV aqui</p>
                  <p className="mt-2 text-sm text-zinc-500">Ou clique para procurar em seu computador</p>
                  <input id="fileInput" type="file" accept=".csv,.txt,.xlsx" className="hidden" onChange={handleFileSelect} />
                </div>
              ) : null}

              {selectedFile && !preview && (
                <div className="mt-6 flex flex-col sm:flex-row sm:items-center justify-between rounded-md border border-emerald-500/20 bg-emerald-500/5 p-4 gap-4">
                  <div className="flex items-center gap-3">
                    <FileUp className="h-5 w-5 text-emerald-400" />
                    <span className="text-sm font-medium text-zinc-200">{selectedFile.name}</span>
                  </div>
                  <Button variant="admin" onClick={() => handleSubmit()} disabled={isSubmitting}>
                    {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Validar Arquivo"}
                  </Button>
                </div>
              )}
            </div>
          )}

          {errorMsg && (
            <div className="mt-6 rounded-md border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400">
              {errorMsg}
            </div>
          )}

          {preview && !isPasteMode && (
            <div className="mt-6 space-y-6 rounded-md border border-slate-800 bg-slate-900 p-6">
              <div className="border-b border-slate-800 pb-4">
                <h3 className="text-lg font-medium text-zinc-100">Resultado da Validação</h3>
                <p className="text-sm text-zinc-400 mt-1">Verifique os dados extraídos antes de prosseguir.</p>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                <div className="rounded-md border border-slate-800 bg-slate-900/50 p-4">
                  <span className="block text-zinc-500 mb-1">Total de Linhas Encontradas</span>
                  <span className="font-medium text-zinc-200">{preview.total_rows ?? 0}</span>
                </div>
                <div className="rounded-md border border-slate-800 bg-slate-900/50 p-4">
                  <span className="block text-zinc-500 mb-1">Linhas Válidas</span>
                  <span className="font-medium text-zinc-200">{preview.valid_rows ?? 0}</span>
                </div>
                <div className="rounded-md border border-slate-800 bg-slate-900/50 p-4">
                  <span className="block text-zinc-500 mb-1">Tipo de Arquivo</span>
                  <span className="font-medium text-zinc-200">{preview.detected_file_type || '-'}</span>
                </div>
              </div>
              
              {preview.errors && preview.errors.length > 0 && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                  <strong className="text-sm text-red-400 block mb-2">Erros e Avisos:</strong>
                  <ul className="list-inside list-disc text-sm text-red-300/80 space-y-1">
                    {preview.errors.map((e: string, i: number) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}

              <div className="mt-8 flex gap-4">
                <Button 
                  onClick={() => { setSelectedFile(null); setPreview(null); }} 
                  variant="admin-outline" 
                  className="flex-1 text-red-400 border-red-500/30 hover:bg-red-500/10 hover:text-red-300 h-12"
                >
                  Descartar Arquivo
                </Button>
                <Button 
                  variant="admin"
                  onClick={() => router.push(`/governance/review?run=${preview.run_id}`)} 
                  className="flex-1 bg-emerald-600 hover:bg-emerald-500 h-12 text-base"
                >
                  Continuar para Revisão
                </Button>
              </div>
            </div>
          )}
        </section>
      </div>
    </PageLayout>
  );
}
