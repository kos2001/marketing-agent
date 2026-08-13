"""데모 데이터 — 저장소가 비어 있을 때 화면을 바로 채워 보여준다.

LLM 호출 없이 정적으로 구성한다. 값은 이 저장소를 실제 hermes api_server로
검증할 때 나온 산출물의 패턴을 그대로 따른다(Executive Summary/지표 대시보드/
고객별 대응 전략/전략의 3축/Action Items 구조가 실측과 동일한 모양).
"""
from __future__ import annotations

from .schemas import (
    ActionItem,
    ActionItemsReport,
    Citation,
    CriticalPoint,
    CustomerStrategy,
    DiagnosisItem,
    DiagnosisSummary,
    IssueStrategyGuide,
    MetricSnapshot,
    OpportunityRiskItem,
    ProcessStep,
    RecommendedTimelineStep,
    SourceDoc,
    StrategicAxis,
    StrategyTimeline,
    TimelineLink,
    CycleReport,
)
from .storage import Store
from . import search as search_mod

DEMO_CYCLE_ID = "demo-2026-W30"

DEMO_SOURCE = SourceDoc(
    id="demo-s1",
    cycle_id=DEMO_CYCLE_ID,
    title="8월 이메일 캠페인 및 법인 고객 현황 (데모 데이터)",
    text=(
        "이메일 뉴스레터 오픈율이 지난달 12%에서 이번 달 8%로 하락했다(목표 15%). "
        "인스타그램 팔로워는 3,200명에서 4,100명으로 증가했다(목표 5,000명). "
        "구독 해지 건수가 주간 15건에서 40건으로 늘었다. "
        "ACME 법인 구매팀 김철수 과장이 뉴스레터 콘텐츠 품질에 불만을 제기하며 "
        "계약 재검토를 언급했다. Beta Corp는 특별한 이슈 없이 정상적으로 "
        "서비스를 이용 중이라고 밝혔다."
    ),
)

_QUOTE_OPEN_RATE = "이메일 뉴스레터 오픈율이 지난달 12%에서 이번 달 8%로 하락했다"
_QUOTE_UNSUB = "구독 해지 건수가 주간 15건에서 40건으로 늘었다"
_QUOTE_INSTA = "인스타그램 팔로워는 3,200명에서 4,100명으로 증가했다"
_QUOTE_ACME = "ACME 법인 구매팀 김철수 과장이 뉴스레터 콘텐츠 품질에 불만을 제기하며 계약 재검토를 언급했다"
_QUOTE_BETA = "Beta Corp는 특별한 이슈 없이 정상적으로 서비스를 이용 중이라고 밝혔다"

