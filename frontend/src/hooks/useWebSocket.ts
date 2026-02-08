import { useEffect, useRef } from "react";
import { wsClient } from "@/services/websocket";
import type { EventType } from "@/types";

/**
 * React hook for subscribing to WebSocket events.
 * Automatically cleans up on unmount.
 */
export function useWebSocket(
  event: EventType,
  handler: (data: Record<string, unknown>) => void,
) {
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  useEffect(() => {
    const unsubscribe = wsClient.on(event, (data) => {
      handlerRef.current(data);
    });
    return unsubscribe;
  }, [event]);
}

/**
 * Connect WebSocket on mount, disconnect on unmount.
 * Call once in the root Layout component.
 */
export function useWebSocketConnection() {
  useEffect(() => {
    wsClient.connect();
    return () => wsClient.disconnect();
  }, []);
}
