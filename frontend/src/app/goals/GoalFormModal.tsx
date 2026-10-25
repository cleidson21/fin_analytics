"use client";

import { useEffect, useId, useRef, useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import type {
  Goal,
  GoalCreatePayload,
  GoalStatus,
  GoalType,
  GoalUpdatePayload,
} from "./types";
import { GOAL_STATUS_OPTIONS, GOAL_TYPE_OPTIONS } from "./types";

const fieldClassName =
  "min-h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground outline-none transition placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30 disabled:cursor-not-allowed disabled:opacity-60";
const labelClassName = "mb-1.5 block text-xs font-medium text-muted-foreground";

function useDialogFocus(
  dialogRef: React.RefObject<HTMLDivElement | null>,
  initialFocusRef: React.RefObject<HTMLElement | null>,
  onClose: () => void,
  disabled = false,
) {
  useEffect(() => {
    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialog = dialogRef.current;
    initialFocusRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !disabled) {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !dialog) return;

      const focusable = Array.from(
        dialog.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
        ),
      );
      const first = focusable[0];
      const last = focusable.at(-1);
      if (!first || !last) return;

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [dialogRef, disabled, initialFocusRef, onClose]);
}

interface GoalFormModalProps {
  mode: "create" | "edit";
  goal?: Goal;
  onSave: (payload: GoalCreatePayload | GoalUpdatePayload) => Promise<void>;
  onClose: () => void;
  saving: boolean;
}

