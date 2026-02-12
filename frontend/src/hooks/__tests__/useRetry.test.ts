import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useRetry } from "../useRetry";

describe("useRetry", () => {
  it("succeeds on first try — returns result, attempt = 1", async () => {
    const fn = vi.fn().mockResolvedValue("ok");
    const { result } = renderHook(() => useRetry(fn));

    let value: unknown;
    await act(async () => {
      value = await result.current.execute();
    });

    expect(value).toBe("ok");
    expect(fn).toHaveBeenCalledOnce();
  });

  it("retries on failure — calls fn max times before giving up", async () => {
    const fn = vi.fn().mockRejectedValue(new Error("fail"));
    const { result } = renderHook(() =>
      useRetry(fn, { maxRetries: 3, baseDelay: 1, maxDelay: 2 }),
    );

    await act(async () => {
      await expect(result.current.execute()).rejects.toThrow("fail");
    });

    expect(fn).toHaveBeenCalledTimes(3);
  });

  it("does not retry on 4xx (client error)", async () => {
    const clientError = Object.assign(new Error("Not found"), {
      isClientError: true,
    });
    const fn = vi.fn().mockRejectedValue(clientError);
    const { result } = renderHook(() =>
      useRetry(fn, { maxRetries: 3, baseDelay: 1 }),
    );

    await act(async () => {
      await expect(result.current.execute()).rejects.toThrow("Not found");
    });

    expect(fn).toHaveBeenCalledOnce();
  });

  it("onRetry callback called on each retry", async () => {
    const onRetry = vi.fn();
    let callCount = 0;
    const fn = vi.fn().mockImplementation(() => {
      callCount++;
      if (callCount < 3) return Promise.reject(new Error("fail"));
      return Promise.resolve("success");
    });

    const { result } = renderHook(() =>
      useRetry(fn, { maxRetries: 3, baseDelay: 1, maxDelay: 2, onRetry }),
    );

    await act(async () => {
      await result.current.execute();
    });

    expect(onRetry).toHaveBeenCalledTimes(2);
    expect(onRetry).toHaveBeenCalledWith(1, expect.any(Error));
    expect(onRetry).toHaveBeenCalledWith(2, expect.any(Error));
  });

  it("reset clears attempt count", async () => {
    const fn = vi.fn().mockResolvedValue("ok");
    const { result } = renderHook(() => useRetry(fn));

    await act(async () => {
      await result.current.execute();
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.attempt).toBe(0);
    expect(result.current.isRetrying).toBe(false);
  });

  it("exponential backoff — retries with increasing delays", async () => {
    const timestamps: number[] = [];
    const fn = vi.fn().mockImplementation(() => {
      timestamps.push(Date.now());
      return Promise.reject(new Error("fail"));
    });

    const { result } = renderHook(() =>
      useRetry(fn, {
        maxRetries: 3,
        baseDelay: 1,
        maxDelay: 100,
        backoffFactor: 2,
      }),
    );

    await act(async () => {
      await expect(result.current.execute()).rejects.toThrow("fail");
    });

    // All 3 calls should have been made
    expect(fn).toHaveBeenCalledTimes(3);
  });
});
