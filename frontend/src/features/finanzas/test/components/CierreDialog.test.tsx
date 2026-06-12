import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import CierreDialog from '../../components/liquidaciones/CierreDialog';

describe('CierreDialog', () => {
  it('requires checkbox before confirming', async () => {
    const onConfirm = vi.fn();
    render(
      <CierreDialog
        open={true}
        onClose={vi.fn()}
        onConfirm={onConfirm}
        periodo="2024-06"
      />
    );

    expect(screen.getByRole('heading', { name: /Cerrar liquidación/ })).toBeInTheDocument();
    const confirmButton = screen.getByRole('button', { name: /^Cerrar liquidación$/i });
    expect(confirmButton).toBeDisabled();

    await userEvent.click(screen.getByRole('checkbox'));
    expect(confirmButton).toBeEnabled();

    await userEvent.click(confirmButton);
    expect(onConfirm).toHaveBeenCalled();
  });
});
