import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useOnlineStatus } from "@/hooks/useOnlineStatus";

export function OfflineBanner() {
  const { t } = useTranslation();
  const isOnline = useOnlineStatus();
  const [showReconnected, setShowReconnected] = useState(false);
  const wasOfflineRef = useRef(false);

  useEffect(() => {
    if (!isOnline) {
      wasOfflineRef.current = true;
    } else if (wasOfflineRef.current) {
      // Just came back online
      wasOfflineRef.current = false;
      setShowReconnected(true);
      const timer = setTimeout(() => setShowReconnected(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [isOnline]);

  if (isOnline && !showReconnected) return null;

  return (
    <div
      role="alert"
      className={`fixed top-0 inset-x-0 z-50 px-4 py-2 text-center text-sm border-b ${
        isOnline
          ? "bg-nps-success/10 border-nps-success text-nps-success"
          : "bg-nps-warning/10 border-nps-warning text-nps-warning"
      }`}
    >
      {isOnline ? t("common.back_online") : t("common.offline_message")}
    </div>
  );
}
