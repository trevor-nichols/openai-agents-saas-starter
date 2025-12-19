export function useSubmitContactMutation() {
  return {
    isPending: false,
    mutate: (_body: unknown, opts?: { onSuccess?: () => void; onError?: (error: Error) => void }) => {
      console.log('mock submit contact', _body);
      opts?.onSuccess?.();
    },
  };
}
