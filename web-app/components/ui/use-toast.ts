'use client';

import { useCallback } from 'react';
import { toast as sonnerToast, type ExternalToast } from 'sonner';

type ToastVariant = 'success' | 'error' | 'info';

interface ToastOptions extends Omit<ExternalToast, 'type'> {
  title: string;
}

export function useToast() {
  const showToast = useCallback((variant: ToastVariant, { title, ...options }: ToastOptions) => {
    switch (variant) {
      case 'success':
        return sonnerToast.success(title, options);
      case 'error':
        return sonnerToast.error(title, options);
      case 'info':
      default:
        return sonnerToast.info(title, options);
    }
  }, []);

  return {
    success: (options: ToastOptions) => showToast('success', options),
    error: (options: ToastOptions) => showToast('error', options),
    info: (options: ToastOptions) => showToast('info', options),
    message: (message: string, options?: ExternalToast) => sonnerToast(message, options),
    dismiss: (id?: number | string) => sonnerToast.dismiss(id),
  };
}
