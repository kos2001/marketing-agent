from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

VerifiedStatus = Literal["confirmed", "needs_review", "unfounded"]


class SourceDoc(BaseModel):
    id: str
    cycle_id: str
    title: str
    text: str


class Citation(BaseModel):
    quote: str
    source_id: str


class DiagnosisItem(BaseModel):
    id: str
    channel: str
    summary: str
    kind: Literal["strength", "weakness"]
    citations: list[Citation] = Field(default_factory=list)
    status: VerifiedStatus = "needs_review"


class OpportunityRiskItem(BaseModel):
    id: str
    kind: Literal["opportunity", "risk"]
    title: str
    rationale: str
    citations: list[Citation] = Field(default_factory=list)
    additionally_flagged: bool = False


class CriticalPoint(BaseModel):
    id: str
    title: str
    impact: str
    urgency: str
    decision_needed: str
    citations: list[Citation] = Field(default_factory=list)


class TimelineLink(BaseModel):
    item_title: str
    prior_cycle_id: str
    same_issue: bool
    rebuttal_passed: bool
    repeat_count: int = 1


class ActionItem(BaseModel):
    id: str
    title: str
    owner: str
    due: str
    priority: Literal["high", "mid", "low"]
    # knowledge-work-plugins의 marketing/performance-report·sales/pipeline-review
    # 스킬이 쓰는 Impact/Effort 매트릭스 패턴 — priority만으로는 "왜 급한가"와
    # "하기 쉬운가"가 섞여 보이지 않는다.
    impact: Literal["high", "mid", "low"] = "mid"
    effort: Literal["high", "mid", "low"] = "mid"
    source_item_ids: list[str] = Field(default_factory=list)


class ActionItemsReport(BaseModel):
    """Action Items — 즉시 확인(긴급) → 조치 필요(일반) → 최종 요약 순으로 구성."""

    immediate_check: list[ActionItem] = Field(default_factory=list)
    action_needed: list[ActionItem] = Field(default_factory=list)
    final_summary: str = ""


class CustomerStrategy(BaseModel):
    """고객(법인)별 대응 전략 — 특정 고객/세그먼트에 대한 현황과 대응 방향."""

    id: str
    customer: str
    situation: str
    strategy: str
    citations: list[Citation] = Field(default_factory=list)


class ProcessStep(BaseModel):
    """법인 대응 process의 한 단계. 절차적 산출이라 축자 인용을 요구하지 않는다."""

    order: int
    title: str
    description: str
    owner: str = ""


class MetricSnapshot(BaseModel):
    """성과 지표 스냅샷 — knowledge-work-plugins의 marketing/performance-report,
    moai-cowork의 marketing-performance-report 스킬이 쓰는 "측정 → 관리 → 개선"
    대시보드 패턴. current/prior/target은 원문에 있는 숫자만 담는다 — 시장
    평균치 같은 외부 벤치마크는 원문에 없으면 만들어 넣지 않는다."""

    metric: str
    current: str
    prior: str = ""
    change: str = ""
    target: str = ""
    status: Literal["on_track", "at_risk", "off_track"] = "at_risk"


class DiagnosisSummary(BaseModel):
    """현황진단을 임원 의사결정 형식으로 종합한 결과."""

    executive_summary: str = ""
    metrics: list[MetricSnapshot] = Field(default_factory=list)
    customer_strategies: list[CustomerStrategy] = Field(default_factory=list)
    corporate_response_process: list[ProcessStep] = Field(default_factory=list)


class StrategicAxis(BaseModel):
    """전략의 3축 — 이번 회차 진단을 관통하는 핵심 전략 방향 하나."""

    id: str
    title: str
    description: str
    citations: list[Citation] = Field(default_factory=list)


class IssueStrategyGuide(BaseModel):
    """사안별 전략 가이드 — 특정 이슈(상충·리스크·CP)에 대한 대응 방향."""

    id: str
    issue_title: str
    guide: str
    source_item_ids: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


class RecommendedTimelineStep(BaseModel):
    """권장 타임라인의 한 단계 — 앞으로 실행을 언제·무엇을·누가 할지 제안."""

    order: int
    when: str
    action: str
    owner: str = ""


class StrategyTimeline(BaseModel):
    """전략/타임라인 — 사안별 전략 가이드 + 전략의 3축 + 권장 타임라인."""

    issue_guides: list[IssueStrategyGuide] = Field(default_factory=list)
    strategic_axes: list[StrategicAxis] = Field(default_factory=list)
    recommended_timeline: list[RecommendedTimelineStep] = Field(default_factory=list)


class CycleReport(BaseModel):
    cycle_id: str
    diagnosis: list[DiagnosisItem] = Field(default_factory=list)
    opportunities_risks: list[OpportunityRiskItem] = Field(default_factory=list)
    critical_points: list[CriticalPoint] = Field(default_factory=list)
    diagnosis_summary: DiagnosisSummary = Field(default_factory=DiagnosisSummary)
    timeline: list[TimelineLink] = Field(default_factory=list)
    strategy_timeline: StrategyTimeline = Field(default_factory=StrategyTimeline)
    action_items: ActionItemsReport = Field(default_factory=ActionItemsReport)
    overview: str = ""
    overview_warnings: list[str] = Field(default_factory=list)
    coverage_note: str = ""
