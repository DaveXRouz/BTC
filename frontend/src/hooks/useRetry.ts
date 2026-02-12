import { useState, useCallback, useRef } from "react";

interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  backoffFactor?: number;
  onRetry?: (attempt: number, error: Error) => void;
}

interface RetryResult<T> {
  execute: () => Promise<T>;
  isRetrying: boolean;
  attempt: number;
  reset: () => void;
}

export function useRetry<T>(
  asyncFn: () => Promise<T>,
  options?: RetryOptions,
): RetryResult<T> {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 10000,
    backoffFactor = 2,
    onRetry,
  } = options ?? {};

  const [isRetrying, setIsRetrying] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const abortRef = useRef(false);

  const reset = useCallback(() => {
    setAttempt(0);
    setIsRetrying(false);
    abortRef.current = false;
  }, []);

  const execute = useCallback(async (): Promise<T> => {
    abortRef.current = false;
    setAttempt(1);

    for (let i = 0; i < maxRetries; i++) {
      try {
        const result = await asyncFn();
        setIsRetrying(false);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));

        // Do not retry client errors (4xx)
        if (
          "isClientError" in error &&
          (error as { isClientError: boolean }).isClientError
        ) {
          setIsRetrying(false);
          throw error;
        }

        if (i < maxRetries - 1 && !abortRef.current) {
          setIsRetrying(true);
          setAttempt(i + 2);
          onRetry?.(i + 1, error);

          // Exponential backoff with jitter
          const rawDelay = baseDelay * Math.pow(backoffFactor, i);
          const clampedDelay = Math.min(rawDelay, maxDelay);
          const jitteredDelay = clampedDelay * (0.5 + Math.random() * 0.5);

          await new Promise((resolve) => setTimeout(resolve, jitteredDelay));
        } else {
          setIsRetrying(false);
          throw error;
        }
      }
    }

    // Should never reach here, but TypeScript needs it
    throw new Error("Retry exhausted");
  }, [asyncFn, maxRetries, baseDelay, maxDelay, backoffFactor, onRetry]);

  return { execute, isRetrying, attempt, reset };
}
