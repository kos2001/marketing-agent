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
    source_item_ids: list[str] = Field(default_factory=list)


class CycleReport(BaseModel):
    cycle_id: str
    diagnosis: list[DiagnosisItem] = Field(default_factory=list)
    opportunities_risks: list[OpportunityRiskItem] = Field(default_factory=list)
    critical_points: list[CriticalPoint] = Field(default_factory=list)
    timeline: list[TimelineLink] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    overview: str = ""
    overview_warnings: list[str] = Field(default_factory=list)
    coverage_note: str = ""