export function GoalFormModal({ mode, goal, onSave, onClose, saving }: GoalFormModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const firstInputRef = useRef<HTMLInputElement>(null);
  const titleId = useId();
  const errorId = useId();
  useDialogFocus(dialogRef, firstInputRef, onClose, saving);

  const [name, setName] = useState(goal?.name ?? "");
  const [description, setDescription] = useState(goal?.description ?? "");
  const [goalType, setGoalType] = useState<GoalType>(goal?.goal_type ?? "CUSTOM");
  const [targetAmount, setTargetAmount] = useState(goal?.target_amount?.toString() ?? "");
  const [targetDate, setTargetDate] = useState(goal?.target_date ?? "");
  const [currentAmount, setCurrentAmount] = useState(
    goal?.current_amount !== null && goal?.current_amount !== undefined ? goal.current_amount.toString() : "",
  );
  const [priority, setPriority] = useState(goal?.priority?.toString() ?? "");
  const [monthlyContribution, setMonthlyContribution] = useState(
    goal?.monthly_contribution !== null && goal?.monthly_contribution !== undefined
      ? goal.monthly_contribution.toString()
      : "",
  );
  const [linkedAccountId, setLinkedAccountId] = useState(goal?.linked_account_id ?? "");
  const [status, setStatus] = useState<GoalStatus>(goal?.status ?? "ACTIVE");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    const targetAmountNumber = Number.parseFloat(targetAmount);
    if (name.trim().length < 3) {
      setError("O nome deve ter pelo menos 3 caracteres.");
      return;
    }
    if (!Number.isFinite(targetAmountNumber) || targetAmountNumber <= 0) {
      setError("O valor alvo deve ser maior que zero.");
      return;
    }

    const payload: GoalCreatePayload | GoalUpdatePayload = {
      name: name.trim(),
      description: description.trim() || undefined,
      goal_type: goalType,
      target_amount: targetAmountNumber,
      target_date: targetDate || undefined,
      current_amount: currentAmount !== "" ? Number.parseFloat(currentAmount) : undefined,
      priority: priority !== "" ? Number.parseInt(priority, 10) : undefined,
      monthly_contribution: monthlyContribution !== "" ? Number.parseFloat(monthlyContribution) : undefined,
      linked_account_id: linkedAccountId.trim() || undefined,
      ...(mode === "edit" ? { status } : {}),
    };

    try {
      await onSave(payload);
    } catch {
      setError("Não foi possível salvar a meta. Tente novamente.");
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-3 backdrop-blur-sm sm:p-6"
      onMouseDown={(event) => {
        if (event.currentTarget === event.target && !saving) onClose();
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={error ? errorId : undefined}
        className="max-h-[92dvh] w-full max-w-xl overflow-y-auto rounded-2xl border border-border bg-card p-5 text-card-foreground shadow-2xl sm:p-7"
      >
        <header className="mb-5 flex items-center justify-between gap-4">
          <h2 id={titleId} className="text-lg font-semibold">
            {mode === "create" ? "Nova meta" : "Editar meta"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            aria-label="Fechar formulário de meta"
            className="grid size-10 shrink-0 place-items-center rounded-lg border border-border text-muted-foreground transition hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          >
            <X aria-hidden="true" className="size-4" />
          </button>
        </header>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor={`${titleId}-name`} className={labelClassName}>Nome *</label>
            <input
              ref={firstInputRef}
              id={`${titleId}-name`}
              className={fieldClassName}
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Ex.: Reserva de emergência"
              maxLength={100}
              required
            />
          </div>

          <div>
            <label htmlFor={`${titleId}-type`} className={labelClassName}>Tipo de meta *</label>
            <select id={`${titleId}-type`} className={fieldClassName} value={goalType} onChange={(event) => setGoalType(event.target.value as GoalType)} required>
              {GOAL_TYPE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor={`${titleId}-target`} className={labelClassName}>Valor alvo (R$) *</label>
              <input id={`${titleId}-target`} className={fieldClassName} type="number" inputMode="decimal" value={targetAmount} onChange={(event) => setTargetAmount(event.target.value)} placeholder="30000,00" min="0.01" step="0.01" required />
            </div>
            <div>
              <label htmlFor={`${titleId}-current`} className={labelClassName}>Valor atual (R$) <span className="font-normal">· opcional</span></label>
              <input id={`${titleId}-current`} className={fieldClassName} type="number" inputMode="decimal" value={currentAmount} onChange={(event) => setCurrentAmount(event.target.value)} placeholder="0,00" min="0" step="0.01" />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor={`${titleId}-date`} className={labelClassName}>Prazo</label>
              <input id={`${titleId}-date`} className={fieldClassName} type="date" value={targetDate} onChange={(event) => setTargetDate(event.target.value)} />
            </div>
            <div>
              <label htmlFor={`${titleId}-priority`} className={labelClassName}>Prioridade</label>
              <select id={`${titleId}-priority`} className={fieldClassName} value={priority} onChange={(event) => setPriority(event.target.value)}>
                <option value="">Nenhuma</option>
                <option value="1">1 — Muito alta</option>
                <option value="2">2 — Alta</option>
                <option value="3">3 — Média</option>
                <option value="4">4 — Baixa</option>
                <option value="5">5 — Muito baixa</option>
              </select>
            </div>
          </div>

          <div>
            <label htmlFor={`${titleId}-contribution`} className={labelClassName}>Aporte mensal planejado (R$)</label>
            <input id={`${titleId}-contribution`} className={fieldClassName} type="number" inputMode="decimal" value={monthlyContribution} onChange={(event) => setMonthlyContribution(event.target.value)} placeholder="0,00" min="0" step="0.01" />
          </div>

          <div>
            <label htmlFor={`${titleId}-account`} className={labelClassName}>Conta ou carteira (referência)</label>
            <input id={`${titleId}-account`} className={fieldClassName} value={linkedAccountId} onChange={(event) => setLinkedAccountId(event.target.value)} placeholder="Ex.: NuInvest, XP, Corretora" maxLength={255} />
          </div>

          <div>
            <label htmlFor={`${titleId}-description`} className={labelClassName}>Descrição</label>
            <textarea id={`${titleId}-description`} className={`${fieldClassName} min-h-20 resize-y`} value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Detalhes sobre esta meta" maxLength={500} />
          </div>

          {mode === "edit" ? (
            <div>
              <label htmlFor={`${titleId}-status`} className={labelClassName}>Status</label>
              <select id={`${titleId}-status`} className={fieldClassName} value={status} onChange={(event) => setStatus(event.target.value as GoalStatus)}>
                {GOAL_STATUS_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
            </div>
          ) : null}

          {error ? <p id={errorId} role="alert" className="rounded-lg border border-destructive/25 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p> : null}

          <footer className="flex flex-col-reverse gap-2 border-t border-border pt-4 sm:flex-row sm:justify-end">
            <button type="button" onClick={onClose} disabled={saving} className="min-h-10 rounded-lg border border-border px-4 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50">Cancelar</button>
            <button type="submit" disabled={saving} className="min-h-10 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60">
              {saving ? "Salvando…" : mode === "create" ? "Criar meta" : "Salvar alterações"}
            </button>
          </footer>
        </form>
      </div>
    </div>
  );
}

interface ConfirmDialogProps {
  goal: Goal;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
  deleting: boolean;
}

export function ConfirmDeleteDialog({ goal, onConfirm, onCancel, deleting }: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  useDialogFocus(dialogRef, cancelRef, onCancel, deleting);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onMouseDown={(event) => {
        if (event.currentTarget === event.target && !deleting) onCancel();
      }}
    >
      <div ref={dialogRef} role="alertdialog" aria-modal="true" aria-labelledby={titleId} className="w-full max-w-sm rounded-2xl border border-destructive/25 bg-card p-6 text-card-foreground shadow-2xl">
        <div className="text-center">
          <span className="mx-auto grid size-11 place-items-center rounded-full bg-destructive/10 text-destructive"><AlertTriangle aria-hidden="true" className="size-5" /></span>
          <h2 id={titleId} className="mt-4 text-lg font-semibold">Excluir meta</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            A meta <strong className="font-semibold text-foreground">“{goal.name}”</strong> será excluída. Esta ação não pode ser desfeita.
          </p>
        </div>
        <div className="mt-6 grid grid-cols-2 gap-2">
          <button ref={cancelRef} type="button" onClick={onCancel} disabled={deleting} className="min-h-10 rounded-lg border border-border px-4 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50">Cancelar</button>
          <button type="button" onClick={() => void onConfirm()} disabled={deleting} className="min-h-10 rounded-lg bg-destructive px-4 text-sm font-semibold text-destructive-foreground hover:bg-destructive/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60">
            {deleting ? "Excluindo…" : "Excluir"}
          </button>
        </div>
      </div>
    </div>
  );
}
