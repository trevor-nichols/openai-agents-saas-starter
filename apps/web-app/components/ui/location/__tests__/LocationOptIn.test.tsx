import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import { LocationOptIn } from '../LocationOptIn';

describe('LocationOptIn', () => {
  it('shows inputs when shareLocation is enabled and propagates changes', () => {
    const handleToggle = vi.fn();
    const handleLocationChange = vi.fn();
    const location = { city: 'Austin', region: '', country: '', timezone: '' };

    render(
      <LocationOptIn
        shareLocation
        onShareLocationChange={handleToggle}
        location={location}
        onLocationChange={handleLocationChange}
        tooltipText="example tooltip"
      />,
    );

    expect(screen.getByLabelText(/bias web search/i)).toBeChecked();
    expect(screen.getByPlaceholderText('City')).toHaveValue('Austin');

    fireEvent.change(screen.getByPlaceholderText('Country'), { target: { value: 'USA' } });
    expect(handleLocationChange).toHaveBeenCalledWith('country', 'USA');
  });

  it('hides inputs when shareLocation is disabled', () => {
    const { queryByPlaceholderText } = render(
      <LocationOptIn
        shareLocation={false}
        onShareLocationChange={vi.fn()}
        location={{}}
        onLocationChange={vi.fn()}
      />,
    );

    expect(queryByPlaceholderText('City')).toBeNull();
  });
});
