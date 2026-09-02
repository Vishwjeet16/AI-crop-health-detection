import { apiFetch, ApiError, mockDelay, USE_MOCK_API } from "./client";
import { mockFields } from "@/lib/mock-data";
import type { Field } from "@/types";

// In-memory store so additions persist for the session (mock only —
// resets on page reload; Stage 3 replaces this with Supabase).
let fieldsStore: Field[] = [...mockFields];

// Backend rows are snake_case (see backend/app/schemas/fields.py); the
// frontend's Field type is camelCase. This is the one place that translates
// between them so every page/component can stay on the camelCase shape
// regardless of which mode (mock or real) is active.
function fromApiRow(row: any): Field {
  return {
    id: row.id,
    name: row.name,
    crop: row.crop,
    areaAcres: row.area_acres,
    latitude: row.latitude,
    longitude: row.longitude,
    healthStatus: row.health_status,
    lastScanAt: row.last_scan_at ?? null,
    lastDisease: row.last_disease ?? null,
    lastRisk: row.last_risk ?? null,
  };
}

export async function listFields(): Promise<Field[]> {
  if (!USE_MOCK_API) {
    const rows = await apiFetch<any[]>("/api/fields");
    return rows.map(fromApiRow);
  }
  await mockDelay(500);
  return fieldsStore;
}

export async function getField(id: string): Promise<Field> {
  if (!USE_MOCK_API) {
    const row = await apiFetch<any>(`/api/fields/${id}`);
    return fromApiRow(row);
  }
  await mockDelay(400);
  const field = fieldsStore.find((f) => f.id === id);
  if (!field) throw new ApiError("Field not found.", 404);
  return field;
}

export interface CreateFieldPayload {
  name: string;
  crop: string;
  areaAcres: number;
  latitude: number;
  longitude: number;
}

export async function createField(payload: CreateFieldPayload): Promise<Field> {
  if (!USE_MOCK_API) {
    const row = await apiFetch<any>("/api/fields", {
      method: "POST",
      body: JSON.stringify({
        name: payload.name,
        crop: payload.crop,
        area_acres: payload.areaAcres,
        latitude: payload.latitude,
        longitude: payload.longitude,
      }),
    });
    return fromApiRow(row);
  }
  await mockDelay(700);
  if (!payload.name.trim()) throw new ApiError("Field name is required.", 400);
  const newField: Field = {
    id: `field-${Date.now()}`,
    name: payload.name,
    crop: payload.crop,
    areaAcres: payload.areaAcres,
    latitude: payload.latitude,
    longitude: payload.longitude,
    healthStatus: "healthy",
    lastScanAt: null,
    lastDisease: null,
    lastRisk: null,
  };
  fieldsStore = [newField, ...fieldsStore];
  return newField;
}
