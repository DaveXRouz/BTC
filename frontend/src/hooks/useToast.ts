import { createContext, useContext, useCallback, useRef } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration: number;
}

export interface ToastContextValue {
  toasts: Toast[];
  addToast: (opts: {
    type: ToastType;
    message: string;
    duration?: number;
  }) => void;
  dismissToast: (id: string) => void;
}

export const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return ctx;
}

const MAX_TOASTS = 5;

/**
 * Hook used internally by ToastProvider to manage toast state.
 * Not for direct use — use `useToast()` from context instead.
 */
export function useToastState() {
  const toastsRef = useRef<Toast[]>([]);
  const listenersRef = useRef<Set<() => void>>(new Set());
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(
    new Map(),
  );

  const notify = useCallback(() => {
    listenersRef.current.forEach((fn) => fn());
  }, []);

  const dismissToast = useCallback(
    (id: string) => {
      const timer = timersRef.current.get(id);
      if (timer) {
        clearTimeout(timer);
        timersRef.current.delete(id);
      }
      toastsRef.current = toastsRef.current.filter((t) => t.id !== id);
      notify();
    },
    [notify],
  );

  const addToast = useCallback(
    (opts: { type: ToastType; message: string; duration?: number }) => {
      const id = crypto.randomUUID();
      const duration = opts.duration ?? 5000;
      const toast: Toast = {
        id,
        type: opts.type,
        message: opts.message,
        duration,
      };

      toastsRef.current = [...toastsRef.current, toast];

      // FIFO eviction if over max
      while (toastsRef.current.length > MAX_TOASTS) {
        const evicted = toastsRef.current[0];
        toastsRef.current = toastsRef.current.slice(1);
        const evTimer = timersRef.current.get(evicted.id);
        if (evTimer) {
          clearTimeout(evTimer);
          timersRef.current.delete(evicted.id);
        }
      }

      // Auto-dismiss timer
      const timer = setTimeout(() => {
        dismissToast(id);
      }, duration);
      timersRef.current.set(id, timer);

      notify();
    },
    [dismissToast, notify],
  );

  const subscribe = useCallback((fn: () => void) => {
    listenersRef.current.add(fn);
    return () => {
      listenersRef.current.delete(fn);
    };
  }, []);

  const getToasts = useCallback(() => toastsRef.current, []);

  return { addToast, dismissToast, subscribe, getToasts };
}
