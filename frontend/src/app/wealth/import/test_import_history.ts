import { render, screen, fireEvent } from '@testing-library/react';
import ImportPage from './page';
import { fetchFromAPI } from '@/lib/api';

// Mock API call
jest.mock('@/lib/api', () => ({
  fetchFromAPI: jest.fn(),
}));

describe('Import Dashboard - Gate 10.2 Audit', () => {
  const mockLogs = [
    {
      id: 'log-1',
      user_id: 'SINGLE_USER',
      created_at: '2026-07-13T10:00:00Z',
      filename: 'test1.csv',
      file_type: 'CSV',
      file_size: 1024,
      checksum: 'hash1',
      parser: 'CSVParser',
      rows_read: 100,
      rows_imported: 90,
      rows_duplicated: 10,
      rows_failed: 0,
      processing_time_ms: 1500,
      status: 'SUCCESS',
    },
    {
      id: 'log-2',
      user_id: 'SINGLE_USER',
      created_at: '2026-07-13T11:00:00Z',
      filename: 'test2.csv',
      file_type: 'CSV',
      file_size: 2048,
      checksum: 'hash2',
      parser: 'CSVParser',
      rows_read: 50,
      rows_imported: 0,
      rows_duplicated: 0,
      rows_failed: 50,
      processing_time_ms: 500,
      status: 'FAILED',
      error_message: 'Invalid format',
    }
  ];

  beforeEach(() => {
    (fetchFromAPI as jest.Mock).mockResolvedValue(mockLogs);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders KPI correctly with data from ImportLog', async () => {
    render(<ImportPage />);
    
    // Wait for the mock to resolve and update state
    const filesKpi = await screen.findByText('2'); // 2 logs
    expect(filesKpi).toBeInTheDocument();
    
    // trades = 90 + 0 = 90
    const tradesKpi = await screen.findByText('90');
    expect(tradesKpi).toBeInTheDocument();
    
    // duplicated = 10 + 0 = 10
    const dupsKpi = await screen.findByText('10');
    expect(dupsKpi).toBeInTheDocument();
  });

  it('opens detail modal on row click', async () => {
    render(<ImportPage />);
    
    // Find the row for test1.csv and click
    const row = await screen.findByText('test1.csv');
    fireEvent.click(row);
    
    // The modal should appear with the checksum and details
    const detailTitle = screen.getByText('Detalhes da Importação');
    expect(detailTitle).toBeInTheDocument();
    
    const checksumHash = screen.getByText('hash1');
    expect(checksumHash).toBeInTheDocument();
  });
});
