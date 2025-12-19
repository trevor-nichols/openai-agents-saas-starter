export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** exponent;
  return `${value.toFixed(value >= 10 || exponent === 0 ? 0 : 1)} ${units[exponent]}`;
}

export function formatToolLabel(tool: string | null | undefined): string {
  switch (tool) {
    case 'image_generation':
      return 'Image generation';
    case 'code_interpreter':
      return 'Code interpreter';
    case 'user_upload':
      return 'User upload';
    default:
      return 'Unknown';
  }
}
