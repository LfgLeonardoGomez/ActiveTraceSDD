import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import UsuarioForm from '../../components/usuarios/UsuarioForm';

describe('UsuarioForm', () => {
  it('submits valid data', async () => {
    const onSubmit = vi.fn();
    render(<UsuarioForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    await userEvent.type(screen.getByLabelText('Nombre'), 'Juan Pérez');
    await userEvent.type(screen.getByLabelText('Email'), 'juan@example.com');
    await userEvent.type(screen.getByLabelText('Regional'), 'Buenos Aires');
    await userEvent.click(screen.getByRole('button', { name: /Guardar cambios/i }));

    expect(onSubmit).toHaveBeenCalled();
  });
});
