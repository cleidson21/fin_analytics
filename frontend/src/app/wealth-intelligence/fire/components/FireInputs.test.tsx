// @vitest-environment jsdom

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { createFireForm } from "./fireForm";
import { FireInputs } from "./FireInputs";

afterEach(() => cleanup());

describe("FireInputs", () => {
  it("shows only the common fields for the current diagnosis", () => {
    render(<FireInputs value={createFireForm()} errors={{}} onChange={vi.fn()} onMode={vi.fn()} />);

    expect(screen.getByLabelText("Gasto mensal desejado (BRL)")).toBeTruthy();
    expect(screen.getByLabelText("Taxa anual de retirada (% a.a.)")).toBeTruthy();
    expect(screen.queryByLabelText("Aporte mensal do cenário (BRL)")).toBeNull();
    expect(screen.queryByLabelText("Horizonte (meses)")).toBeNull();
    expect(screen.queryByLabelText("Retorno anual esperado (% a.a.)")).toBeNull();
  });

  it("shows contribution, horizon and return only for the reach-date analysis", () => {
    render(
      <FireInputs
        value={{ ...createFireForm(), mode: "PROJECTED_DATE" }}
        errors={{}}
        onChange={vi.fn()}
        onMode={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Aporte mensal do cenário (BRL)")).toBeTruthy();
    expect(screen.getByLabelText("Horizonte (meses)")).toBeTruthy();
    expect(screen.getByLabelText("Retorno anual esperado (% a.a.)")).toBeTruthy();
    expect(screen.queryByLabelText("Data desejada para independência")).toBeNull();
  });

  it("shows the desired date and return for the required-contribution analysis", () => {
    render(
      <FireInputs
        value={{ ...createFireForm(), mode: "REQUIRED_CONTRIBUTION" }}
        errors={{}}
        onChange={vi.fn()}
        onMode={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Data desejada para independência")).toBeTruthy();
    expect(screen.getByLabelText("Retorno anual esperado (% a.a.)")).toBeTruthy();
    expect(screen.queryByLabelText("Aporte mensal do cenário (BRL)")).toBeNull();
    expect(screen.queryByLabelText("Horizonte (meses)")).toBeNull();
  });

  it("reveals a monetary field only for the user-provided starting value", () => {
    const { rerender } = render(
      <FireInputs value={createFireForm()} errors={{}} onChange={vi.fn()} onMode={vi.fn()} />,
    );
    expect(screen.queryByLabelText("Patrimônio inicial (BRL)")).toBeNull();

    rerender(
      <FireInputs
        value={{ ...createFireForm(), source: "USER_PROVIDED_SCENARIO" }}
        errors={{}}
        onChange={vi.fn()}
        onMode={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Patrimônio inicial (BRL)")).toBeTruthy();
  });
});
