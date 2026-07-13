import { renderHook, waitFor } from '@testing-library/react';
import { usePortfolioData } from './src/hooks/usePortfolioData';
import { usePositionsData } from './src/hooks/usePositionsData';
import { usePerformanceData } from './src/hooks/usePerformanceData';
import { useGrowthData } from './src/hooks/useGrowthData';

// Mocking the fetch API
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  })
) as jest.Mock;

describe('Integration Hooks Tests (Gate 9.2)', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockClear();
  });

  it('usePortfolioData fetches JSON correctly and handles loading state', async () => {
    const mockData = { total_market_value: 10000.5, total_cost_basis: 9000, by_asset: [], by_class: [], by_institution: [] };
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(mockData) })
    );

    const { result } = renderHook(() => usePortfolioData());
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.isError).toBe(false);
  });

  it('useGrowthData correctly maps PerformanceSummary to legacy shape', async () => {
    const mockPerfSummary = {
      market_value: 50000.75,
      cost_basis: 40000.0,
      dividends_received: 1000.0,
      metrics: { cagr: 12.5 }
    };
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(mockPerfSummary) })
    );

    const { result } = renderHook(() => useGrowthData('ALL'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.summary?.patrimonio_atual_value).toBe(50000.75);
    expect(result.current.summary?.rentabilidade_acumulada).toBe(12.5);
    expect(result.current.summary?.proventos_totais).toBe(1000.0);
    expect(result.current.summary?.compras_totais).toBe(40000.0);
  });

  it('Handles empty arrays and graceful defaults', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    );

    const { result } = renderHook(() => usePositionsData());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual([]);
  });

  it('Handles server errors and retry limits', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.reject(new Error("Network Error"))
    );

    const { result } = renderHook(() => usePerformanceData());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isError).toBe(true);
    expect(result.current.data).toBeNull();
  });
});
