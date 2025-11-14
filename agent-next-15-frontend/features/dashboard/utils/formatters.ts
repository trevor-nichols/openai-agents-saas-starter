export function formatCurrency(amountCents?: number | null, currency: string = 'USD') {
  if (amountCents == null) {
    return '—';
  }
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amountCents / 100);
}
