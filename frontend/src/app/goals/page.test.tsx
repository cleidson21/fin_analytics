// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const fetchFromAPIMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api", () => ({ fetchFromAPI: fetchFromAPIMock }));
vi.mock("@/components/layout/PageLayout", () => ({
  PageLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import GoalsPage from "./page";

afterEach(() => cleanup());

beforeEach(() => {
  fetchFromAPIMock.mockReset();
  fetchFromAPIMock.mockResolvedValue([]);
});

describe("GoalsPage minimal chrome", () => {
  it("keeps semantic context and removes repeated headings and local journey navigation", async () => {
    render(<GoalsPage />);

    expect(screen.getByRole("heading", { name: "Metas" })).toBeTruthy();
    expect(screen.queryByText("Seus objetivos financeiros")).toBeNull();
    expect(screen.queryByRole("link", { name: "Planejamento" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Independência Financeira" })).toBeNull();
    expect(screen.getByRole("button", { name: "Nova meta" })).toBeTruthy();

    await waitFor(() => expect(fetchFromAPIMock).toHaveBeenCalledWith("/goals"));
  });
});
