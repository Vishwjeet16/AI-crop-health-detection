import { API_BASE_URL, ApiError, apiFetch, authHeaders, mockDelay, USE_MOCK_API } from "./client";
import { mockHistory, mockScan } from "@/lib/mock-data";
import { getField } from "./fields";
import type { HistoryPoint, Scan, SeverityLevel } from "@/types";

// In-memory store so a saved scan can be looked up again by id within the
// session. Stage 3 replaces this with GET /api/scans/{id} against Postgres.
const scansStore = new Map<string, Scan>([[mockScan.id, mockScan]]);

// --- Demo AI Mode outcome registry (mock-API mirror of the backend's
// app/services/demo_outcomes.py) ---------------------------------------
//
// Keyed by crop (lowercase) so a newly-added field gets a demo result that
// actually matches its crop, not whichever field happened to be selected.
// Spans the full severity range and includes one deliberately
// low-confidence entry so every UI path (severity badges, the "AI is not
// confident enough" message, risk gauge) gets exercised during a demo.

const BASE_RECOMMENDATION = {
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
};

const HEALTHY_RECOMMENDATION = {
  title: "No action needed",
  actions: ["Continue routine monitoring."],
  prevention: ["Maintain field hygiene.", "Keep scanning regularly."],
  nextScan: BASE_RECOMMENDATION.nextScan,
};

const LOW_CONFIDENCE_RECOMMENDATION = {
  title: "Re-scan recommended",
  actions: [
    "The AI is not confident enough to identify an issue from this image.",
    "Capture a clearer, well-lit photo focused on the affected area, or consult an agricultural expert.",
  ],
  prevention: ["Maintain field hygiene.", "Keep scanning regularly."],
  nextScan: BASE_RECOMMENDATION.nextScan,
};

function riskFor(level: SeverityLevel, confidence: number | null): Scan["risk"] {
  // Mirrors the shape (not the exact math) of the backend's rule-based
  // risk_service.py so mock mode tells a consistent story.
  const factors = ["Recent humidity", "Temperature"];
  if (confidence !== null) factors.unshift("Current disease detection");
  if (level === "critical") return { level: "high", score: 88, factors: [...factors, "Previous field observations"] };
  if (level === "high") return { level: "high", score: 72, factors };
  if (level === "moderate") return { level: "moderate", score: 45, factors };
  return confidence !== null && confidence < 0.6
    ? { level: "moderate", score: 38, factors: ["Low-confidence detection", "Recent humidity"] }
    : { level: "healthy", score: 8, factors: ["No disease detected", "Stable weather conditions"] };
}

function buildOutcome(
  idSuffix: string,
  fieldId: string,
  crop: string,
  detection: Scan["detections"][number] | null,
  severity: SeverityLevel,
  affectedAreaPercent: number
): Scan {
  const recommendation =
    detection === null
      ? HEALTHY_RECOMMENDATION
      : detection.confidence < 0.6
      ? LOW_CONFIDENCE_RECOMMENDATION
      : { title: "Inspect affected plants", ...BASE_RECOMMENDATION };

  return {
    ...mockScan,
    id: `scan-${idSuffix}`,
    fieldId,
    crop,
    detections: detection ? [detection] : [],
    severity: { level: severity, affectedAreaPercent, isDemo: true },
    risk: riskFor(severity, detection?.confidence ?? null),
    recommendation,
  };
}

const DEMO_POOL: Record<string, Scan[]> = {
  tomato: [
    buildOutcome(
      "tomato-1",
      "field-a",
      "Tomato",
      { class: "early_blight", label: "Early Blight", confidence: 0.94, bbox: [28, 22, 42, 48] },
      "moderate",
      23
    ),
    buildOutcome(
      "tomato-2",
      "field-a",
      "Tomato",
      { class: "late_blight", label: "Late Blight", confidence: 0.89, bbox: [15, 10, 65, 70] },
      "critical",
      58
    ),
    buildOutcome("tomato-3", "field-a", "Tomato", null, "low", 0),
  ],
  cotton: [
    buildOutcome(
      "cotton-1",
      "field-b",
      "Cotton",
      { class: "leaf_curl", label: "Leaf Curl (uncertain)", confidence: 0.42, bbox: [30, 25, 35, 40] },
      "low",
      6
    ),
    buildOutcome(
      "cotton-2",
      "field-b",
      "Cotton",
      { class: "bollworm_damage", label: "Bollworm Damage", confidence: 0.81, bbox: [20, 30, 50, 45] },
      "high",
      34
    ),
    buildOutcome("cotton-3", "field-b", "Cotton", null, "low", 0),
  ],
  soybean: [
    buildOutcome(
      "soybean-1",
      "field-c",
      "Soybean",
      { class: "soybean_rust", label: "Soybean Rust", confidence: 0.77, bbox: [25, 20, 40, 35] },
      "moderate",
      15
    ),
    buildOutcome("soybean-2", "field-c", "Soybean", null, "low", 0),
  ],
  wheat: [
    buildOutcome(
      "wheat-1",
      "field-wheat",
      "Wheat",
      { class: "wheat_rust", label: "Wheat Rust", confidence: 0.88, bbox: [20, 15, 55, 50] },
      "moderate",
      27
    ),
    buildOutcome("wheat-2", "field-wheat", "Wheat", null, "low", 0),
  ],
  rice: [
    buildOutcome(
      "rice-1",
      "field-rice",
      "Rice",
      { class: "rice_blast", label: "Rice Blast", confidence: 0.91, bbox: [18, 12, 60, 55] },
      "high",
      44
    ),
    buildOutcome("rice-2", "field-rice", "Rice", null, "low", 0),
  ],
};

