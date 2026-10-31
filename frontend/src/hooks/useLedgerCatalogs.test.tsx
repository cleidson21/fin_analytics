// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, renderHook, waitFor } from "@testing-library/react";

vi.stubEnv("NEXT_PUBLIC_API_URL", "https://example.test/api/v1");
const { useAccounts } = await import("./useAccounts");
const { useCategoriesAdmin } = await import("./useCategoriesAdmin");
const { useAuditRunDetail } = await import("./useAudit");
beforeEach(() => { localStorage.clear(); localStorage.setItem("fin_token", "synthetic-token"); });
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it("distinguishes account authorization denial from an empty catalog", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 403 })));
  const { result } = renderHook(() => useAccounts());
  await waitFor(() => expect(result.current.error).toContain("Autorização financeira pendente"));
  expect(result.current.data).toEqual([]);
  expect(localStorage.getItem("fin_token")).toBe("synthetic-token");
});

it("reads the actual flat private category DTO, preserves scoped counts and applies filtering/pagination", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([
    { provider: "pierre", name: "Food", normalized_name: "food", transaction_count: 3 },
    { provider: "pierre", name: "Travel", normalized_name: "travel", transaction_count: 1 },
  ]), { status: 200 })));
  const { result } = renderHook(() => useCategoriesAdmin({ limit: 10, offset: 0, search: "food" }));
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  expect(result.current.total).toBe(1);
  expect(result.current.data[0]).toMatchObject({ categoria: "Food", quantidade_transacoes: 3 });
});

it("does not present an authorization failure as an empty category catalog", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 403 })));
  const { result } = renderHook(() => useCategoriesAdmin({ limit: 10, offset: 0 }));
  await waitFor(() => expect(result.current.error?.message).toContain("Autorização financeira pendente"));
});

it("clears a previous import detail and reports a later scope denial without logging out", async () => {
  vi.stubGlobal("fetch", vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({ id: "synthetic-run-a", file_name: "Synthetic" }), { status: 200 }))
    .mockResolvedValueOnce(new Response("{}", { status: 403 })));
  const { result, rerender } = renderHook(({ id }) => useAuditRunDetail(id), { initialProps: { id: "synthetic-run-a" } });
  await waitFor(() => expect(result.current.data?.id).toBe("synthetic-run-a"));
  rerender({ id: "synthetic-run-b" });
  await waitFor(() => expect(result.current.error).toContain("Autorização financeira pendente"));
  expect(result.current.data).toBeNull();
  expect(localStorage.getItem("fin_token")).toBe("synthetic-token");
});
