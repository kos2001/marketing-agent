from __future__ import annotations
from .llm import ChatClient, extract_json
from .schemas import TimelineLink

MATCH_SYSTEM = (
    "현재 회차 이슈 제목들과 과거 회차 이슈 제목들을 비교해, 같은 사안으로 보이는 "
    '후보 쌍을 고르십시오. JSON: {"matches": [{"current": str, "prior_cycle": str, '
    '"prior_title": str}]}. 확실하지 않으면 포함하지 마십시오.'
)

REBUTTAL_SYSTEM = (
    "두 이슈 제목이 같은 사안이라는 주장에 대해, 그것이 실은 서로 다른 사안이라는 "
    '반박을 시도하십시오. 반박이 설득력 있으면 same_issue를 false로, 반박하지 '
    '못하면 true로 답하십시오. JSON: {"same_issue": bool}.'
)


async def run_t1(
    client: ChatClient,
    cycle_id: str,
    current_titles: list[str],
    prior_cycle_titles: dict[str, list[str]],
) -> list[TimelineLink]:
    if not current_titles or not prior_cycle_titles:
        return []
    prior_text = "\n".join(
        f"[{cid}] " + ", ".join(titles) for cid, titles in prior_cycle_titles.items()
    )
    user = f"현재 회차 이슈:\n{', '.join(current_titles)}\n\n과거 회차 이슈:\n{prior_text}"
    raw = await client.chat(MATCH_SYSTEM, user, session_id="t1-match")
    matches = extract_json(raw).get("matches", [])

    links: list[TimelineLink] = []
    for m in matches:
        rebut_user = (
            f"주장: '{m['current']}' (현재 회차)와 '{m['prior_title']}' ({m['prior_cycle']} 회차)"
            "는 같은 사안이다. 이 주장을 반박하라."
        )
        raw2 = await client.chat(REBUTTAL_SYSTEM, rebut_user, session_id="t1-rebut")
        same = extract_json(raw2).get("same_issue", False)
        if same:
            links.append(TimelineLink(
                item_title=m["current"],
                prior_cycle_id=m["prior_cycle"],
                same_issue=True,
                rebuttal_passed=True,
            ))
    return links
