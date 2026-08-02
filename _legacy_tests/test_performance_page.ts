import { render, screen, fireEvent } from "@testing-library/react";
import PerformancePage from "./src/app/wealth/performance/page";
import { usePerformanceData } from "./src/hooks/usePerformanceData";

jest.mock("./src/hooks/usePerformanceData", () => ({
  usePerformanceData: jest.fn(),
}));

const mockData = {
  cost_basis: 10000,
  market_value: 12000,
  holding_days: 365,
  metrics: {
    unrealized_gain: 2000,
    realized_gain: 500,
    total_gain: 2500,
    dividends_received: 500,
    total_return: 3000,
    unrealized_return_pct: 20.0,
    realized_return_pct: 5.0,
    total_return_pct: 30.0,
    yield_on_cost: 5.0,
    cagr: 30.0,
    annualized_return_pct: 30.0,
    monthly_return_pct: 2.21,
    daily_return_pct: 0.07,
    mwr: 28.5,
    twr: 31.2,
  },
};

describe("PerformancePage Integration Tests", () => {
  beforeEach(() => {
    (usePerformanceData as jest.Mock).mockReturnValue({
      data: mockData,
      isLoading: false,
      isError: false,
    });
  });

  it("should render loading state correctly", () => {
    (usePerformanceData as jest.Mock).mockReturnValue({ data: null, isLoading: true, isError: false });
    render(<PerformancePage />);
    expect(screen.getByText(/carregando dados/i)).toBeInTheDocument();
  });

  it("should render error state and retry button", () => {
    (usePerformanceData as jest.Mock).mockReturnValue({ data: null, isLoading: false, isError: true });
    render(<PerformancePage />);
    expect(screen.getByText(/erro ao carregar os dados/i)).toBeInTheDocument();
    expect(screen.getByText(/tentar novamente/i)).toBeInTheDocument();
  });

  it("should render empty state if metrics are missing", () => {
    (usePerformanceData as jest.Mock).mockReturnValue({ data: { ...mockData, metrics: null }, isLoading: false, isError: false });
    render(<PerformancePage />);
    expect(screen.getByText(/nenhuma métrica computada/i)).toBeInTheDocument();
  });

  it("should render KPIs correctly", () => {
    render(<PerformancePage />);
    // Check CAGR
    expect(screen.getByText("30.00%")).toBeInTheDocument();
    // Check MWR
    expect(screen.getByText("28.50%")).toBeInTheDocument();
    // Check Unrealized Gain
    expect(screen.getByText("R$ 2.000,00")).toBeInTheDocument();
  });

  it("should format negative metrics correctly", () => {
    (usePerformanceData as jest.Mock).mockReturnValue({
      data: {
        ...mockData,
        metrics: {
          ...mockData.metrics,
          cagr: -15.5,
          total_return: -1500,
        }
      },
      isLoading: false,
      isError: false,
    });
    render(<PerformancePage />);
    expect(screen.getByText("-15.50%")).toBeInTheDocument();
    expect(screen.getByText("-R$ 1.500,00")).toBeInTheDocument();
  });

  it("should render technical table", () => {
    render(<PerformancePage />);
    expect(screen.getByText("Holding Days")).toBeInTheDocument();
    expect(screen.getByText("365 dias")).toBeInTheDocument();
    expect(screen.getByText("TWR (Time-Weighted Return)")).toBeInTheDocument();
    expect(screen.getByText("31.20%")).toBeInTheDocument();
  });
});
