// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GoalCard } from "./GoalCard";
import type { Goal } from "./types";

const goal: Goal = {
  id: "goal-1",
  user_id: "user-1",
  name: "Reserva de segurança",
  description: "Proteção para despesas inesperadas.",
  goal_type: "EMERGENCY_RESERVE",
  target_amount: 30000,
  current_amount: 12500,
  progress_pct: 41.7,
  monthly_contribution: 750,
  target_date: "2027-12-31",
  status: "ACTIVE",
  priority: 1,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-10-01T00:00:00Z",
};

afterEach(() => cleanup());

describe("GoalCard", () => {
  it("presents the governed progress and registered goal facts accessibly", () => {
    render(<GoalCard goal={goal} onEdit={vi.fn()} onDelete={vi.fn()} />);

    expect(screen.getByText("R$ 30.000,00")).toBeTruthy();
    expect(screen.getByText("R$ 12.500,00")).toBeTruthy();
    expect(screen.getByText("R$ 750,00/mês")).toBeTruthy();
    const progress = screen.getByRole("progressbar", { name: "Progresso da meta Reserva de segurança" });
    expect(progress.getAttribute("aria-valuenow")).toBe("41.7");
    expect(progress.getAttribute("aria-valuetext")).toBe("41,7%");
    expect(screen.getByText("41,7%")).toBeTruthy();
  });

  it("does not fabricate a percentage when the contract omits progress", () => {
    render(
      <GoalCard
        goal={{ ...goal, current_amount: 5000, progress_pct: null }}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.queryByRole("progressbar")).toBeNull();
    expect(screen.getByText("Progresso ainda não disponível")).toBeTruthy();
    expect(screen.queryByText("0,0%")).toBeNull();
  });

  it("preserves the existing edit and delete actions", () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(<GoalCard goal={goal} onEdit={onEdit} onDelete={onDelete} />);

    fireEvent.click(screen.getByRole("button", { name: "Editar" }));
    fireEvent.click(screen.getByRole("button", { name: "Excluir" }));

    expect(onEdit).toHaveBeenCalledWith(goal);
    expect(onDelete).toHaveBeenCalledWith(goal);
  });
});
