import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import CarreraForm from '../../components/estructura/CarreraForm';

describe('CarreraForm', () => {
  it('submits valid data', async () => {
    const onSubmit = vi.fn();
    render(<CarreraForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    await userEvent.type(screen.getByLabelText('Nombre'), 'Ingeniería');
    await userEvent.type(screen.getByLabelText('Código'), 'ING');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));

    expect(onSubmit).toHaveBeenCalled();
  });
});
