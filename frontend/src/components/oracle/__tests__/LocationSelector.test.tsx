import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LocationSelector } from "../LocationSelector";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "oracle.location_label": "Location",
        "oracle.location_auto_detect": "Auto-Detect Location",
        "oracle.location_detecting": "Detecting...",
        "oracle.location_detect_error":
          "Could not detect location. Please select manually.",
        "oracle.location_country": "Country",
        "oracle.location_city": "City",
        "oracle.location_coordinates": "Coordinates",
      };
      return map[key] ?? key;
    },
  }),
}));

// Mock geolocation
const mockGeolocation = {
  getCurrentPosition: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  Object.defineProperty(navigator, "geolocation", {
    value: mockGeolocation,
    writable: true,
    configurable: true,
  });
});

describe("LocationSelector", () => {
  it("renders auto-detect button", () => {
    render(<LocationSelector value={null} onChange={vi.fn()} />);
    expect(screen.getByText("Auto-Detect Location")).toBeInTheDocument();
  });

  it("detects location successfully via geolocation", async () => {
    const onChange = vi.fn();
    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success({ coords: { latitude: 35.6892, longitude: 51.389 } });
    });

    render(<LocationSelector value={null} onChange={onChange} />);
    await userEvent.click(screen.getByText("Auto-Detect Location"));

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ lat: 35.6892, lon: 51.389 }),
      );
    });
  });

  it("shows error when geolocation fails", async () => {
    mockGeolocation.getCurrentPosition.mockImplementation((_s, error) => {
      error(new Error("denied"));
    });

    render(<LocationSelector value={null} onChange={vi.fn()} />);
    await userEvent.click(screen.getByText("Auto-Detect Location"));

    await waitFor(() => {
      expect(
        screen.getByText("Could not detect location. Please select manually."),
      ).toBeInTheDocument();
    });
  });

  it("selects a country from dropdown", async () => {
    const onChange = vi.fn();
    render(<LocationSelector value={null} onChange={onChange} />);
    const countrySelect = screen.getByLabelText("Country");
    await userEvent.selectOptions(countrySelect, "Iran");
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        lat: 35.6892,
        lon: 51.389,
        country: "Iran",
        city: "Tehran",
      }),
    );
  });

  it("displays coordinates when value is set", () => {
    render(
      <LocationSelector
        value={{ lat: 35.6892, lon: 51.389, country: "Iran", city: "Tehran" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/35.6892, 51.389/)).toBeInTheDocument();
  });
});
