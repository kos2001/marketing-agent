import {
  AddSourceResponseSchema,
  CycleListSchema,
  CycleReportSchema,
  type CycleReport,
} from "@/lib/schemas";

export type {
  Citation,
  DiagnosisItem,
  OpportunityRiskItem,
  CriticalPoint,
  TimelineLink,
  ActionItem,
  ActionItemsReport,
  CustomerStrategy,
  ProcessStep,
  MetricSnapshot,
  DiagnosisSummary,
  StrategicAxis,
  IssueStrategyGuide,
  RecommendedTimelineStep,
  StrategyTimeline,
  CycleReport,
} from "@/lib/schemas";

const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8012";

export async function addSource(cycleId: string, title: string, text: string): Promise<{ id: string }> {
  const res = await fetch(`${BASE}/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cycle_id: cycleId, title, text }),
  });
  if (!res.ok) throw new Error(`업로드 실패: ${res.status}`);
  return AddSourceResponseSchema.parse(await res.json());
}

export async function runPipeline(cycleId: string): Promise<CycleReport> {
  const res = await fetch(`${BASE}/pipeline/run?cycle_id=${encodeURIComponent(cycleId)}`, { method: "POST" });
  if (!res.ok) throw new Error(`파이프라인 실행 실패: ${res.status}`);
  return CycleReportSchema.parse(await res.json());
}

export async function getReport(cycleId: string): Promise<CycleReport | null> {
  const res = await fetch(`${BASE}/reports/${encodeURIComponent(cycleId)}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`리포트 조회 실패: ${res.status}`);
  return CycleReportSchema.parse(await res.json());
}

export async function listCycles(): Promise<string[]> {
  const res = await fetch(`${BASE}/cycles`);
  if (!res.ok) throw new Error(`회차 목록 조회 실패: ${res.status}`);
  return CycleListSchema.parse(await res.json());
}
