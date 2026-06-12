import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ScopeBadge from '../../components/auditoria/ScopeBadge';

describe('ScopeBadge', () => {
  it('renders when propio', () => {
    render(<ScopeBadge isPropio={true} />);
    expect(screen.getByText('Vista personal')).toBeInTheDocument();
  });

  it('does not render when not propio', () => {
    render(<ScopeBadge isPropio={false} />);
    expect(screen.queryByText('Vista personal')).not.toBeInTheDocument();
  });
});
