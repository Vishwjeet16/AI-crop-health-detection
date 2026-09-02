import { apiFetch, mockDelay, USE_MOCK_API } from "./client";
import { mockAlerts } from "@/lib/mock-data";
import type { Alert } from "@/types";

let alertsStore: Alert[] = [...mockAlerts];

function fromApiRow(row: any): Alert {
  return {
    id: row.id,
    fieldId: row.field_id,
    fieldName: row.field_name,
    message: row.message,
    severity: row.severity,
    createdAt: row.created_at,
    read: row.read,
  };
}

export async function listAlerts(): Promise<Alert[]> {
  if (!USE_MOCK_API) {
    const rows = await apiFetch<any[]>("/api/alerts");
    return rows.map(fromApiRow);
  }
  await mockDelay(450);
  return alertsStore;
}

export async function markAlertRead(id: string): Promise<Alert> {
  if (!USE_MOCK_API) {
    return fromApiRow(await apiFetch<any>(`/api/alerts/${id}/read`, { method: "PATCH" }));
  }
  await mockDelay(300);
  alertsStore = alertsStore.map((a) => (a.id === id ? { ...a, read: true } : a));
  return alertsStore.find((a) => a.id === id)!;
}
