import {
  AddSourceResponseSchema,
  CycleListSchema,
  CycleReportSchema,
  SearchResultListSchema,
  SearchStatusSchema,
  SourceDocListSchema,
  UploadFormatsSchema,
  UploadSourceResponseSchema,
  type CycleReport,
  type SearchResult,
  type SearchStatus,
  type SourceDoc,
  type SourceType,
} from "@/lib/schemas";

export { SOURCE_TYPE_LABEL } from "@/lib/schemas";
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
  SourceType,
  SourceDoc,
  SearchResult,
  SearchStatus,
} from "@/lib/schemas";

const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8012";

export async function addSource(
  cycleId: string,
  title: string,
  text: string,
  sourceType: SourceType = "manual",
): Promise<{ id: string }> {
  const res = await fetch(`${BASE}/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cycle_id: cycleId, title, text, source_type: sourceType }),
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

export async function getSources(cycleId: string): Promise<SourceDoc[]> {
  const res = await fetch(`${BASE}/sources/${encodeURIComponent(cycleId)}`);
  if (!res.ok) throw new Error(`수집 자료 조회 실패: ${res.status}`);
  return SourceDocListSchema.parse(await res.json());
}

export async function getUploadFormats(): Promise<string[]> {
  const res = await fetch(`${BASE}/upload-formats`);
  if (!res.ok) throw new Error(`업로드 형식 조회 실패: ${res.status}`);
  return UploadFormatsSchema.parse(await res.json());
}

export async function uploadSourceFile(
  cycleId: string,
  file: File,
  sourceType: SourceType = "upload",
  title?: string,
): Promise<{ id: string; extracted_chars: number }> {
  const form = new FormData();
  form.append("cycle_id", cycleId);
  form.append("source_type", sourceType);
  if (title) form.append("title", title);
  form.append("file", file);

  const res = await fetch(`${BASE}/sources/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail || `문서 업로드 실패: ${res.status}`);
  }
  return UploadSourceResponseSchema.parse(await res.json());
}

export async function search(query: string, cycleId?: string, limit = 10): Promise<SearchResult[]> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  if (cycleId) params.set("cycle_id", cycleId);
  const res = await fetch(`${BASE}/search?${params.toString()}`);
  if (!res.ok) throw new Error(`검색 실패: ${res.status}`);
  return SearchResultListSchema.parse(await res.json());
}

export async function getSearchStatus(): Promise<SearchStatus> {
  const res = await fetch(`${BASE}/search-status`);
  if (!res.ok) throw new Error(`검색 상태 조회 실패: ${res.status}`);
  return SearchStatusSchema.parse(await res.json());
}