for (const pool of Object.values(DEMO_POOL)) {
  for (const s of pool) scansStore.set(s.id, s);
}

function pickDemoOutcome(crop: string, fieldId: string, imageSizeHint: number): Scan {
  const pool = DEMO_POOL[crop.trim().toLowerCase()] ?? DEMO_POOL.tomato;
  // Deterministic-but-varied, same spirit as the backend: a stable pick per
  // photo (by file size, the cheapest signal available client-side) so a
  // repeated demo run looks consistent rather than random each time.
  const index = imageSizeHint % pool.length;
  return { ...pool[index], fieldId };
}

// Backend ScanOut is snake_case; translate to the frontend's camelCase Scan.
function fromApiScan(row: any): Scan {
  return {
    id: row.id,
    fieldId: row.field_id,
    imageUrl: row.image_url,
    timestamp: row.timestamp,
    crop: row.crop,
    isDemo: row.is_demo,
    detections: row.detections.map((d: any) => ({
      class: d.class,
      label: d.label,
      confidence: d.confidence,
      bbox: d.bbox,
    })),
    severity: {
      level: row.severity.level,
      affectedAreaPercent: row.severity.affected_area_percent,
      isDemo: row.severity.is_demo,
    },
    risk: { level: row.risk.level, score: row.risk.score, factors: row.risk.factors },
    weather: row.weather
      ? {
          temperatureC: row.weather.temperature_c,
          humidityPercent: row.weather.humidity_percent,
          rainProbabilityPercent: row.weather.rain_probability_percent,
          windKph: row.weather.wind_kph,
          condition: row.weather.condition,
          diseaseRiskNote: row.weather.disease_risk_note,
        }
      : mockScan.weather,
    recommendation: {
      title: row.recommendation.title,
      actions: row.recommendation.actions,
      prevention: row.recommendation.prevention,
      nextScan: row.recommendation.next_scan,
    },
  };
}

export async function analyzeImage(fieldId: string, file: File): Promise<Scan> {
  if (!USE_MOCK_API) {
    // Multipart upload — bypasses apiFetch's JSON content-type so the
    // browser can set the correct multipart boundary itself.
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE_URL}/api/analyze?field_id=${encodeURIComponent(fieldId)}`, {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new ApiError(body.error ?? body.detail ?? `Analysis failed (${res.status})`, res.status);
    }
    return fromApiScan(await res.json());
  }

  await mockDelay(300); // the visible step-by-step LoadingState carries the rest of the perceived latency
  const field = await getField(fieldId).catch(() => null);
  const crop = field?.crop ?? "Tomato";
  const outcome = pickDemoOutcome(crop, fieldId, file.size || 1);
  scansStore.set(outcome.id, outcome);
  return outcome;
}

export async function getScan(id: string): Promise<Scan> {
  if (!USE_MOCK_API) {
    return fromApiScan(await apiFetch<any>(`/api/scans/${id}`));
  }
  await mockDelay(400);
  const scan = scansStore.get(id);
  if (!scan) throw new ApiError("Scan not found.", 404);
  return scan;
}

export async function saveScan(scan: Scan): Promise<{ saved: true }> {
  // In real mode the scan is already persisted server-side by /api/analyze,
  // so this becomes a no-op kept only so the frontend's "Save to History"
  // button still has something to call without an if-branch at the call site.
  if (!USE_MOCK_API) {
    await mockDelay(150);
    return { saved: true };
  }
  await mockDelay(500);
  scansStore.set(scan.id, scan);
  return { saved: true };
}

export async function getFieldHistory(fieldId: string): Promise<HistoryPoint[]> {
  if (!USE_MOCK_API) {
    const rows = await apiFetch<any[]>(`/api/fields/${fieldId}/history`);
    return rows.map((r) => ({
      date: r.date,
      affectedAreaPercent: r.affected_area_percent,
      severity: r.severity,
      risk: r.risk,
    }));
  }
  await mockDelay(400);
  return mockHistory;
}
