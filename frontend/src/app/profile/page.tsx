"use client";

import { useState, useEffect, useRef } from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { useAuth } from "@/contexts/AuthContext";
import {
  User,
  Briefcase,
  Save,
  CheckCircle2,
  Mail,
  Phone,
  Calendar,
  CreditCard,
  Building2,
  DollarSign,
  FileText,
  Clock,
  ShieldCheck,
} from "lucide-react";

const STORAGE_KEY = "fin_profile_extended";
const PERSISTED_PROFILE_FIELDS = ["display_name", "occupation", "company", "tax_regime"] as const;

interface ExtendedProfile {
  display_name: string;
  birthdate: string;
  cpf: string;
  phone: string;
  occupation: string;
  company: string;
  gross_monthly_income: string;
  tax_regime: string;
  employment_start: string;
}

const DEFAULT_PROFILE: ExtendedProfile = {
  display_name: "",
  birthdate: "",
  cpf: "",
  phone: "",
  occupation: "",
  company: "",
  gross_monthly_income: "",
  tax_regime: "",
  employment_start: "",
};

function getPersistedProfile(profile: Partial<ExtendedProfile>) {
  return PERSISTED_PROFILE_FIELDS.reduce<Partial<ExtendedProfile>>((persisted, field) => {
    persisted[field] = profile[field] ?? "";
    return persisted;
  }, {});
}

const TAX_REGIMES = [
  { value: "", label: "Selecione..." },
  { value: "CLT", label: "CLT — Empregado" },
  { value: "MEI", label: "MEI — Microempreendedor Individual" },
  { value: "PJ", label: "PJ — Pessoa Jurídica" },
  { value: "AUTONOMO", label: "Autônomo / Freelancer" },
  { value: "SERVIDOR", label: "Servidor Público" },
  { value: "APOSENTADO", label: "Aposentado / Pensionista" },
];

function calcAge(birthdate: string): string {
  if (!birthdate) return "";
  const birth = new Date(birthdate);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return `${age} anos`;
}

function formatCPF(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  return digits
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/(\d{3})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3-$4");
}

function formatPhone(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  if (digits.length <= 2) return digits;
  if (digits.length <= 7) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  if (digits.length <= 11)
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
  return value;
}

function formatCurrency(value: string): string {
  const digits = value.replace(/\D/g, "");
  if (!digits) return "";
  const num = parseInt(digits) / 100;
  return num.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-1.5">
      {children}
    </label>
  );
}

function InputField({
  icon: Icon,
  value,
  onChange,
  placeholder,
  type = "text",
  readOnly = false,
}: {
  icon: React.ElementType;
  value: string;
  onChange?: (v: string) => void;
  placeholder?: string;
  type?: string;
  readOnly?: boolean;
}) {
  return (
    <div className="relative">
      <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600" />
      <input
        type={type}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        readOnly={readOnly}
        className={`w-full rounded-xl border py-2.5 pl-10 pr-4 text-sm outline-none transition-colors
          ${readOnly
            ? "border-white/5 bg-white/[0.02] text-zinc-500 cursor-not-allowed"
            : "border-white/10 bg-white/[0.04] text-zinc-100 placeholder-zinc-600 focus:border-emerald-500/40 focus:bg-white/[0.06] focus:ring-1 focus:ring-emerald-500/20"
          }`}
      />
    </div>
  );
}

