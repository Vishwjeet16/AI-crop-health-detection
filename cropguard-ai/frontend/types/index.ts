import type { LanguageCode } from "@/lib/i18n";

export type RiskLevel = "healthy" | "moderate" | "high";
export type SeverityLevel = "low" | "moderate" | "high" | "critical";
export type TrendType = "stable" | "improving" | "slowly_spreading" | "rapidly_spreading";

export interface User {
  id: string;
  name: string;
  contact: string;
  location: string;
  // Derived from the i18n registry so adding a language doesn't mean editing
  // this union, lib/api/auth.ts, and three pickers by hand.
  language: LanguageCode;
}


export interface Field {
  id: string;
  name: string;
  crop: string;
  areaAcres: number;
  latitude: number;
  longitude: number;
  healthStatus: RiskLevel;
  lastScanAt: string | null;
  lastDisease: string | null;
  lastRisk: RiskLevel | null;
}

export interface Detection {
  class: string;
  label: string;
  confidence: number; // 0-1
  bbox: [number, number, number, number];
}

export interface Severity {
  level: SeverityLevel;
  affectedAreaPercent: number;
  isDemo: boolean;
}

export interface Risk {
  level: RiskLevel;
  score: number; // 0-100
  factors: string[];
}

export interface Recommendation {
  title: string;
  actions: string[];
  prevention: string[];
  nextScan: string;
}

export interface Weather {
  temperatureC: number;
  humidityPercent: number;
  rainProbabilityPercent: number;
  windKph: number;
  condition: string;
  diseaseRiskNote: string;
}

export interface Scan {
  id: string;
  fieldId: string;
  imageUrl: string;
  timestamp: string;
  crop: string;
  isDemo: boolean;
  detections: Detection[];
  severity: Severity;
  risk: Risk;
  weather: Weather;
  recommendation: Recommendation;
}

export interface Alert {
  id: string;
  fieldId: string;
  fieldName: string;
  message: string;
  severity: RiskLevel;
  createdAt: string;
  read: boolean;
}

export interface HistoryPoint {
  date: string;
  affectedAreaPercent: number;
  severity: SeverityLevel;
  risk: RiskLevel;
}
