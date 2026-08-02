import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import PositionsPage from "./src/app/wealth/positions/page";
import { usePositionsData } from "./src/hooks/usePositionsData";

// Mock do hook
jest.mock("./src/hooks/usePositionsData", () => ({
  usePositionsData: jest.fn(),
}));

const mockData = [
  {
    ticker: "BBAS3",
    institution: "NU INVEST",
    quantity: 100,
    cost_basis: 4500,
    average_cost: 45,
    current_price: 50,
    market_value: 5000,
    unrealized_gain: 500,
    unrealized_gain_percent: 11.11,
  },
  {
    ticker: "MXRF11",
    institution: "XP",
    quantity: 0,
    cost_basis: 0,
    average_cost: 10,
    current_price: 10.5,
    market_value: 0,
    unrealized_gain: 0,
    unrealized_gain_percent: 0,
  }
];

describe("PositionsPage Integration Tests", () => {
  beforeEach(() => {
    (usePositionsData as jest.Mock).mockReturnValue({
      data: mockData,
      isLoading: false,
      isError: false,
    });
  });

  it("should render loading state", () => {
    (usePositionsData as jest.Mock).mockReturnValue({ data: [], isLoading: true, isError: false });
    render(<PositionsPage />);
    expect(screen.getByText(/carregando dados/i)).toBeInTheDocument();
  });

  it("should render error state", () => {
    (usePositionsData as jest.Mock).mockReturnValue({ data: [], isLoading: false, isError: true });
    render(<PositionsPage />);
    expect(screen.getByText(/erro ao carregar as posições/i)).toBeInTheDocument();
  });

  it("should render empty list", () => {
    (usePositionsData as jest.Mock).mockReturnValue({ data: [], isLoading: false, isError: false });
    render(<PositionsPage />);
    expect(screen.getByText(/nenhuma posição em carteira/i)).toBeInTheDocument();
  });

  it("should render large lists and table correctly", () => {
    render(<PositionsPage />);
    expect(screen.getByText("BBAS3")).toBeInTheDocument();
    expect(screen.getByText("MXRF11")).toBeInTheDocument();
    expect(screen.getByText("NU INVEST")).toBeInTheDocument();
  });

  it("should filter by search text", () => {
    render(<PositionsPage />);
    const input = screen.getByPlaceholderText(/Buscar por Ticker/i);
    fireEvent.change(input, { target: { value: "bbas3" } });
    
    expect(screen.getByText("BBAS3")).toBeInTheDocument();
    expect(screen.queryByText("MXRF11")).not.toBeInTheDocument();
  });

  it("should filter by position status (Zerada)", () => {
    render(<PositionsPage />);
    const btn = screen.getByText("Zerada");
    fireEvent.click(btn);
    
    expect(screen.getByText("MXRF11")).toBeInTheDocument();
    expect(screen.queryByText("BBAS3")).not.toBeInTheDocument();
  });

  it("should correctly render KPIs with memoization", () => {
    render(<PositionsPage />);
    // Total market value = 5000 + 0 = 5000
    expect(screen.getByText("R$ 5.000,00")).toBeInTheDocument();
    // Investido = 4500
    expect(screen.getByText("R$ 4.500,00")).toBeInTheDocument();
    // Rentabilidade = 11.11%
    expect(screen.getByText("+11.11%")).toBeInTheDocument();
  });

  it("should render Charts (Top 10 & Distribution)", () => {
    render(<PositionsPage />);
    expect(screen.getByText("Top 10 Posições")).toBeInTheDocument();
    expect(screen.getByText("Distribuição por Instituição")).toBeInTheDocument();
  });
});
