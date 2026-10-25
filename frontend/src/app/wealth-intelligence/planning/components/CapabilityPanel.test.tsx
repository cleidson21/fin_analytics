// @vitest-environment jsdom

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { CapabilityResultState } from "./CapabilityPanel";

afterEach(() => cleanup());

describe("CapabilityResultState transient action", () => {
  it("shows the action only for a current completed result", () => {
    const view = render(
      <CapabilityResultState hasResult loading={false} dirty={false} loadingLabel="Calculando" empty={null} action={<button>Mostrar na Visão Geral</button>}>
        <p>Resultado</p>
      </CapabilityResultState>,
    );
    expect(screen.getByRole("button", { name: "Mostrar na Visão Geral" })).toBeTruthy();

    view.rerender(
      <CapabilityResultState hasResult loading={false} dirty loadingLabel="Calculando" empty={null} action={<button>Mostrar na Visão Geral</button>}>
        <p>Resultado</p>
      </CapabilityResultState>,
    );
    expect(screen.queryByRole("button", { name: "Mostrar na Visão Geral" })).toBeNull();
  });

  it("does not expose an action while a replacement response is pending", () => {
    render(
      <CapabilityResultState hasResult loading dirty={false} loadingLabel="Calculando" empty={null} action={<button>Mostrar na Visão Geral</button>}>
        <p>Resultado anterior</p>
      </CapabilityResultState>,
    );
    expect(screen.queryByRole("button", { name: "Mostrar na Visão Geral" })).toBeNull();
  });
});
