import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ImportPage from "./src/app/wealth/import/page";
import { fetchFromAPI } from "./src/lib/api";

jest.mock("./src/lib/api", () => ({
  fetchFromAPI: jest.fn(),
}));

const mockReport = {
  source: "CEI",
  file_name: "test.csv",
  started_at: "2026-07-13T10:00:00Z",
  finished_at: "2026-07-13T10:00:02Z",
  elapsed_ms: 1000,
  rows_read: 100,
  rows_parsed: 100,
  rows_normalized: 100,
  rows_persisted: 90,
  duplicates_detected: 10,
  warnings: [],
  errors: [],
  success: true
};

describe("ImportPage Real Upload Tests", () => {
  beforeEach(() => {
    // mock history endpoint
    (fetchFromAPI as jest.Mock).mockImplementation((url, options) => {
      if (url === "/investments/import/history") {
        return Promise.resolve([]);
      }
      if (options && options.method === "POST") {
        return Promise.resolve(mockReport);
      }
      return Promise.resolve(null);
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("should trigger real fetchFromAPI when file is dropped", async () => {
    render(<ImportPage />);
    
    // Simulate drop
    const dropzone = screen.getByText("Clique ou arraste arquivos").closest("div");
    expect(dropzone).toBeInTheDocument();
    
    const file = new File(["dummy content"], "test.csv", { type: "text/csv" });
    Object.defineProperty(file, 'size', { value: 1024 });
    
    fireEvent.drop(dropzone!, {
      dataTransfer: {
        files: [file]
      }
    });
    
    await waitFor(() => {
      expect(fetchFromAPI).toHaveBeenCalledWith("/investments/import/cei", expect.objectContaining({
        method: "POST"
      }));
    });
    
    // After upload finishes, KPIs should update based on the mockReport
    await waitFor(() => {
      // 90 persistidos
      expect(screen.getByText("90")).toBeInTheDocument();
      // 10 duplicados
      expect(screen.getByText("10")).toBeInTheDocument();
    });
  });
});
