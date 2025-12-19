export type UiToolStatus =
  | 'input-streaming'
  | 'input-available'
  | 'output-available'
  | 'output-error';

const STATUS_RANK: Record<UiToolStatus, number> = {
  'input-streaming': 0,
  'input-available': 1,
  'output-available': 2,
  'output-error': 3,
};

export function upgradeToolStatus(current: UiToolStatus, next: UiToolStatus): UiToolStatus {
  return STATUS_RANK[next] > STATUS_RANK[current] ? next : current;
}

export function uiToolStatusFromProviderStatus(status: string): UiToolStatus {
  if (status === 'completed') return 'output-available';
  if (status === 'failed') return 'output-error';
  return 'input-available';
}

