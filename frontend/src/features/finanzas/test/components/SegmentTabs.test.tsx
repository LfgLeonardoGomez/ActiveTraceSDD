import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import SegmentTabs from '@/shared/components/SegmentTabs';

describe('SegmentTabs', () => {
  const segments = [
    { key: 'general', label: 'General', count: 10 },
    { key: 'nexo', label: 'NEXO' },
  ];

  it('renders segments and calls onChange when clicked', async () => {
    const onChange = vi.fn();
    render(<SegmentTabs segments={segments} active="general" onChange={onChange} />);

    expect(screen.getByText('General')).toBeInTheDocument();
    expect(screen.getByText('NEXO')).toBeInTheDocument();

    await userEvent.click(screen.getByText('NEXO'));
    expect(onChange).toHaveBeenCalledWith('nexo');
  });
});
