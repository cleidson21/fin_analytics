import { PageLayout } from "@/components/layout/PageLayout";
import { HeartPulse, Target, Map, Brain, BarChart2, Sparkles } from "lucide-react";
import Link from "next/link";

export default function WealthIntelligenceDashboard() {
  return (
    <PageLayout title="Wealth Intelligence" subtitle="O sistema operacional do seu patrimônio." hideTitle={true}>
      <div className="flex flex-col gap-8">
        <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>

          {/* Functional: Goals */}
          <div style={{
            background: "rgba(78,207,152,0.08)",
            border: "1px solid rgba(78,207,152,0.2)",
            borderRadius: "16px",
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            transition: "background 0.2s, border-color 0.2s",
          }}>
            <div aria-hidden="true" style={{ color: "#4ecf98", display: "flex", height: "24px", alignItems: "center" }}>
              <Target size={24} strokeWidth={1.8} />
            </div>
            <div>
              <h3 style={{ color: "#f1f5f9", fontSize: "16px", fontWeight: 600, margin: "0 0 4px" }}>Metas</h3>
              <p style={{ color: "#94a3b8", fontSize: "13px", margin: 0, lineHeight: 1.5 }}>
                Gerencie seus objetivos, acompanhe o progresso e defina prioridades.
              </p>
            </div>
            <Link
              href="/goals"
              style={{ color: "#4ecf98", fontSize: "13px", fontWeight: 600, marginTop: "auto", display: "inline-block", paddingTop: "8px" }}
            >
              Acessar Metas &rarr;
            </Link>
          </div>

          {/* Functional: Financial Health */}
          <div style={{
            background: "rgba(126,184,247,0.08)",
            border: "1px solid rgba(126,184,247,0.2)",
            borderRadius: "16px",
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}>
            <div
              aria-hidden="true"
              style={{ color: "#7EB8F7", display: "flex", height: "24px", alignItems: "center" }}
            >
              <HeartPulse size={24} strokeWidth={1.8} />
            </div>
            <div>
              <h3 style={{ color: "#f1f5f9", fontSize: "16px", fontWeight: 600, margin: "0 0 4px" }}>Saúde Financeira</h3>
              <p style={{ color: "#94a3b8", fontSize: "13px", margin: 0, lineHeight: 1.5 }}>
                Consulte o fluxo de caixa, histórico, categorias e sinais certificados.
              </p>
            </div>
            <Link
              href="/wealth-intelligence/health"
              style={{ color: "#7EB8F7", fontSize: "13px", fontWeight: 600, marginTop: "auto", display: "inline-block", paddingTop: "8px" }}
            >
              Acessar Saúde Financeira &rarr;
            </Link>
          </div>

          {/* Functional: Planning foundation */}
          <div style={{
            background: "rgba(196,181,253,0.08)",
            border: "1px solid rgba(196,181,253,0.2)",
            borderRadius: "16px",
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}>
            <div aria-hidden="true" style={{ color: "#94a3b8", display: "flex", height: "24px", alignItems: "center" }}>
              <Map size={24} strokeWidth={1.5} />
            </div>
            <div>
              <h3 style={{ color: "#f1f5f9", fontSize: "16px", fontWeight: 600, margin: "0 0 4px" }}>Planejamento</h3>
              <p style={{ color: "#94a3b8", fontSize: "13px", margin: 0, lineHeight: 1.5 }}>
                Projete seu patrimônio, analise metas e compare cenários.
              </p>
            </div>
            <Link
              href="/wealth-intelligence/planning"
              style={{ color: "#c4b5fd", fontSize: "13px", fontWeight: 600, marginTop: "auto", display: "inline-block", paddingTop: "8px" }}
            >
              Abrir Planejamento &rarr;
            </Link>
          </div>

          {/* Coming Soon: Portfolio Intelligence */}
          <div style={{
            background: "rgba(255,255,255,0.02)",
            border: "1px dashed rgba(255,255,255,0.08)",
            borderRadius: "16px",
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            opacity: 0.55,
          }}>
            <div aria-hidden="true" style={{ color: "#94a3b8", display: "flex", height: "24px", alignItems: "center" }}>
              <Brain size={24} strokeWidth={1.5} />
            </div>
            <div>
              <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "4px" }}>
                <h3 style={{ color: "#f1f5f9", fontSize: "16px", fontWeight: 600, margin: 0 }}>Portfolio Intelligence</h3>
                <span style={{ fontSize: "10px", background: "rgba(255,255,255,0.08)", padding: "2px 6px", borderRadius: "4px", color: "#64748b", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>Em breve</span>
              </div>
              <p style={{ color: "#94a3b8", fontSize: "13px", margin: 0, lineHeight: 1.5 }}>
                Análise de risco, Drop &amp; Event Radar e descoberta de Oportunidades.
              </p>
            </div>
          </div>

          {/* Coming Soon: Market Intelligence & News */}
          <div style={{
            background: "rgba(255,255,255,0.02)",
            border: "1px dashed rgba(255,255,255,0.08)",
            borderRadius: "16px",
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            opacity: 0.55,
          }}>
            <div aria-hidden="true" style={{ color: "#94a3b8", display: "flex", height: "24px", alignItems: "center" }}>
              <BarChart2 size={24} strokeWidth={1.5} />
            </div>
            <div>
              <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "4px" }}>
                <h3 style={{ color: "#f1f5f9", fontSize: "16px", fontWeight: 600, margin: 0 }}>Market Intelligence</h3>
                <span style={{ fontSize: "10px", background: "rgba(255,255,255,0.08)", padding: "2px 6px", borderRadius: "4px", color: "#64748b", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>Em breve</span>
              </div>
              <p style={{ color: "#94a3b8", fontSize: "13px", margin: 0, lineHeight: 1.5 }}>
                Notícias, contexto macroeconômico e alertas do mercado.
              </p>
            </div>
          </div>

          {/* Coming Soon: AI Copilot */}
          <div style={{
            background: "rgba(255,255,255,0.02)",
            border: "1px dashed rgba(255,255,255,0.08)",
            borderRadius: "16px",
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            opacity: 0.55,
          }}>
            <div aria-hidden="true" style={{ color: "#94a3b8", display: "flex", height: "24px", alignItems: "center" }}>
              <Sparkles size={24} strokeWidth={1.5} />
            </div>
            <div>
              <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "4px" }}>
                <h3 style={{ color: "#f1f5f9", fontSize: "16px", fontWeight: 600, margin: 0 }}>Wealth Copilot</h3>
                <span style={{ fontSize: "10px", background: "rgba(255,255,255,0.08)", padding: "2px 6px", borderRadius: "4px", color: "#64748b", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>Em breve</span>
              </div>
              <p style={{ color: "#94a3b8", fontSize: "13px", margin: 0, lineHeight: 1.5 }}>
                Sua Inteligência Artificial rodando localmente (Ollama) para responder perguntas do seu patrimônio.
              </p>
            </div>
          </div>

        </div>
      </div>
    </PageLayout>
  );
}
