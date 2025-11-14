export function formatDateLabel(timestamp: string | null | undefined): string {
  if (!timestamp) {
    return 'Updating now';
  }
  try {
    const formatter = new Intl.DateTimeFormat('en-US', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
    return formatter.format(new Date(timestamp));
  } catch (_error) {
    return timestamp;
  }
}

export function formatPrice(amount: number | null | undefined, currency = 'USD'): string {
  if (amount === null || amount === undefined || Number.isNaN(amount)) {
    return 'Custom';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}
