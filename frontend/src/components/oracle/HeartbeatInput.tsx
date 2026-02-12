import { useState, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";

interface HeartbeatInputProps {
  value: number | null;
  onChange: (bpm: number | null) => void;
}

type InputMode = "manual" | "tap";

const MIN_BPM = 30;
const MAX_BPM = 220;
const MIN_TAPS = 5;
const MAX_INTERVAL_MS = 3000;

export function HeartbeatInput({ value, onChange }: HeartbeatInputProps) {
  const { t } = useTranslation();
  const [mode, setMode] = useState<InputMode>("manual");
  const [manualValue, setManualValue] = useState(value?.toString() ?? "");
  const [manualError, setManualError] = useState<string | null>(null);
  const [tapCount, setTapCount] = useState(0);
  const [tapBpm, setTapBpm] = useState<number | null>(null);
  const [animating, setAnimating] = useState(false);

  const tapTimestamps = useRef<number[]>([]);

  function handleManualChange(raw: string) {
    setManualValue(raw);
    setManualError(null);
    if (raw === "") {
      onChange(null);
      return;
    }
    const num = Number(raw);
    if (Number.isNaN(num)) return;
    if (num < MIN_BPM) {
      setManualError(t("oracle.heartbeat_error_low"));
      return;
    }
    if (num > MAX_BPM) {
      setManualError(t("oracle.heartbeat_error_high"));
      return;
    }
    onChange(Math.round(num));
  }

  function handleManualBlur() {
    if (manualValue === "") return;
    const num = Number(manualValue);
    if (Number.isNaN(num)) return;
    if (num < MIN_BPM) {
      setManualError(t("oracle.heartbeat_error_low"));
    } else if (num > MAX_BPM) {
      setManualError(t("oracle.heartbeat_error_high"));
    }
  }

  function handleClear() {
    setManualValue("");
    setManualError(null);
    onChange(null);
  }

  const handleTap = useCallback(() => {
    const now = performance.now();
    tapTimestamps.current.push(now);

    // Trigger animation
    setAnimating(true);
    setTimeout(() => setAnimating(false), 200);

    // Keep only last 6 timestamps (5 intervals)
    if (tapTimestamps.current.length > 6) {
      tapTimestamps.current = tapTimestamps.current.slice(-6);
    }

    const count = tapTimestamps.current.length;
    setTapCount(count);

    if (count >= 2) {
      // Compute intervals, discard those > MAX_INTERVAL_MS
      const intervals: number[] = [];
      for (let i = 1; i < tapTimestamps.current.length; i++) {
        const gap = tapTimestamps.current[i] - tapTimestamps.current[i - 1];
        if (gap <= MAX_INTERVAL_MS) {
          intervals.push(gap);
        }
      }
      if (intervals.length > 0) {
        const avgMs = intervals.reduce((s, v) => s + v, 0) / intervals.length;
        const bpm = Math.round(60000 / avgMs);
        if (bpm >= MIN_BPM && bpm <= MAX_BPM) {
          setTapBpm(bpm);
        } else {
          setTapBpm(null);
        }
      }
    }
  }, []);

  function handleTapConfirm() {
    if (tapBpm !== null) {
      onChange(tapBpm);
      setManualValue(tapBpm.toString());
      setMode("manual");
      resetTap();
    }
  }

  function resetTap() {
    tapTimestamps.current = [];
    setTapCount(0);
    setTapBpm(null);
  }

  const tapMessage =
    tapCount < 2
      ? t("oracle.heartbeat_tap_minimum")
      : tapCount < MIN_TAPS
        ? t("oracle.heartbeat_tap_count", { count: tapCount })
        : tapBpm !== null
          ? t("oracle.heartbeat_tap_result", { bpm: tapBpm })
          : t("oracle.heartbeat_tap_count", { count: tapCount });

  return (
    <div className="space-y-2">
      {/* Mode tabs */}
      <div
        className="flex gap-1"
        role="tablist"
        aria-label={t("oracle.heartbeat_label")}
      >
        <button
          type="button"
          role="tab"
          aria-selected={mode === "manual"}
          onClick={() => setMode("manual")}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            mode === "manual"
              ? "bg-nps-oracle-accent text-nps-bg font-medium"
              : "text-nps-text-dim hover:text-nps-text"
          }`}
        >
          {t("oracle.heartbeat_manual_mode")}
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "tap"}
          onClick={() => setMode("tap")}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            mode === "tap"
              ? "bg-nps-oracle-accent text-nps-bg font-medium"
              : "text-nps-text-dim hover:text-nps-text"
          }`}
        >
          {t("oracle.heartbeat_tap_mode")}
        </button>
      </div>

      {mode === "manual" ? (
        <div className="flex items-center gap-2">
          <input
            type="number"
            min={MIN_BPM}
            max={MAX_BPM}
            value={manualValue}
            onChange={(e) => handleManualChange(e.target.value)}
            onBlur={handleManualBlur}
            placeholder={t("oracle.heartbeat_placeholder")}
            aria-label={t("oracle.heartbeat_label")}
            aria-invalid={!!manualError}
            className={`flex-1 bg-nps-bg-input border rounded px-3 py-2 text-sm text-nps-text focus:outline-none focus:border-nps-oracle-accent ${
              manualError ? "border-nps-error" : "border-nps-border"
            }`}
            data-testid="heartbeat-manual-input"
          />
          {manualValue && (
            <button
              type="button"
              onClick={handleClear}
              className="px-2 py-2 text-xs text-nps-text-dim hover:text-nps-text border border-nps-border rounded"
              aria-label="Clear heart rate"
              data-testid="heartbeat-clear"
            >
              ✕
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          <button
            type="button"
            onClick={handleTap}
            aria-label={t("oracle.heartbeat_tap_instruction")}
            className={`w-full py-6 text-2xl rounded-lg border-2 border-red-500/30 bg-red-500/5 hover:bg-red-500/10 transition-all ${
              animating ? "scale-95" : "scale-100"
            }`}
            data-testid="heartbeat-tap-button"
          >
            <span
              className={`inline-block transition-transform ${animating ? "scale-125" : ""}`}
            >
              ❤️
            </span>
          </button>

          <p
            className="text-xs text-nps-text-dim text-center"
            data-testid="tap-message"
          >
            {tapMessage}
          </p>

          <div className="flex gap-2">
            {tapCount >= MIN_TAPS && tapBpm !== null && (
              <button
                type="button"
                onClick={handleTapConfirm}
                className="flex-1 px-3 py-1.5 text-xs bg-nps-oracle-accent text-nps-bg rounded hover:bg-nps-oracle-accent/80"
                data-testid="heartbeat-tap-confirm"
              >
                {t("oracle.heartbeat_tap_confirm")}
              </button>
            )}
            {tapCount > 0 && (
              <button
                type="button"
                onClick={resetTap}
                className="px-3 py-1.5 text-xs text-nps-text-dim border border-nps-border rounded hover:text-nps-text"
                data-testid="heartbeat-tap-reset"
              >
                {t("oracle.heartbeat_tap_reset")}
              </button>
            )}
          </div>
        </div>
      )}

      {manualError && (
        <p
          className="text-nps-error text-xs"
          role="alert"
          data-testid="heartbeat-error"
        >
          {manualError}
        </p>
      )}

      <p className="text-xs text-nps-text-dim">
        {t("oracle.heartbeat_optional")}
      </p>
    </div>
  );
}
