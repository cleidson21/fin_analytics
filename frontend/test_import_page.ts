import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ImportPage from "./src/app/wealth/import/page";
import { fetchFromAPI } from "./src/lib/api";

jest.mock("./src/lib/api", () => ({
  fetchFromAPI: jest.fn(),
}));

describe("ImportPage Integration Tests", () => {
  beforeEach(() => {
    (fetchFromAPI as jest.Mock).mockResolvedValue([]);
    // Mock fetch for the upload
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          source: "CEI",
          file_name: "test.csv",
          started_at: "2026-07-13T00:00:00Z",
          finished_at: "2026-07-13T00:00:01Z",
          elapsed_ms: 1000,
          rows_read: 100,
          rows_parsed: 100,
          rows_normalized: 100,
          rows_persisted: 98,
          duplicates_detected: 2,
          warnings: [],
          errors: [],
          success: true
        }),
      })
    ) as jest.Mock;
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("should render upload area and KPIs", async () => {
    render(<ImportPage />);
    expect(screen.getByText("Resumo de Ingestão")).toBeInTheDocument();
    expect(screen.getByText("Arquivos Importados")).toBeInTheDocument();
    expect(screen.getByText("CEI (B3)")).toBeInTheDocument();
    expect(screen.getByText("Open Finance")).toBeInTheDocument();
  });

  it("should handle empty history and show placeholder", async () => {
    render(<ImportPage />);
    await waitFor(() => {
      // Because we mock fetch to fail or return empty, the component uses the mock fallback
      expect(screen.getByText("b3_negociacao_2024.csv")).toBeInTheDocument();
    });
  });

  it("should switch between CEI and Open Finance upload types", async () => {
    render(<ImportPage />);
    const ofBtn = screen.getByText("Open Finance");
    fireEvent.click(ofBtn);
    expect(screen.getByText(/Selecionar Arquivo JSON/i)).toBeInTheDocument();

    const ceiBtn = screen.getByText("CEI (B3)");
    fireEvent.click(ceiBtn);
    expect(screen.getByText(/Selecionar Arquivo CSV/i)).toBeInTheDocument();
  });
});
