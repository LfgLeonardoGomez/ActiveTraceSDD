import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import VigenciaConflictAlert from '../../components/salarios/VigenciaConflictAlert';

describe('VigenciaConflictAlert', () => {
  it('renders warning message', () => {
    render(<VigenciaConflictAlert message="El rango de fechas se solapa con otro salario base." />);
    expect(screen.getByRole('alert')).toHaveTextContent('El rango de fechas se solapa');
  });
});
