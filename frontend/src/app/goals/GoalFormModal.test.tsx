// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConfirmDeleteDialog, GoalFormModal } from "./GoalFormModal";
import type { Goal } from "./types";

const goal: Goal = {
  id: "goal-1",
  user_id: "user-1",
  name: "Reserva de segurança",
  goal_type: "EMERGENCY_RESERVE",
  target_amount: 30000,
  status: "ACTIVE",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-10-01T00:00:00Z",
};

afterEach(() => cleanup());

describe("Goal dialogs", () => {
  it("exposes the goal form as a labelled modal and moves focus to its first field", () => {
    render(<GoalFormModal mode="create" saving={false} onClose={vi.fn()} onSave={vi.fn()} />);

    expect(screen.getByRole("dialog", { name: "Nova meta" })).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByRole("textbox", { name: "Nome *" }));
    expect(screen.getByRole("textbox", { name: "Descrição" }).className).toContain("bg-background");
  });

  it("closes with Escape when no save is in progress", () => {
    const onClose = vi.fn();
    render(<GoalFormModal mode="create" saving={false} onClose={onClose} onSave={vi.fn()} />);

    fireEvent.keyDown(document, { key: "Escape" });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("keeps the destructive confirmation modal while deletion is pending", () => {
    const onCancel = vi.fn();
    render(<ConfirmDeleteDialog goal={goal} deleting onCancel={onCancel} onConfirm={vi.fn()} />);

    expect(screen.getByRole("alertdialog", { name: "Excluir meta" })).toBeTruthy();
    fireEvent.keyDown(document, { key: "Escape" });

    expect(onCancel).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Excluindo…" }).hasAttribute("disabled")).toBe(true);
  });
});
