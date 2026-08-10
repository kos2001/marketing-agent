const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

export interface Citation {
  quote: string;
  source_id: string;
}

export interface DiagnosisItem {
  id: string;
  channel: string;
  summary: string;
  kind: "strength" | "weakness";
  citations: Citation[];
  status: "confirmed" | "needs_review" | "unfounded";
}

export interface OpportunityRiskItem {
  id: string;
  kind: "opportunity" | "risk";
  title: string;
  rationale: string;
  citations: Citation[];
  additionally_flagged: boolean;
}

export interface CriticalPoint {
  id: string;
  title: string;
  impact: string;
  urgency: string;
  decision_needed: string;
  citations: Citation[];
}

export interface TimelineLink {
  item_title: string;
  prior_cycle_id: string;
  same_issue: boolean;
  rebuttal_passed: boolean;
  repeat_count: number;
}

export interface ActionItem {
  id: string;
  title: string;
  owner: string;
  due: string;
  priority: "high" | "mid" | "low";
  source_item_ids: string[];
}

export interface CycleReport {
  cycle_id: string;
  diagnosis: DiagnosisItem[];
  opportunities_risks: OpportunityRiskItem[];
  critical_points: CriticalPoint[];
  timeline: TimelineLink[];
  action_items: ActionItem[];
  overview: string;
  overview_warnings: string[];
  coverage_note: string;
}

export async function addSource(cycleId: string, title: string, text: string): Promise<{ id: string }> {
  const res = await fetch(`${BASE}/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cycle_id: cycleId, title, text }),
  });
  if (!res.ok) throw new Error(`업로드 실패: ${res.status}`);
  return res.json();
}

export async function runPipeline(cycleId: string): Promise<CycleReport> {
  const res = await fetch(`${BASE}/pipeline/run?cycle_id=${encodeURIComponent(cycleId)}`, { method: "POST" });
  if (!res.ok) throw new Error(`파이프라인 실행 실패: ${res.status}`);
  return res.json();
}

export async function getReport(cycleId: string): Promise<CycleReport | null> {
  const res = await fetch(`${BASE}/reports/${encodeURIComponent(cycleId)}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`리포트 조회 실패: ${res.status}`);
  return res.json();
}

export async function listCycles(): Promise<string[]> {
  const res = await fetch(`${BASE}/cycles`);
  if (!res.ok) throw new Error(`회차 목록 조회 실패: ${res.status}`);
  return res.json();
}
