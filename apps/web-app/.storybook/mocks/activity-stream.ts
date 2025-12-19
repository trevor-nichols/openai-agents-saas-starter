type OpenParams = { onOpen?: () => void };

export const openActivityStream = ({ onOpen }: OpenParams) => {
  onOpen?.();
  return { close: () => {} } as EventSource;
};