DEMO_REPORT = CycleReport(
    cycle_id=DEMO_CYCLE_ID,
    diagnosis=[
        DiagnosisItem(
            id="demo-d1-1", channel="이메일 뉴스레터", summary="오픈율이 12%에서 8%로 하락",
            kind="weakness", status="confirmed",
            citations=[Citation(quote=_QUOTE_OPEN_RATE, source_id="demo-s1")],
        ),
        DiagnosisItem(
            id="demo-d1-2", channel="이메일 구독", summary="주간 구독 해지가 15건에서 40건으로 급증",
            kind="weakness", status="confirmed",
            citations=[Citation(quote=_QUOTE_UNSUB, source_id="demo-s1")],
        ),
        DiagnosisItem(
            id="demo-d1-3", channel="인스타그램", summary="팔로워가 3,200명에서 4,100명으로 증가",
            kind="strength", status="confirmed",
            citations=[Citation(quote=_QUOTE_INSTA, source_id="demo-s1")],
        ),
    ],
    opportunities_risks=[
        OpportunityRiskItem(
            id="demo-o1", kind="risk", title="이메일 뉴스레터 오픈율 급락(12%→8%)",
            rationale="핵심 커뮤니케이션 채널의 오픈율이 한 달 만에 1/3 하락해 수신자 관심도 저하 신호로 보인다.",
            citations=[Citation(quote=_QUOTE_OPEN_RATE, source_id="demo-s1")],
        ),
        OpportunityRiskItem(
            id="demo-o2", kind="risk", title="구독 해지 급증(15건→40건)",
            rationale="약 2.7배 급증한 수치로, 기존 잠재고객 기반 유출이 심화되고 있다.",
            citations=[Citation(quote=_QUOTE_UNSUB, source_id="demo-s1")],
        ),
        OpportunityRiskItem(
            id="demo-o3", kind="opportunity", title="인스타그램 팔로워 성장(3,200명→4,100명)",
            rationale="이메일 채널 하락과 대비되어 성장 중인 유일한 접점으로, 신규 도달 확장에 활용할 수 있다.",
            citations=[Citation(quote=_QUOTE_INSTA, source_id="demo-s1")],
        ),
    ],
    critical_points=[
        CriticalPoint(
            id="demo-cp1", title="이메일 오픈율 급락의 원인 방치 위험",
            impact="콘텐츠 적합성·발송 빈도·제목 품질 등 이메일 채널 코어 지표가 동시에 무너지고 있다는 신호다.",
            urgency="high",
            decision_needed="오픈율 하락 원인을 분해 분석하고, 다음 발송 전에 개선안(세그먼트 정비, 제목 A/B 테스트)을 확정할 것",
            citations=[Citation(quote=_QUOTE_OPEN_RATE, source_id="demo-s1")],
        ),
    ],
    diagnosis_summary=DiagnosisSummary(
        executive_summary=(
            "이번 사이클의 핵심 악화 지표는 이메일 뉴스레터 채널이다. 오픈율이 12%에서 8%로 "
            "하락(목표 15%)하고 주간 구독 해지가 15건에서 40건으로 급증해, 콘텐츠 품질 저하가 "
            "해지와 법인 고객 불만의 공통 원인으로 작용하는 정황이다. 특히 주요 법인 고객 ACME "
            "구매팀이 콘텐츠 품질 불만과 함께 계약 재검토를 언급해 실질적인 매출 이탈 리스크가 "
            "임박한 것으로 판단된다. 반면 인스타그램 팔로워는 3,200명에서 4,100명으로 성장했고 "
            "Beta Corp 고객은 안정적으로 유지 중이다."
        ),
        metrics=[
            MetricSnapshot(metric="이메일 뉴스레터 오픈율", current="8%", prior="12%",
                            change="-4%p", target="15%", status="off_track"),
            MetricSnapshot(metric="인스타그램 팔로워", current="4,100명", prior="3,200명",
                            change="+900명", target="5,000명", status="at_risk"),
            MetricSnapshot(metric="주간 구독 해지 건수", current="40건", prior="15건",
                            change="+25건", target="", status="at_risk"),
        ],
        customer_strategies=[
            CustomerStrategy(
                id="demo-cust1", customer="ACME (법인 구매팀 김철수 과장)",
                situation="뉴스레터 콘텐츠 품질에 불만을 제기하며 계약 재검토를 언급해 이탈 위험이 임박했다.",
                strategy="김철수 과장을 우선 접점으로 콘텐츠 불만 요인을 구체적으로 청취하고, 개선안을 제시해 신뢰를 복원한다.",
                risk_level="critical",
                citations=[Citation(quote=_QUOTE_ACME, source_id="demo-s1")],
            ),
            CustomerStrategy(
                id="demo-cust2", customer="Beta Corp",
                situation="특별한 이슈 없이 정상적으로 서비스를 이용 중이다.",
                strategy="현재 대응을 유지하되, 분기별 정기 점검으로 관계를 관리한다.",
                risk_level="stable",
                citations=[Citation(quote=_QUOTE_BETA, source_id="demo-s1")],
            ),
        ],
        corporate_response_process=[
            ProcessStep(order=1, title="법인 고객 이슈 접수 및 우선순위 정리", description="불만·재계약 검토 등 위험 신호를 접수해 심각도순으로 정리한다.", owner="영업/고객관리"),
            ProcessStep(order=2, title="법인별 실무 접점 직접 소통", description="담당 AE가 해당 법인 실무자와 직접 소통해 구체적 요구사항을 파악한다.", owner="계정 담당 AE"),
            ProcessStep(order=3, title="개선안 수립 및 실행", description="원인 분석 결과를 바탕으로 개선안을 만들어 적용한다.", owner="콘텐츠/마케팅 기획"),
            ProcessStep(order=4, title="결과 공유 및 후속 관리", description="개선 결과를 법인에 공유하고 재발 여부를 모니터링한다.", owner="영업 책임자"),
        ],
    ),
    timeline=[
        TimelineLink(
            item_title="이메일 뉴스레터 오픈율 하락", prior_cycle_id="demo-2026-W29",
            same_issue=True, rebuttal_passed=True, repeat_count=2,
        ),
    ],
    strategy_timeline=StrategyTimeline(
        issue_guides=[
            IssueStrategyGuide(
                id="demo-guide1", issue_title="이메일 뉴스레터 오픈율 하락",
                guide="콘텐츠·발송 빈도·제목 품질을 분해 진단하고, 다음 발송 전 A/B 테스트로 개선안을 검증한다.",
                source_item_ids=["demo-d1-1", "demo-cp1"],
                citations=[Citation(quote=_QUOTE_OPEN_RATE, source_id="demo-s1")],
            ),
            IssueStrategyGuide(
                id="demo-guide2", issue_title="ACME 법인 고객 콘텐츠 불만",
                guide="담당 AE가 즉시 접촉해 불만 요인을 구체화하고, 개선 로드맵을 공유해 계약 재검토를 철회하도록 유도한다.",
                source_item_ids=["demo-cust1"],
                citations=[Citation(quote=_QUOTE_ACME, source_id="demo-s1")],
            ),
        ],
        strategic_axes=[
            StrategicAxis(id="demo-axis1", title="이메일 채널 콘텐츠 품질 재건",
                          description="오픈율·해지 지표 동반 악화의 근본 원인(콘텐츠·발송 전략)을 진단하고 개선한다.",
                          citations=[Citation(quote=_QUOTE_OPEN_RATE, source_id="demo-s1")]),
            StrategicAxis(id="demo-axis2", title="법인 고객 이탈 방어",
                          description="ACME 등 위험 신호가 있는 법인 계정에 우선 자원을 투입해 매출 연속성을 지킨다.",
                          citations=[Citation(quote=_QUOTE_ACME, source_id="demo-s1")]),
            StrategicAxis(id="demo-axis3", title="성장 채널을 통한 유입 다각화",
                          description="이메일 의존도를 낮추고 성장 중인 인스타그램을 신규·재흡수 채널로 육성한다.",
                          citations=[Citation(quote=_QUOTE_INSTA, source_id="demo-s1")]),
        ],
        recommended_timeline=[
            RecommendedTimelineStep(order=1, when="즉시", action="ACME 법인 고객 접촉 및 계약 재검토 대응 착수", owner="계정 담당 AE"),
            RecommendedTimelineStep(order=2, when="1주차", action="오픈율·해지 급증의 공통 원인 진단", owner="마케팅 리드"),
            RecommendedTimelineStep(order=3, when="2주차", action="콘텐츠·발송 전략 개선안 실행", owner="콘텐츠 팀"),
            RecommendedTimelineStep(order=4, when="당월 말", action="개선 효과 및 ACME 관계 상태 재점검", owner="마케팅/영업 리드"),
        ],
    ),
    action_items=ActionItemsReport(
        immediate_check=[
            ActionItem(id="demo-ai1", title="ACME 법인 고객 계약 재검토 즉시 대응",
                       owner="계정 담당 AE", due="2026-08-14", priority="high",
                       impact="high", effort="mid", source_item_ids=["demo-cust1"]),
            ActionItem(id="demo-ai2", title="구독 해지 급증(15건→40건) 원인 규명",
                       owner="마케팅/데이터", due="2026-08-14", priority="high",
                       impact="high", effort="mid", source_item_ids=["demo-d1-2"]),
        ],
        action_needed=[
            ActionItem(id="demo-ai3", title="이메일 콘텐츠 A/B 테스트 실시",
                       owner="콘텐츠 팀", due="2026-08-25", priority="mid",
                       impact="mid", effort="mid", source_item_ids=["demo-d1-1"]),
            ActionItem(id="demo-ai4", title="인스타그램 성장세를 신규 유입 퍼널로 전환",
                       owner="소셜 채널 담당", due="2026-09-01", priority="mid",
                       impact="mid", effort="high", source_item_ids=["demo-d1-3"]),
        ],
        final_summary=(
            "ACME 법인 대응과 구독 해지 원인 규명을 이번 주 최우선으로 처리하고, "
            "이후 콘텐츠 개선과 인스타그램 채널 활용을 순차적으로 진행한다."
        ),
    ),
    overview=(
        "이번 사이클은 이메일 채널의 오픈율 하락과 구독 해지 급증이 동시에 나타나며, "
        "핵심 법인 고객 ACME의 계약 재검토 언급까지 겹쳐 위험도가 높다. 인스타그램은 "
        "유일하게 성장 중인 채널로 대체·보완 자원으로 활용할 수 있다. 이메일 콘텐츠 "
        "개선과 ACME 관계 안정화가 이번 사이클의 최우선 과제다."
    ),
    overview_warnings=[],
    coverage_note="1/1개 자료 반영 (데모 데이터)",
)


def seed_demo_data(store: Store) -> None:
    """저장소에 회차가 하나도 없을 때만 데모 데이터를 채운다.

    실제 사용자가 자료를 올리기 시작하면(list_cycles()가 비어 있지 않으면)
    다시 실행되지 않는다 — 실 데이터를 덮어쓰지 않는다.
    """
    if store.list_cycles():
        return
    store.add_source(DEMO_SOURCE)
    search_mod.index_embedding(store, DEMO_SOURCE)
    store.save_report(DEMO_REPORT)
