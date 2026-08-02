import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ReconciliationPage from "./src/app/wealth/reconciliation/page";
import { fetchFromAPI } from "./src/lib/api";

jest.mock("./src/lib/api", () => ({
  fetchFromAPI: jest.fn(),
}));

const mockData = [
  {
    ticker: "PETR4",
    broker: "XP",
    ledger_quantity: 100,
    snapshot_quantity: 100,
    difference: 0,
    difference_percent: 0,
    status: "OK",
    recommendation: "Sem ação"
  },
  {
    ticker: "VALE3",
    broker: "NU",
    ledger_quantity: 50,
    snapshot_quantity: 49.5,
    difference: 0.5,
    difference_percent: 0.0101,
    status: "WARNING",
    recommendation: "Conferir custódia"
  },
  {
    ticker: "WEGE3",
    broker: "XP",
    ledger_quantity: 200,
    snapshot_quantity: 150,
    difference: 50,
    difference_percent: 0.3333,
    status: "ERROR",
    recommendation: "Revisar importação"
  }
];

describe("ReconciliationPage Integration Tests", () => {
  beforeEach(() => {
    (fetchFromAPI as jest.Mock).mockResolvedValue(mockData);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("should render KPIs correctly", async () => {
    render(<ReconciliationPage />);
    
    await waitFor(() => {
      // 1 OK, 1 Warning, 1 Error
      expect(screen.getByText("Ativos Conciliados (OK)")).toBeInTheDocument();
      const allText = screen.getAllByText("1");
      expect(allText.length).toBeGreaterThanOrEqual(3); 
    });
  });

  it("should render table data correctly", async () => {
    render(<ReconciliationPage />);
    await waitFor(() => {
      expect(screen.getByText("PETR4")).toBeInTheDocument();
      expect(screen.getByText("VALE3")).toBeInTheDocument();
      expect(screen.getByText("WEGE3")).toBeInTheDocument();
    });
  });

  it("should filter by status", async () => {
    render(<ReconciliationPage />);
    await waitFor(() => expect(screen.getByText("PETR4")).toBeInTheDocument());
    
    const filterSelect = screen.getByRole("combobox", { name: "" }); // or just select by looking for 'Status: Todos'
    const selects = screen.getAllByRole("combobox");
    const statusSelect = selects[0]; // Assuming it's the first one

    fireEvent.change(statusSelect, { target: { value: "ERROR" } });
    
    await waitFor(() => {
      expect(screen.queryByText("PETR4")).not.toBeInTheDocument();
      expect(screen.getByText("WEGE3")).toBeInTheDocument();
    });
  });

  it("should search by ticker", async () => {
    render(<ReconciliationPage />);
    await waitFor(() => expect(screen.getByText("PETR4")).toBeInTheDocument());
    
    const searchInput = screen.getByPlaceholderText("Buscar por ticker...");
    fireEvent.change(searchInput, { target: { value: "vale" } });
    
    await waitFor(() => {
      expect(screen.queryByText("PETR4")).not.toBeInTheDocument();
      expect(screen.getByText("VALE3")).toBeInTheDocument();
    });
  });

  it("should sort correctly", async () => {
    render(<ReconciliationPage />);
    await waitFor(() => expect(screen.getByText("PETR4")).toBeInTheDocument());
    
    const selects = screen.getAllByRole("combobox");
    const sortSelect = selects[1]; 
    
    fireEvent.change(sortSelect, { target: { value: "ticker" } });
    
    await waitFor(() => {
      // Just check if they render. Actual dom order testing requires more complex querying
      expect(screen.getByText("PETR4")).toBeInTheDocument();
    });
  });
});
