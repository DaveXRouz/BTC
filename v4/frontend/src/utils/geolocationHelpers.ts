import type { LocationData } from "@/types";

/** Request browser geolocation with timeout */
export function getCurrentPosition(
  timeout = 10000,
): Promise<{ lat: number; lon: number }> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation not supported"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          lat: Math.round(pos.coords.latitude * 10000) / 10000,
          lon: Math.round(pos.coords.longitude * 10000) / 10000,
        }),
      (err) => reject(err),
      { timeout, enableHighAccuracy: false },
    );
  });
}

/** Country list with default coordinates for manual selection */
export const COUNTRIES: Record<string, LocationData> = {
  Iran: { lat: 35.6892, lon: 51.389, country: "Iran", city: "Tehran" },
  "United States": {
    lat: 40.7128,
    lon: -74.006,
    country: "United States",
    city: "New York",
  },
  "United Kingdom": {
    lat: 51.5074,
    lon: -0.1278,
    country: "United Kingdom",
    city: "London",
  },
  Germany: { lat: 52.52, lon: 13.405, country: "Germany", city: "Berlin" },
  France: { lat: 48.8566, lon: 2.3522, country: "France", city: "Paris" },
  Turkey: { lat: 41.0082, lon: 28.9784, country: "Turkey", city: "Istanbul" },
  UAE: { lat: 25.2048, lon: 55.2708, country: "UAE", city: "Dubai" },
  Canada: { lat: 43.6532, lon: -79.3832, country: "Canada", city: "Toronto" },
  Australia: {
    lat: -33.8688,
    lon: 151.2093,
    country: "Australia",
    city: "Sydney",
  },
  India: { lat: 28.6139, lon: 77.209, country: "India", city: "New Delhi" },
};
