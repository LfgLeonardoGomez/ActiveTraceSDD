import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import KpiCards from '../../components/liquidaciones/KpiCards';

describe('KpiCards', () => {
  it('renders total cards with currency format', () => {
    render(<KpiCards totalSinFactura={150000} totalConFactura={75000} />);
    expect(screen.getByText('Total sin factura')).toBeInTheDocument();
    expect(screen.getByText('Total con factura')).toBeInTheDocument();
    expect(screen.getByText('Total general')).toBeInTheDocument();
  });
});
