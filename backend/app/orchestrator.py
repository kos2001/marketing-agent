from __future__ import annotations
import asyncio
from .llm import ChatClient
from .storage import Store
from .schemas import CycleReport, TimelineLink
from .agents_diagnosis import run_d1, run_d2, run_d3, run_v, run_v2
from .agents_timeline import run_t1
from .agents_summary import run_summary
from .agents_strategy import run_strategy
from .agents_actions import run_action_items, run_overview

AGENT_CATALOG: tuple[dict[str, object], ...] = (
    {"id": "D1", "phase": "diagnose", "needs": ()},
    {"id": "D2", "phase": "diagnose", "needs": ()},
    {"id": "D3", "phase": "diagnose", "needs": ()},
    {"id": "V", "phase": "diagnose", "needs": ()},
    {"id": "V2", "phase": "diagnose", "needs": ()},
    {"id": "T1", "phase": "timeline", "needs": ("D1", "V", "D2", "D3")},
    {"id": "SUMMARY", "phase": "compose", "needs": ("D1", "D2", "D3")},
    {"id": "STRATEGY", "phase": "compose", "needs": ("D1", "D2", "D3", "T1")},
    {"id": "ACTIONS", "phase": "compose", "needs": ("D1", "D2", "D3", "T1")},
    {"id": "V3", "phase": "compose", "needs": ("D1", "D2", "D3", "V", "V2", "T1")},
)


def _compute_repeat_count(link: TimelineLink, store: Store) -> int:
    """이 링크의 item_title이 몇 회차째 이어지는지, 과거 회차의 타임라인 링크를
    따라가며 센다. 최소 2(이번 회차 + 링크된 직전 회차)에서 시작해, 그 직전
    회차 자신도 더 과거로 이어지는 링크를 갖고 있으면 계속 거슬러 올라간다."""
    count = 2
    prior_report = store.get_report(link.prior_cycle_id)
    while prior_report:
        match = next((t for t in prior_report.timeline if t.item_title == link.item_title), None)
        if not match:
            break
        count += 1
        prior_report = store.get_report(match.prior_cycle_id)
    return count


async def run_pipeline(client: ChatClient, store: Store, cycle_id: str) -> CycleReport:
    sources = store.sources_for_cycle(cycle_id)
    source_map = {s.id: s.text for s in sources}

    # phase: diagnose — D1/D2/D3/V/V2 are independent (needs=()) and run in parallel
    d1_items, d2_items, d3_items = await asyncio.gather(
        run_d1(client, sources), run_d2(client, sources), run_d3(client, sources)
    )
    verified_d1, v2_additional = await asyncio.gather(
        run_v(client, sources, d1_items), run_v2(client, sources, d2_items)
    )
    opp_risks = d2_items + v2_additional

    # phase: timeline — needs D1,V,D2,D3 (declared above)
    current_titles = [i.summary for i in verified_d1] + [i.title for i in opp_risks] + [i.title for i in d3_items]
    prior_cycle_ids = store.prior_cycles(cycle_id)
    prior_titles: dict[str, list[str]] = {}
    for pc in prior_cycle_ids:
        prior_report = store.get_report(pc)
        if prior_report:
            prior_titles[pc] = (
                [i.summary for i in prior_report.diagnosis]
                + [i.title for i in prior_report.opportunities_risks]
                + [i.title for i in prior_report.critical_points]
            )
    raw_timeline = await run_t1(client, cycle_id, current_titles, prior_titles)
    timeline = [
        t.model_copy(update={"repeat_count": _compute_repeat_count(t, store)})
        for t in raw_timeline
    ]

    # phase: compose — SUMMARY needs D1,D2,D3; STRATEGY/ACTIONS/V3 also need T1
    diagnosis_summary, strategy_timeline, action_items, (overview_text, warnings) = await asyncio.gather(
        run_summary(client, sources, verified_d1, opp_risks, d3_items),
        run_strategy(client, sources, verified_d1, opp_risks, d3_items, timeline),
        run_action_items(client, verified_d1, opp_risks, d3_items),
        run_overview(client, verified_d1, opp_risks, d3_items, timeline, source_map),
    )

    total_sources = len(sources)
    coverage_note = f"{total_sources}/{total_sources}개 자료 반영" if total_sources else "입력 자료 없음"

    report = CycleReport(
        cycle_id=cycle_id,
        diagnosis=verified_d1,
        opportunities_risks=opp_risks,
        critical_points=d3_items,
        diagnosis_summary=diagnosis_summary,
        timeline=timeline,
        strategy_timeline=strategy_timeline,
        action_items=action_items,
        overview=overview_text,
        overview_warnings=warnings,
        coverage_note=coverage_note,
    )
    store.save_report(report)
    return report
