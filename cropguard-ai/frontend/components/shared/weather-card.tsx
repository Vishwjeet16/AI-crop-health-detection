import { Cloud, CloudRain, Droplets, Thermometer, Wind } from "lucide-react";
import type { Weather } from "@/types";

export function WeatherCard({ weather }: { weather: Weather }) {
  return (
    <div className="card p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-display text-lg text-forest-dark">Field Weather</h3>
        <span className="flex items-center gap-1.5 text-sm text-ink-soft">
          <Cloud className="h-4 w-4" /> {weather.condition}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat icon={Thermometer} label="Temp" value={`${weather.temperatureC}°C`} />
        <Stat icon={Droplets} label="Humidity" value={`${weather.humidityPercent}%`} />
        <Stat icon={CloudRain} label="Rain chance" value={`${weather.rainProbabilityPercent}%`} />
        <Stat icon={Wind} label="Wind" value={`${weather.windKph} km/h`} />
      </div>
      <div className="mt-4 rounded-md bg-bg-alt px-4 py-3 text-sm text-ink-soft">
        <span className="font-semibold text-ink">Disease risk factors: </span>
        {weather.diseaseRiskNote}
      </div>
    </div>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Thermometer;
  label: string;
  value: string;
}) {
  return (
    <div>
      <div className="flex items-center gap-1.5 text-xs text-ink-soft">
        <Icon className="h-3.5 w-3.5" /> {label}
      </div>
      <div className="font-mono text-lg font-semibold text-ink">{value}</div>
    </div>
  );
}