function SelectField({
  icon: Icon,
  value,
  onChange,
  options,
}: {
  icon: React.ElementType;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="relative">
      <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600 pointer-events-none" />
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full appearance-none rounded-xl border border-white/10 bg-white/[0.04] py-2.5 pl-10 pr-8 text-sm text-zinc-100 outline-none transition-colors focus:border-emerald-500/40 focus:bg-white/[0.06] focus:ring-1 focus:ring-emerald-500/20"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value} className="bg-zinc-900">
            {o.label}
          </option>
        ))}
      </select>
      <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-zinc-600">▾</span>
    </div>
  );
}

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
    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] overflow-hidden">
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-6 py-4">
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${iconColor}`}>
          <Icon className="w-4 h-4" />
        </div>
        <div>
          <p className="text-sm font-semibold text-zinc-100">{title}</p>
          <p className="text-xs text-zinc-500">{subtitle}</p>
        </div>
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<ExtendedProfile>(DEFAULT_PROFILE);
  const [saved, setSaved] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as Partial<ExtendedProfile>;
        const persisted = getPersistedProfile(parsed);
        // Rewrite old entries so previously saved sensitive fields are removed.
        localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
        setProfile((prev) => ({ ...prev, ...persisted }));
      } catch {}
    }
    if (user?.name) {
      setProfile((prev) => ({ ...prev, display_name: prev.display_name || user.name }));
    }
  }, [user]);

  function set(key: keyof ExtendedProfile, value: string) {
    setProfile((prev) => ({ ...prev, [key]: value }));
  }

  function handleSave() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(getPersistedProfile(profile)));
    setSaved(true);
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => setSaved(false), 3000);
  }

  const initials = (profile.display_name || user?.name || "U")
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  const age = calcAge(profile.birthdate);

  return (
    <PageLayout title="Perfil">
      <div className="max-w-3xl mx-auto space-y-6 pb-12">

        {/* Avatar + nome hero */}
        <div className="flex items-center gap-5 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6">
          <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 ring-1 ring-inset ring-emerald-400/20">
            <span className="text-2xl font-bold text-emerald-300">{initials}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xl font-semibold text-zinc-100 truncate">
              {profile.display_name || user?.name || "Usuário"}
            </p>
            <p className="text-sm text-zinc-500 mt-0.5">{user?.email}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 ring-1 ring-inset ring-emerald-400/20">
                <ShieldCheck className="w-3 h-3" />
                {user?.role ?? "USER"}
              </span>
              {age && (
                <span className="inline-flex items-center gap-1 rounded-full bg-white/[0.05] px-2.5 py-0.5 text-xs text-zinc-400 ring-1 ring-inset ring-white/10">
                  <Calendar className="w-3 h-3" />
                  {age}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Dados Pessoais */}
        <SectionCard
          title="Dados Pessoais"
          subtitle="Informações básicas do seu perfil"
          icon={User}
          iconColor="bg-sky-500/15 text-sky-400"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <FieldLabel>Nome completo</FieldLabel>
              <InputField
                icon={User}
                value={profile.display_name}
                onChange={(v) => set("display_name", v)}
                placeholder="Seu nome completo"
              />
            </div>

            <div>
              <FieldLabel>E-mail</FieldLabel>
              <InputField
                icon={Mail}
                value={user?.email ?? ""}
                readOnly
                placeholder="e-mail"
              />
            </div>

            <div>
              <FieldLabel>Telefone</FieldLabel>
              <InputField
                icon={Phone}
                value={profile.phone}
                onChange={(v) => set("phone", formatPhone(v))}
                placeholder="(11) 99999-9999"
              />
            </div>

            <div>
              <FieldLabel>Data de nascimento</FieldLabel>
              <InputField
                icon={Calendar}
                value={profile.birthdate}
                onChange={(v) => set("birthdate", v)}
                type="date"
              />
            </div>

            <div>
              <FieldLabel>CPF</FieldLabel>
              <InputField
                icon={CreditCard}
                value={profile.cpf}
                onChange={(v) => set("cpf", formatCPF(v))}
                placeholder="000.000.000-00"
              />
            </div>
          </div>
        </SectionCard>

        {/* Dados de Trabalho */}
        <SectionCard
          title="Dados de Trabalho"
          subtitle="Usados como base para análises de saúde financeira e metas"
          icon={Briefcase}
          iconColor="bg-violet-500/15 text-violet-400"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <FieldLabel>Ocupação / Cargo</FieldLabel>
              <InputField
                icon={Briefcase}
                value={profile.occupation}
                onChange={(v) => set("occupation", v)}
                placeholder="Ex: Desenvolvedor Sênior"
              />
            </div>

            <div>
              <FieldLabel>Empresa / Empregador</FieldLabel>
              <InputField
                icon={Building2}
                value={profile.company}
                onChange={(v) => set("company", v)}
                placeholder="Ex: Acme Corp"
              />
            </div>

            <div>
              <FieldLabel>Renda mensal bruta (R$)</FieldLabel>
              <InputField
                icon={DollarSign}
                value={profile.gross_monthly_income}
                onChange={(v) => set("gross_monthly_income", formatCurrency(v))}
                placeholder="0,00"
              />
            </div>

            <div>
              <FieldLabel>Regime tributário</FieldLabel>
              <SelectField
                icon={FileText}
                value={profile.tax_regime}
                onChange={(v) => set("tax_regime", v)}
                options={TAX_REGIMES}
              />
            </div>

            <div className="sm:col-span-2">
              <FieldLabel>Início no emprego atual</FieldLabel>
              <InputField
                icon={Clock}
                value={profile.employment_start}
                onChange={(v) => set("employment_start", v)}
                type="date"
              />
            </div>
          </div>
        </SectionCard>

        {/* Botão salvar */}
        <div className="flex items-center justify-between gap-4">
          <p className="text-xs text-zinc-600">
            CPF, nascimento, telefone, renda e vínculo não são salvos neste navegador.
          </p>
          <button
            onClick={handleSave}
            className={`inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-all duration-200
              ${saved
                ? "bg-emerald-500/20 text-emerald-400 ring-1 ring-inset ring-emerald-400/30"
                : "bg-emerald-500 text-white hover:bg-emerald-400 active:scale-95 shadow-lg shadow-emerald-500/20"
              }`}
          >
            {saved ? (
              <>
                <CheckCircle2 className="w-4 h-4" />
                Salvo com sucesso
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Salvar perfil
              </>
            )}
          </button>
        </div>

      </div>
    </PageLayout>
  );
}
