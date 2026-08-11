const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8012";

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
  impact: "high" | "mid" | "low";
  effort: "high" | "mid" | "low";
  source_item_ids: string[];
}

export interface ActionItemsReport {
  immediate_check: ActionItem[];
  action_needed: ActionItem[];
  final_summary: string;
}

export interface CustomerStrategy {
  id: string;
  customer: string;
  situation: string;
  strategy: string;
  citations: Citation[];
}

export interface ProcessStep {
  order: number;
  title: string;
  description: string;
  owner: string;
}

export interface MetricSnapshot {
  metric: string;
  current: string;
  prior: string;
  change: string;
  target: string;
  status: "on_track" | "at_risk" | "off_track";
}

export interface DiagnosisSummary {
  executive_summary: string;
  metrics: MetricSnapshot[];
  customer_strategies: CustomerStrategy[];
  corporate_response_process: ProcessStep[];
}

export interface StrategicAxis {
  id: string;
  title: string;
  description: string;
  citations: Citation[];
}

export interface IssueStrategyGuide {
  id: string;
  issue_title: string;
  guide: string;
  source_item_ids: string[];
  citations: Citation[];
}

export interface RecommendedTimelineStep {
  order: number;
  when: string;
  action: string;
  owner: string;
}

export interface StrategyTimeline {
  issue_guides: IssueStrategyGuide[];
  strategic_axes: StrategicAxis[];
  recommended_timeline: RecommendedTimelineStep[];
}

export interface CycleReport {
  cycle_id: string;
  diagnosis: DiagnosisItem[];
  opportunities_risks: OpportunityRiskItem[];
  critical_points: CriticalPoint[];
  diagnosis_summary: DiagnosisSummary;
  timeline: TimelineLink[];
  strategy_timeline: StrategyTimeline;
  action_items: ActionItemsReport;
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
