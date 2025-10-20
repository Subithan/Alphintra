import { getToken } from "@/lib/auth";
import { buildGatewayUrl } from "@/lib/config/gateway";

export interface MyStrategySummary {
  workflow_id: number;
  workflow_uuid: string;
  name: string;
  compilation_status: string | null;
  requirements: string[];
  code_metrics: { lines: number; size_bytes: number };
  compiler_version: string;
  updated_at: string | null;
  storage: string;
}

interface StrategyListResponse {
  success: boolean;
  strategies: MyStrategySummary[];
  total_count: number;
  storage_info: unknown;
}

export async function fetchMyStrategies(): Promise<MyStrategySummary[]> {
  const token = getToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    buildGatewayUrl("/api/workflows/strategies/list"),
    {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = body?.detail ?? `Failed to load strategies (${response.status})`;
    throw new Error(message);
  }

  const data = (await response.json()) as StrategyListResponse;
  return data.strategies ?? [];
}
