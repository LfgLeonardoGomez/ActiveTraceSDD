import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MonitorGeneralTable } from '../../components/monitor/MonitorGeneralTable';

vi.mock('../../hooks/useMonitorCoordinacion', () => ({
  useMonitorGeneral: vi.fn(),
  useAuditoria: vi.fn(),
}));

import { useMonitorGeneral } from '../../hooks/useMonitorCoordinacion';

const defaultProps = {
  filters: {},
  onPageChange: vi.fn(),
  page: 1,
};

describe('MonitorGeneralTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading skeleton with filter pills and table rows', () => {
    vi.mocked(useMonitorGeneral).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as never);

    const { container } = render(<MonitorGeneralTable {...defaultProps} />);

    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThanOrEqual(4);
  });

  it('renders empty state correctly', () => {
    vi.mocked(useMonitorGeneral).mockReturnValue({
      data: { data: [], total: 0, page: 1, total_pages: 1 },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<MonitorGeneralTable {...defaultProps} />);
    expect(screen.getByText('No se encontraron resultados')).toBeInTheDocument();
    expect(
      screen.getByText('Ajustá los filtros o importá datos para comenzar'),
    ).toBeInTheDocument();
  });
});
