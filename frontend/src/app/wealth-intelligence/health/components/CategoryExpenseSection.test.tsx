// @vitest-environment jsdom

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CategoryExpenseSection } from "./CategoryExpenseSection";

describe("CategoryExpenseSection", () => {
  it("keeps the five highest-ranked categories in view and discloses the remainder", () => {
    render(
      <CategoryExpenseSection
        summary={{
          reference_month: "2026-10",
          total_expense: "2100.00",
          top_category: { category: "Categoria 1", expense_total: "600.00", share_of_expenses: "0.2857", rank: 1 },
          categories: Array.from({ length: 7 }, (_, index) => ({
            category: `Categoria ${index + 1}`,
            expense_total: String(600 - index * 50),
            share_of_expenses: "0.1000",
            rank: index + 1,
          })),
        }}
      />,
    );

    expect(screen.getByRole("list", { name: "Principais despesas por categoria" }).children).toHaveLength(5);
    expect(screen.getByText("Ver demais categorias (2)")).toBeTruthy();

    fireEvent.click(screen.getByText("Ver demais categorias (2)"));
    expect(screen.getByRole("list", { name: "Demais despesas por categoria" }).children).toHaveLength(2);
  });
});
