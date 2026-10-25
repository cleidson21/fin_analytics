"use client";

import { useState } from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { ThemeSwitcher } from "@/components/ui/ThemeSwitcher";
import {
  ShieldCheck,
  Lock,
  Monitor,
  Globe,
  Sun,
  Download,
  Trash2,
  AlertTriangle,
  ChevronRight,
  Smartphone,
  Eye,
  EyeOff,
  CheckCircle2,
} from "lucide-react";

function SectionCard({
  title,
  subtitle,
  icon: Icon,
  iconColor,
  children,
}: {
  title: string;
  subtitle: string;
  icon: React.ElementType;
  iconColor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-border bg-muted/30 overflow-hidden">
      <div className="flex items-center gap-3 border-b border-border px-6 py-4">
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${iconColor}`}>
          <Icon className="w-4 h-4" />
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">{title}</p>
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        </div>
      </div>
      <div className="divide-y divide-border">{children}</div>
    </div>
  );
}

function SettingsRow({
  icon: Icon,
  label,
  description,
  badge,
  action,
  danger = false,
}: {
  icon: React.ElementType;
  label: string;
  description?: string;
  badge?: string;
  action?: React.ReactNode;
  danger?: boolean;
}) {
  return (
    <div className={`flex items-center gap-4 px-6 py-4 transition-colors hover:bg-muted/30 ${danger ? "hover:bg-red-500/[0.03]" : ""}`}>
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${danger ? "bg-red-500/10 text-red-400" : "bg-muted/40 text-muted-foreground"}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className={`text-sm font-medium ${danger ? "text-red-400" : "text-foreground"}`}>{label}</p>
          {badge && (
            <span className="rounded-full bg-muted/50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground ring-1 ring-inset ring-border">
              {badge}
            </span>
          )}
        </div>
        {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
      </div>
      {action ?? (
        <ChevronRight className={`w-4 h-4 shrink-0 ${danger ? "text-red-400/50" : "text-muted-foreground"}`} />
      )}
    </div>
  );
}

function ToggleSwitch({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-200 focus:outline-none
        ${checked ? "bg-emerald-500" : "bg-muted/70"}`}
    >
      <span
        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform duration-200
          ${checked ? "translate-x-4" : "translate-x-1"}`}
      />
    </button>
  );
}

function PasswordSection() {
  const [show, setShow] = useState(false);
  const [current, setCurrent] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [open, setOpen] = useState(false);
  const [saved, setSaved] = useState(false);

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => { setSaved(false); setOpen(false); setCurrent(""); setNewPw(""); setConfirm(""); }, 2500);
  }

  return (
    <div>
      <div
        className="flex items-center gap-4 px-6 py-4 transition-colors hover:bg-muted/30 cursor-pointer"
        onClick={() => setOpen(!open)}
      >
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted/40 text-muted-foreground">
          <Lock className="w-4 h-4" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-foreground">Alterar senha</p>
          <p className="text-xs text-muted-foreground mt-0.5">Atualize sua senha de acesso</p>
        </div>
        <ChevronRight className={`w-4 h-4 shrink-0 text-muted-foreground transition-transform ${open ? "rotate-90" : ""}`} />
      </div>
      {open && (
        <form onSubmit={handleSave} className="px-6 pb-5 space-y-3">
          <div className="h-px bg-muted/45 mb-4" />
          {[
            { label: "Senha atual", value: current, set: setCurrent },
            { label: "Nova senha", value: newPw, set: setNewPw },
            { label: "Confirmar nova senha", value: confirm, set: setConfirm },
          ].map(({ label, value, set }) => (
            <div key={label}>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">{label}</label>
              <div className="relative">
                <input
                  type={show ? "text" : "password"}
                  value={value}
                  onChange={(e) => set(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full rounded-xl border border-border bg-muted/40 py-2.5 pl-4 pr-10 text-sm text-foreground placeholder-zinc-600 outline-none transition-colors focus:border-emerald-500/40 focus:ring-1 focus:ring-emerald-500/20"
                />
                <button
                  type="button"
                  onClick={() => setShow(!show)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-muted-foreground"
                >
                  {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          ))}
          <div className="flex justify-end pt-1">
            <button
              type="submit"
              className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all ${
                saved
                  ? "bg-emerald-500/20 text-emerald-400 ring-1 ring-inset ring-emerald-400/30"
                  : "bg-emerald-500 text-white hover:bg-emerald-400"
              }`}
            >
              {saved ? <><CheckCircle2 className="w-4 h-4" /> Senha alterada</> : "Salvar nova senha"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const [emailNotif, setEmailNotif] = useState(true);
  const [weeklyReport, setWeeklyReport] = useState(false);
  const [anomalyAlert, setAnomalyAlert] = useState(true);

  function handleExport() {
    const data = {
      profile: localStorage.getItem("fin_profile_extended"),
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "finanalytics_dados.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleClearCache() {
    if (confirm("Isso vai limpar os dados de perfil salvos localmente. Continuar?")) {
      localStorage.removeItem("fin_profile_extended");
      window.location.reload();
    }
  }

  return (
    <PageLayout title="Configurações">
      <div className="max-w-3xl mx-auto space-y-6 pb-12">

        {/* Segurança */}
        <SectionCard
          title="Segurança"
          subtitle="Senha e controle de acesso"
          icon={ShieldCheck}
          iconColor="bg-emerald-500/15 text-emerald-400"
        >
          <PasswordSection />
          <SettingsRow
            icon={Smartphone}
            label="Autenticação de dois fatores"
            description="Adicione uma camada extra de proteção"
            badge="Em breve"
            action={<span className="text-xs text-muted-foreground">Indisponível</span>}
          />
          <SettingsRow
            icon={Monitor}
            label="Sessões ativas"
            description="Gerencie onde você está conectado"
            action={
              <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 ring-1 ring-inset ring-emerald-400/20">
                Esta sessão
              </span>
            }
          />
        </SectionCard>

        {/* Notificações */}
        <SectionCard
          title="Notificações"
          subtitle="Controle os alertas que deseja receber"
          icon={Monitor}
          iconColor="bg-sky-500/15 text-sky-400"
        >
          <SettingsRow
            icon={Monitor}
            label="Notificações por e-mail"
            description="Receba resumos e alertas no seu e-mail"
            badge="Em breve"
            action={<ToggleSwitch checked={emailNotif} onChange={setEmailNotif} />}
          />
          <SettingsRow
            icon={Monitor}
            label="Relatório semanal"
            description="Resumo de gastos toda segunda-feira"
            badge="Em breve"
            action={<ToggleSwitch checked={weeklyReport} onChange={setWeeklyReport} />}
          />
          <SettingsRow
            icon={AlertTriangle}
            label="Alertas de anomalias"
            description="Gastos incomuns ou acima da média histórica"
            badge="Em breve"
            action={<ToggleSwitch checked={anomalyAlert} onChange={setAnomalyAlert} />}
          />
        </SectionCard>

        {/* Aparência */}
        <SectionCard
          title="Aparência"
          subtitle="Tema e idioma do sistema"
          icon={Sun}
          iconColor="bg-amber-500/15 text-amber-400"
        >
          <SettingsRow
            icon={Sun}
            label="Tema"
            description="Siga o sistema ou escolha um tema"
            action={<ThemeSwitcher />}
          />
          <SettingsRow
            icon={Globe}
            label="Idioma"
            description="Português (Brasil)"
            badge="Em breve"
            action={
              <span className="rounded-xl bg-muted/45 px-3 py-1 text-xs text-muted-foreground ring-1 ring-inset ring-border">
                🇧🇷 PT-BR
              </span>
            }
          />
        </SectionCard>

        {/* Dados & Sistema */}
        <SectionCard
          title="Dados e Sistema"
          subtitle="Exportar ou limpar dados locais"
          icon={Download}
          iconColor="bg-violet-500/15 text-violet-400"
        >
          <div className="flex items-center gap-4 px-6 py-4 transition-colors hover:bg-muted/30 cursor-pointer" onClick={handleExport}>
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted/40 text-muted-foreground">
              <Download className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground">Exportar meus dados</p>
              <p className="text-xs text-muted-foreground mt-0.5">Baixar perfil e configurações em JSON</p>
            </div>
            <ChevronRight className="w-4 h-4 shrink-0 text-muted-foreground" />
          </div>
          <div className="flex items-center gap-4 px-6 py-4 transition-colors hover:bg-red-500/[0.03] cursor-pointer" onClick={handleClearCache}>
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-red-500/10 text-red-400">
              <Trash2 className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-red-400">Limpar dados locais</p>
              <p className="text-xs text-muted-foreground mt-0.5">Remove o perfil estendido salvo neste navegador</p>
            </div>
            <ChevronRight className="w-4 h-4 shrink-0 text-red-400/50" />
          </div>
        </SectionCard>

      </div>
    </PageLayout>
  );
}
