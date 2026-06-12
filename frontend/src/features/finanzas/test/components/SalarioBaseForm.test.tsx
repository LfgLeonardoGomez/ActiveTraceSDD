import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import SalarioBaseForm from '../../components/salarios/SalarioBaseForm';

describe('SalarioBaseForm', () => {
  it('submits valid data', async () => {
    const onSubmit = vi.fn();
    render(<SalarioBaseForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    await userEvent.type(screen.getByLabelText('Rol'), 'TUTOR');
    await userEvent.type(screen.getByLabelText('Monto'), '50000');
    await userEvent.type(screen.getByLabelText('Vigencia desde'), '2024-01-01');
    await userEvent.type(screen.getByLabelText('Vigencia hasta'), '2024-12-31');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));

    expect(onSubmit).toHaveBeenCalled();
  });
});
