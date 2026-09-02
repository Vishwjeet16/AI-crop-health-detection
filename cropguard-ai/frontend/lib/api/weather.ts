import { apiFetch, mockDelay, USE_MOCK_API } from "./client";
import { mockScan } from "@/lib/mock-data";
import type { Weather } from "@/types";

function fromApiWeather(row: any): Weather {
  return {
    temperatureC: row.temperature_c,
    humidityPercent: row.humidity_percent,
    rainProbabilityPercent: row.rain_probability_percent,
    windKph: row.wind_kph,
    condition: row.condition,
    diseaseRiskNote: row.disease_risk_note,
  };
}

export async function getWeatherByCoordinates(latitude: number, longitude: number): Promise<Weather> {
  if (!USE_MOCK_API) {
    const params = new URLSearchParams({
      latitude: String(latitude),
      longitude: String(longitude),
    });
    return fromApiWeather(await apiFetch<any>(`/api/weather/current?${params}`));
  }

  await mockDelay(300);
  return mockScan.weather;
}
