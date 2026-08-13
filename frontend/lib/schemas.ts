import { z } from "zod";

/**
 * backend/app/schemas.py와 1:1로 대응하는 zod 스키마. API 응답을 파싱 시점에
 * 검증해, 백엔드 스키마가 바뀌었는데 프론트가 조용히 깨지는 것(런타임에야 발견되는
 * undefined 접근)을 막는다 — 이 세션에서만 CycleReport 모양이 세 번 바뀌었다.
 */

export const SourceTypeSchema = z.enum([
  "email", "social", "crm", "analytics", "customer_feedback", "news", "upload", "manual",
]);

export const SOURCE_TYPE_LABEL: Record<z.infer<typeof SourceTypeSchema>, string> = {
  email: "이메일 캠페인",
  social: "소셜미디어",
  crm: "CRM/영업 파이프라인",
  analytics: "웹/앱 애널리틱스",
  customer_feedback: "고객 피드백/VoC",
  news: "뉴스/경쟁사 동향",
  upload: "업로드 문서",
  manual: "직접 입력",
};

export const CitationSchema = z.object({
  quote: z.string(),
  source_id: z.string(),
});

export const DiagnosisItemSchema = z.object({
  id: z.string(),
  channel: z.string(),
  summary: z.string(),
  kind: z.enum(["strength", "weakness"]),
  citations: z.array(CitationSchema),
  status: z.enum(["confirmed", "needs_review", "unfounded"]),
});

export const OpportunityRiskItemSchema = z.object({
  id: z.string(),
  kind: z.enum(["opportunity", "risk"]),
  title: z.string(),
  rationale: z.string(),
  citations: z.array(CitationSchema),
  additionally_flagged: z.boolean(),
});

export const CriticalPointSchema = z.object({
  id: z.string(),
  title: z.string(),
  impact: z.string(),
  urgency: z.string(),
  decision_needed: z.string(),
  citations: z.array(CitationSchema),
});

export const TimelineLinkSchema = z.object({
  item_title: z.string(),
  prior_cycle_id: z.string(),
  same_issue: z.boolean(),
  rebuttal_passed: z.boolean(),
  repeat_count: z.number(),
});

const LevelSchema = z.enum(["high", "mid", "low"]);

export const ActionItemSchema = z.object({
  id: z.string(),
  title: z.string(),
  owner: z.string(),
  due: z.string(),
  priority: LevelSchema,
  impact: LevelSchema,
  effort: LevelSchema,
  source_item_ids: z.array(z.string()),
});

export const ActionItemsReportSchema = z.object({
  immediate_check: z.array(ActionItemSchema),
  action_needed: z.array(ActionItemSchema),
  final_summary: z.string(),
});

export const CustomerStrategySchema = z.object({
  id: z.string(),
  customer: z.string(),
  situation: z.string(),
  strategy: z.string(),
  risk_level: z.enum(["stable", "at_risk", "critical"]),
  citations: z.array(CitationSchema),
});

export const ProcessStepSchema = z.object({
  order: z.number(),
  title: z.string(),
  description: z.string(),
  owner: z.string(),
});

export const MetricSnapshotSchema = z.object({
  metric: z.string(),
  current: z.string(),
  prior: z.string(),
  change: z.string(),
  target: z.string(),
  status: z.enum(["on_track", "at_risk", "off_track"]),
});

export const DiagnosisSummarySchema = z.object({
  executive_summary: z.string(),
  metrics: z.array(MetricSnapshotSchema),
  customer_strategies: z.array(CustomerStrategySchema),
  corporate_response_process: z.array(ProcessStepSchema),
});

export const StrategicAxisSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  citations: z.array(CitationSchema),
});

export const IssueStrategyGuideSchema = z.object({
  id: z.string(),
  issue_title: z.string(),
  guide: z.string(),
  source_item_ids: z.array(z.string()),
  citations: z.array(CitationSchema),
});

export const RecommendedTimelineStepSchema = z.object({
  order: z.number(),
  when: z.string(),
  action: z.string(),
  owner: z.string(),
});

export const StrategyTimelineSchema = z.object({
  issue_guides: z.array(IssueStrategyGuideSchema),
  strategic_axes: z.array(StrategicAxisSchema),
  recommended_timeline: z.array(RecommendedTimelineStepSchema),
});

export const CycleReportSchema = z.object({
  cycle_id: z.string(),
  diagnosis: z.array(DiagnosisItemSchema),
  opportunities_risks: z.array(OpportunityRiskItemSchema),
  critical_points: z.array(CriticalPointSchema),
  diagnosis_summary: DiagnosisSummarySchema,
  timeline: z.array(TimelineLinkSchema),
  strategy_timeline: StrategyTimelineSchema,
  action_items: ActionItemsReportSchema,
  overview: z.string(),
  overview_warnings: z.array(z.string()),
  coverage_note: z.string(),
});

export const SourceDocSchema = z.object({
  id: z.string(),
  cycle_id: z.string(),
  title: z.string(),
  text: z.string(),
  source_type: SourceTypeSchema,
});
export const SourceDocListSchema = z.array(SourceDocSchema);

export const AddSourceResponseSchema = z.object({ id: z.string() });
export const CycleListSchema = z.array(z.string());

export type SourceType = z.infer<typeof SourceTypeSchema>;
export type SourceDoc = z.infer<typeof SourceDocSchema>;
export type Citation = z.infer<typeof CitationSchema>;
export type DiagnosisItem = z.infer<typeof DiagnosisItemSchema>;
export type OpportunityRiskItem = z.infer<typeof OpportunityRiskItemSchema>;
export type CriticalPoint = z.infer<typeof CriticalPointSchema>;
export type TimelineLink = z.infer<typeof TimelineLinkSchema>;
export type ActionItem = z.infer<typeof ActionItemSchema>;
export type ActionItemsReport = z.infer<typeof ActionItemsReportSchema>;
export type CustomerStrategy = z.infer<typeof CustomerStrategySchema>;
export type ProcessStep = z.infer<typeof ProcessStepSchema>;
export type MetricSnapshot = z.infer<typeof MetricSnapshotSchema>;
export type DiagnosisSummary = z.infer<typeof DiagnosisSummarySchema>;
export type StrategicAxis = z.infer<typeof StrategicAxisSchema>;
export type IssueStrategyGuide = z.infer<typeof IssueStrategyGuideSchema>;
export type RecommendedTimelineStep = z.infer<typeof RecommendedTimelineStepSchema>;
export type StrategyTimeline = z.infer<typeof StrategyTimelineSchema>;
export type CycleReport = z.infer<typeof CycleReportSchema>;
