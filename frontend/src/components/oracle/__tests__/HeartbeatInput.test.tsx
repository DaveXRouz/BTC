import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { HeartbeatInput } from "../HeartbeatInput";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const map: Record<string, string> = {
        "oracle.heartbeat_label": "Resting Heart Rate",
        "oracle.heartbeat_placeholder": "BPM (30-220)",
        "oracle.heartbeat_optional": "Optional",
        "oracle.heartbeat_tap_mode": "Tap to Measure",
        "oracle.heartbeat_manual_mode": "Enter Manually",
        "oracle.heartbeat_tap_instruction": "Tap in rhythm",
        "oracle.heartbeat_tap_minimum": "Tap at least 5 times",
        "oracle.heartbeat_error_low": "BPM must be at least 30",
        "oracle.heartbeat_error_high": "BPM must be at most 220",
        "oracle.heartbeat_tap_reset": "Start Over",
        "oracle.heartbeat_tap_confirm": "Use This BPM",
      };
      let text = map[key] ?? key;
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          text = text.replace(`{{${k}}}`, String(v));
        }
      }
      return text;
    },
  }),
}));

describe("HeartbeatInput", () => {
  it("renders manual input mode by default", () => {
    render(<HeartbeatInput value={null} onChange={() => {}} />);
    expect(screen.getByTestId("heartbeat-manual-input")).toBeDefined();
  });

  it("accepts valid BPM in range 30-220", () => {
    const onChange = vi.fn();
    render(<HeartbeatInput value={null} onChange={onChange} />);
    const input = screen.getByTestId("heartbeat-manual-input");
    fireEvent.change(input, { target: { value: "72" } });
    expect(onChange).toHaveBeenCalledWith(72);
  });

  it("rejects BPM below 30", () => {
    const onChange = vi.fn();
    render(<HeartbeatInput value={null} onChange={onChange} />);
    const input = screen.getByTestId("heartbeat-manual-input");
    fireEvent.change(input, { target: { value: "20" } });
    expect(screen.getByTestId("heartbeat-error")).toBeDefined();
    expect(screen.getByTestId("heartbeat-error").textContent).toBe(
      "BPM must be at least 30",
    );
  });

  it("rejects BPM above 220", () => {
    const onChange = vi.fn();
    render(<HeartbeatInput value={null} onChange={onChange} />);
    const input = screen.getByTestId("heartbeat-manual-input");
    fireEvent.change(input, { target: { value: "300" } });
    expect(screen.getByTestId("heartbeat-error")).toBeDefined();
    expect(screen.getByTestId("heartbeat-error").textContent).toBe(
      "BPM must be at most 220",
    );
  });

  it("clears value when clear button clicked", () => {
    const onChange = vi.fn();
    render(<HeartbeatInput value={72} onChange={onChange} />);
    const clearBtn = screen.getByTestId("heartbeat-clear");
    fireEvent.click(clearBtn);
    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("switches to tap mode", () => {
    render(<HeartbeatInput value={null} onChange={() => {}} />);
    const tapTab = screen.getByText("Tap to Measure");
    fireEvent.click(tapTab);
    expect(screen.getByTestId("heartbeat-tap-button")).toBeDefined();
    expect(screen.getByTestId("tap-message").textContent).toBe(
      "Tap at least 5 times",
    );
  });
});
