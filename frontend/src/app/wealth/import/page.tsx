"use client";

import { useState, useRef, useMemo, useEffect } from "react";
import { WealthKpiCard } from "@/components/wealth/ui/WealthKpiCard";
import { WealthChartCard } from "@/components/wealth/ui/WealthChartCard";
import { WealthTable } from "@/components/wealth/ui/WealthTable";
import { formatCurrency, colorForValue } from "@/lib/utils";
import { UploadCloud, FileJson, FileSpreadsheet, CheckCircle, AlertTriangle, AlertCircle, Clock, Save, Copy } from "lucide-react";
import { fetchFromAPI } from "@/lib/api";

interface ImportLog {
  id: string;
  user_id: string;
  created_at: string;
  filename: string;
  file_type: string;
  file_size: number;
  checksum: string;
  parser: string;
  rows_read: number;
  rows_imported: number;
  rows_duplicated: number;
  rows_failed: number;
  processing_time_ms: number;
  status: string;
  error_message?: string;
  metadata_json?: string;
}

export default function ImportPage() {
  const [history, setHistory] = useState<ImportLog[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isErrorHistory, setIsErrorHistory] = useState(false);

  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadType, setUploadType] = useState<"CEI" | "OPEN_FINANCE">("CEI");
  const [selectedLog, setSelectedLog] = useState<ImportLog | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchHistory = async () => {
    setIsLoadingHistory(true);
    setIsErrorHistory(false);
    try {
      const res = await fetchFromAPI<ImportLog[]>("/investments/import/history").catch(() => []);
      if (res && Array.isArray(res)) {
        setHistory(res);
      }
    } catch {
      setIsErrorHistory(true);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(10);
    
    const formData = new FormData();
    formData.append("file", file);

    const endpoint = uploadType === "CEI" ? "/investments/import/cei" : "/investments/import/open-finance";

    try {
      // Basic progress simulation for UI while it uploads
      const interval = setInterval(() => {
        setUploadProgress(p => p < 90 ? p + 10 : p);
      }, 300);

      const response = await fetchFromAPI<any>(endpoint, {
        method: "POST",
        body: formData,
        // we don't set Content-Type header here, fetch automatically sets it for FormData
      });

      clearInterval(interval);
      setUploadProgress(100);
      
      // Update history table with the new result
      if (response) {
        setHistory(prev => [response, ...prev]);
      }
    } catch (e) {
      console.error("Upload failed", e);
      setUploadProgress(0);
    } finally {
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
      }, 500);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (isUploading) return;
    
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      uploadFile(droppedFiles[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  };

  // Aggregated KPIs
  const { totalFiles, totalTrades, totalDuplicates, totalErrors } = useMemo(() => {
    let files = history.length;
    let trades = 0;
    let dups = 0;
    let errs = 0;
    
    history.forEach(h => {
      trades += h.rows_persisted;
      dups += h.duplicates_detected;
      errs += h.errors.length;
    });

    return { totalFiles: files, totalTrades: trades, totalDuplicates: dups, totalErrors: errs };
  }, [history]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);

    // Simulated progress
    const interval = setInterval(() => {
      setUploadProgress(p => {
        if (p >= 90) {
          clearInterval(interval);
          return 90;
        }
        return p + 10;
      });
    }, 200);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const endpoint = uploadType === "CEI" ? "/investments/import/cei" : "/investments/import/open-finance";
      // We don't use fetchFromAPI because it's for JSON by default, we'll use basic fetch
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
      
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers,
        body: formData,
      });

      clearInterval(interval);
      setUploadProgress(100);
      
      if (res.ok) {
        fetchHistory();
      } else {
        throw new Error("Upload failed");
      }
    } catch (err) {
      clearInterval(interval);
      setUploadProgress(0);
      // Simulate toast error
    } finally {
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }, 1000);
    }
  };

  const onDragOver = (e: React.DragEvent) => e.preventDefault();
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (isUploading) return;
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    
    // Simulate setting file and triggering upload
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    if (fileInputRef.current) {
      fileInputRef.current.files = dataTransfer.files;
      // manual trigger
      handleFileUpload({ target: fileInputRef.current } as any);
    }
  };

  const { totalFiles, totalTrades, totalDuplicates, totalErrors } = useMemo(() => {
    let files = history.length;
    let trades = 0;
    let dups = 0;
    let errs = 0;
    
    history.forEach(h => {
      trades += h.rows_imported;
      dups += h.rows_duplicated;
      errs += h.rows_failed;
    });

    return { totalFiles: files, totalTrades: trades, totalDuplicates: dups, totalErrors: errs };
  }, [history]);

  return (
    <div className="space-y-6">
      
      {/* Primeira Seção: KPIs */}
      <h2 className="text-sm font-semibold text-white/80 uppercase tracking-wider mb-2">Resumo de Ingestão</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <WealthKpiCard
          title="Arquivos Importados"
          value={isLoadingHistory ? "..." : totalFiles.toString()}
          icon={Save}
          iconBgColor="bg-[#7EB8F7]/10"
          iconColor="text-[#7EB8F7]"
        />
        <WealthKpiCard
          title="Registros Processados"
          value={isLoadingHistory ? "..." : totalTrades.toString()}
          icon={CheckCircle}
          iconBgColor="bg-[#4ecf98]/10"
          iconColor="text-[#4ecf98]"
        />
        <WealthKpiCard
          title="Duplicidades (Hashes)"
          value={isLoadingHistory ? "..." : totalDuplicates.toString()}
          icon={Copy}
          iconBgColor="bg-[#f5a623]/10"
          iconColor="text-[#f5a623]"
        />
        <WealthKpiCard
          title="Erros Críticos"
          value={<span className={totalErrors > 0 ? "text-[#e97070]" : "text-white"}>{isLoadingHistory ? "..." : totalErrors.toString()}</span>}
          icon={AlertTriangle}
          iconBgColor="bg-[#e97070]/10"
          iconColor="text-[#e97070]"
        />
      </div>

      {/* Segunda Seção: Upload Area */}
      <h2 className="text-sm font-semibold text-white/80 uppercase tracking-wider mt-8 mb-2">Importação de Dados</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        <WealthChartCard title="Modo de Ingestão" className="h-[280px]">
          <div className="flex gap-4 mb-6 mt-2">
            <button
              onClick={() => setUploadType("CEI")}
              className={`flex-1 flex flex-col items-center justify-center p-4 rounded-xl border transition-all ${uploadType === "CEI" ? "bg-[#4ecf98]/10 border-[#4ecf98]/40" : "bg-white/[0.02] border-white/5 hover:bg-white/[0.05]"}`}
            >
              <FileSpreadsheet className={`w-8 h-8 mb-2 ${uploadType === "CEI" ? "text-[#4ecf98]" : "text-neutral-500"}`} />
              <span className={`font-medium ${uploadType === "CEI" ? "text-white" : "text-neutral-400"}`}>CEI (B3)</span>
              <span className="text-xs text-neutral-500 mt-1">Planilha Excel / CSV</span>
            </button>
            <button
              onClick={() => setUploadType("OPEN_FINANCE")}
              className={`flex-1 flex flex-col items-center justify-center p-4 rounded-xl border transition-all ${uploadType === "OPEN_FINANCE" ? "bg-[#7F77DD]/10 border-[#7F77DD]/40" : "bg-white/[0.02] border-white/5 hover:bg-white/[0.05]"}`}
            >
              <FileJson className={`w-8 h-8 mb-2 ${uploadType === "OPEN_FINANCE" ? "text-[#7F77DD]" : "text-neutral-500"}`} />
              <span className={`font-medium ${uploadType === "OPEN_FINANCE" ? "text-white" : "text-neutral-400"}`}>Open Finance</span>
              <span className="text-xs text-neutral-500 mt-1">Payload JSON</span>
            </button>
          </div>
          <div className="text-center text-xs text-neutral-500">
            A ingestão é idempotente. Transações com o mesmo <code className="text-[#4ecf98]/80">transaction_hash</code> serão ignoradas de forma segura.
          </div>
        </WealthChartCard>

        <WealthChartCard title="Área de Transferência (Dropzone)" className="h-[280px]">
          <div 
            onDragOver={onDragOver}
            onDrop={onDrop}
            className={`w-full h-full min-h-[160px] border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 transition-all mt-2 relative overflow-hidden ${isUploading ? "border-[#7EB8F7]/40 bg-[#7EB8F7]/5" : "border-white/10 hover:border-white/20 hover:bg-white/[0.02]"}`}
          >
            {isUploading && (
              <div className="absolute top-0 left-0 h-1 bg-[#7EB8F7] transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
            )}

            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileUpload} 
              className="hidden" 
              accept={uploadType === "CEI" ? ".csv,.xlsx" : ".json"}
            />
            
            {isUploading ? (
              <div className="flex flex-col items-center text-[#7EB8F7]">
                <div className="w-8 h-8 border-2 border-[#7EB8F7]/30 border-t-[#7EB8F7] rounded-full animate-spin mb-4" />
                <span className="font-medium">Processando arquivo...</span>
                <span className="text-xs mt-1">{uploadProgress}% concluído</span>
              </div>
            ) : (
              <>
                <UploadCloud className="w-10 h-10 text-neutral-500 mb-4" />
                <p className="text-sm font-medium text-white/90 mb-1">Arraste e solte o arquivo aqui</p>
                <p className="text-xs text-neutral-500 mb-4">ou</p>
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="px-6 py-2 bg-white/5 border border-white/10 rounded-lg text-sm hover:bg-white/10 transition-colors text-white"
                >
                  Selecionar Arquivo {uploadType === "CEI" ? "CSV" : "JSON"}
                </button>
              </>
            )}
          </div>
        </WealthChartCard>

      </div>

      {/* Terceira Seção: Tabela / Logs */}
      <div className="space-y-4">
        {isErrorHistory ? (
           <div className="p-8 text-center bg-white/[0.02] rounded-xl border border-white/[0.05]">
            <p className="text-red-400 mb-2">Erro ao carregar o histórico de importação.</p>
            <button onClick={fetchHistory} className="px-4 py-2 bg-white/5 rounded-lg text-sm hover:bg-white/10 transition">Tentar novamente</button>
          </div>
        ) : (
          <WealthChartCard title="Histórico e Logs de Importação" tableMode>
            <WealthTable
              data={history}
              isLoading={isLoadingHistory}
              pageSize={10}
              emptyMessage="Nenhuma importação realizada."
              columns={[
                {
                  header: "Status",
                  cell: (r) => (
                    r.status === 'SUCCESS'
                      ? <div className="flex items-center gap-1.5 text-[#4ecf98]"><CheckCircle className="w-3.5 h-3.5" /> Sucesso</div>
                      : r.status === 'PARTIAL'
                        ? <div className="flex items-center gap-1.5 text-[#f5a623]"><AlertTriangle className="w-3.5 h-3.5" /> Parcial</div>
                        : <div className="flex items-center gap-1.5 text-[#e97070]"><AlertCircle className="w-3.5 h-3.5" /> Erro</div>
                  )
                },
                { 
                  header: "Data", 
                  cell: (r) => new Date(r.created_at).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }),
                  className: "text-neutral-400"
                },
                { 
                  header: "Arquivo", 
                  accessorKey: "filename",
                  className: "font-medium text-white/80"
                },
                { 
                  header: "Duração", 
                  cell: (r) => `${r.processing_time_ms} ms`,
                  align: "right"
                },
                { 
                  header: "Lidos", 
                  accessorKey: "rows_read",
                  align: "right"
                },
                { 
                  header: "Inseridos", 
                  accessorKey: "rows_imported",
                  align: "right",
                  className: "text-[#4ecf98]"
                },
                { 
                  header: "Duplicados", 
                  accessorKey: "rows_duplicated",
                  align: "right",
                  className: "text-[#f5a623]"
                },
                { 
                  header: "Erros", 
                  accessorKey: "rows_failed",
                  align: "right",
                  className: (r) => r.rows_failed > 0 ? "text-[#e97070]" : "text-neutral-500"
                },
              ]}
              onRowClick={(row) => setSelectedLog(row)}
            />
          </WealthChartCard>
        )}
      </div>

      {/* Modal Detalhamento (Lateral/Modal) */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-[#121214] border border-white/10 rounded-xl max-w-2xl w-full p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold text-white">Detalhes da Importação</h2>
              <button onClick={() => setSelectedLog(null)} className="text-neutral-400 hover:text-white transition">
                ✕
              </button>
            </div>
            
            <div className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-white/5 rounded-lg border border-white/5">
                  <div className="text-xs text-neutral-500 mb-1">ID Audit</div>
                  <div className="text-white break-all font-mono text-xs">{selectedLog.id}</div>
                </div>
                <div className="p-4 bg-white/5 rounded-lg border border-white/5">
                  <div className="text-xs text-neutral-500 mb-1">Data</div>
                  <div className="text-white">{new Date(selectedLog.created_at).toLocaleString()}</div>
                </div>
              </div>

              <div className="p-4 bg-white/5 rounded-lg border border-white/5">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-xs text-neutral-500 mb-1">Arquivo</div>
                    <div className="text-white font-medium break-words">{selectedLog.filename}</div>
                  </div>
                  <div>
                    <div className="text-xs text-neutral-500 mb-1">Tamanho</div>
                    <div className="text-white font-medium">{(selectedLog.file_size / 1024).toFixed(2)} KB</div>
                  </div>
                  <div>
                    <div className="text-xs text-neutral-500 mb-1">Tipo / Parser</div>
                    <div className="text-white font-medium">{selectedLog.file_type} / {selectedLog.parser}</div>
                  </div>
                  <div>
                    <div className="text-xs text-neutral-500 mb-1">Status</div>
                    <div className={`font-medium ${selectedLog.status === 'SUCCESS' ? 'text-[#4ecf98]' : selectedLog.status === 'PARTIAL' ? 'text-[#f5a623]' : 'text-[#e97070]'}`}>{selectedLog.status}</div>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-white/5 rounded-lg border border-white/5">
                <div className="text-xs text-neutral-500 mb-2">Resumo da Ingestão</div>
                <div className="flex gap-6">
                  <div><span className="text-neutral-400">Lidos:</span> <span className="text-white font-medium">{selectedLog.rows_read}</span></div>
                  <div><span className="text-neutral-400">Inseridos:</span> <span className="text-[#4ecf98] font-medium">{selectedLog.rows_imported}</span></div>
                  <div><span className="text-neutral-400">Duplicados:</span> <span className="text-[#f5a623] font-medium">{selectedLog.rows_duplicated}</span></div>
                  <div><span className="text-neutral-400">Falhas:</span> <span className="text-[#e97070] font-medium">{selectedLog.rows_failed}</span></div>
                  <div><span className="text-neutral-400">Tempo:</span> <span className="text-white font-medium">{selectedLog.processing_time_ms} ms</span></div>
                </div>
              </div>
              
              <div className="p-4 bg-white/5 rounded-lg border border-white/5">
                <div className="text-xs text-neutral-500 mb-1">Checksum (Idempotência de Arquivo)</div>
                <code className="text-xs text-[#7EB8F7] break-all bg-black/20 p-2 block rounded border border-white/5">{selectedLog.checksum}</code>
              </div>

              {selectedLog.error_message && (
                <div className="p-4 bg-[#e97070]/10 rounded-lg border border-[#e97070]/20">
                  <div className="text-xs text-[#e97070] mb-1 font-semibold flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Erro Principal</div>
                  <div className="text-white text-xs">{selectedLog.error_message}</div>
                </div>
              )}
            </div>

            <div className="mt-8 flex justify-end">
              <button onClick={() => setSelectedLog(null)} className="px-6 py-2 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition text-white">
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

