// DEMO DATA — all values here are illustrative mock data for the Stage 1
// UI/UX prototype. Nothing in this file represents real model output,
// verified agricultural guidance, or real farm records. Shapes match the
// API contracts in the backend so this file can be deleted once /api/*
// routes are live (Stage 2+).

import type { Alert, Field, HistoryPoint, Scan } from "@/types";

export const currentUser = {
  name: "Ramesh Patil",
  location: "Nashik, Maharashtra",
  language: "en" as const,
};

export const mockFields: Field[] = [
  {
    id: "field-a",
    name: "Field A",
    crop: "Tomato",
    areaAcres: 2.1,
    latitude: 19.9975,
    longitude: 73.7898,
    healthStatus: "high",
    lastScanAt: "2026-08-24T07:12:00Z",
    lastDisease: "Early Blight",
    lastRisk: "high",
  },
  {
    id: "field-b",
    name: "Field B",
    crop: "Cotton",
    areaAcres: 3.4,
    latitude: 20.005,
    longitude: 73.775,
    healthStatus: "moderate",
    lastScanAt: "2026-08-23T05:40:00Z",
    lastDisease: "Leaf Curl (suspected)",
    lastRisk: "moderate",
  },
  {
    id: "field-c",
    name: "Field C",
    crop: "Soybean",
    areaAcres: 1.6,
    latitude: 19.99,
    longitude: 73.80,
    healthStatus: "healthy",
    lastScanAt: "2026-08-20T06:05:00Z",
    lastDisease: null,
    lastRisk: "healthy",
  },
];

export const mockScan: Scan = {
  id: "scan-001",
  fieldId: "field-a",
  imageUrl: "/demo/tomato-leaf.svg",
  timestamp: "2026-08-24T07:12:00Z",
  crop: "Tomato",
  isDemo: true,
  detections: [
    {
      class: "early_blight",
      label: "Early Blight",
      confidence: 0.94,
      bbox: [28, 22, 42, 48], // x%, y%, width%, height% of image frame
    },
  ],
  severity: {
    level: "moderate",
    affectedAreaPercent: 23,
    isDemo: true,
  },
  risk: {
    level: "high",
    score: 78,
    factors: [
      "Current disease detection",
      "Recent humidity",
      "Temperature",
      "Previous field observations",
    ],
  },
  weather: {
    temperatureC: 31,
    humidityPercent: 78,
    rainProbabilityPercent: 40,
    windKph: 12,
    condition: "Partly cloudy",
    diseaseRiskNote:
      "High humidity may increase the risk of certain fungal diseases. This is a general environmental signal, not proof of infection.",
  },
  recommendation: {
    title: "Inspect affected plants",
    actions: [
      "Inspect nearby plants and remove severely affected plant material where appropriate.",
      "Continue monitoring the field over the next few days.",
    ],
    prevention: [
      "Maintain field hygiene.",
      "Monitor nearby plants.",
      "Avoid unnecessary irrigation.",
      "Follow local agricultural guidance.",
    ],
    nextScan: "Recommended monitoring: rescan according to crop-specific guidance.",
  },
};

export const mockHistory: HistoryPoint[] = [
  { date: "Day 1", affectedAreaPercent: 5, severity: "low", risk: "moderate" },
  { date: "Day 4", affectedAreaPercent: 9, severity: "low", risk: "moderate" },
  { date: "Day 7", affectedAreaPercent: 17, severity: "moderate", risk: "high" },
  { date: "Day 10", affectedAreaPercent: 31, severity: "high", risk: "high" },
];

export const mockAlerts: Alert[] = [
  {
    id: "alert-1",
    fieldId: "field-a",
    fieldName: "Field A",
    message: "High disease risk detected in Field A.",
    severity: "high",
    createdAt: "2026-08-24T07:15:00Z",
    read: false,
  },
  {
    id: "alert-2",
    fieldId: "field-a",
    fieldName: "Field A",
    message: "Disease severity has increased since the previous scan.",
    severity: "moderate",
    createdAt: "2026-08-21T06:00:00Z",
    read: false,
  },
  {
    id: "alert-3",
    fieldId: "field-c",
    fieldName: "Field C",
    message: "No significant issue detected in the latest scan.",
    severity: "healthy",
    createdAt: "2026-08-20T06:10:00Z",
    read: true,
  },
];

export const dashboardStats = {
  totalFields: mockFields.length,
  healthyFields: mockFields.filter((f) => f.healthStatus === "healthy").length,
  atRiskFields: mockFields.filter((f) => f.healthStatus !== "healthy").length,
  activeAlerts: mockAlerts.filter((a) => !a.read).length,
};
