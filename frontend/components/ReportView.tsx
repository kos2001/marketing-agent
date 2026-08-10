import type { CycleReport } from "@/lib/api";
import { Card, PriorityBadge, SectionTitle, StatusBadge, Tag, Td, Th, TableCard } from "@/components/ui";

export function ReportView({ report }: { report: CycleReport }) {
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <SectionTitle>총평</SectionTitle>
        <p className="text-sm leading-relaxed text-zinc-200">{report.overview}</p>
        {report.overview_warnings.length > 0 && (
          <ul className="mt-3 space-y-1">
            {report.overview_warnings.map((w, i) => (
              <li key={i} className="text-xs text-amber-400">
                근거 미확인: {w}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-3 text-xs text-zinc-500">{report.coverage_note}</p>
      </Card>

      <Card>
        <SectionTitle>현황진단</SectionTitle>
        <ul className="space-y-3">
          {report.diagnosis.length === 0 && <p className="text-sm text-zinc-500">진단 항목 없음</p>}
          {report.diagnosis.map((d) => (
            <li key={d.id} className="border-b border-zinc-800 pb-3 last:border-0 last:pb-0">
              <div className="flex flex-wrap items-center gap-2 text-sm text-zinc-200">
                <Tag>{d.channel}</Tag>
                <span>{d.summary}</span>
                <Tag>{d.kind === "strength" ? "강점" : "약점"}</Tag>
                <StatusBadge status={d.status} />
              </div>
              {d.citations.length > 0 && (
                <ul className="mt-2 space-y-1 pl-4">
                  {d.citations.map((c, i) => (
                    <li key={i} className="text-xs text-zinc-500">
                      &quot;{c.quote}&quot;
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <SectionTitle>기회 / 리스크</SectionTitle>
        <ul className="space-y-3">
          {report.opportunities_risks.length === 0 && <p className="text-sm text-zinc-500">항목 없음</p>}
          {report.opportunities_risks.map((o) => (
            <li key={o.id} className="border-b border-zinc-800 pb-3 last:border-0 last:pb-0">
              <div className="flex flex-wrap items-center gap-2 text-sm text-zinc-200">
                <Tag>{o.kind === "opportunity" ? "기회" : "리스크"}</Tag>
                <span>{o.title}</span>
                {o.additionally_flagged && <Tag>추가 지적 항목</Tag>}
              </div>
              <p className="mt-1 text-xs text-zinc-500">{o.rationale}</p>
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <SectionTitle>Critical Point</SectionTitle>
        <ul className="space-y-3">
          {report.critical_points.length === 0 && <p className="text-sm text-zinc-500">항목 없음</p>}
          {report.critical_points.map((cp) => (
            <li key={cp.id} className="border-b border-zinc-800 pb-3 last:border-0 last:pb-0">
              <p className="text-sm text-zinc-200">{cp.title}</p>
              <p className="mt-1 text-xs text-zinc-500">
                임팩트: {cp.impact} · 시급성: {cp.urgency} · 필요 결정: {cp.decision_needed}
              </p>
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <SectionTitle>타임라인</SectionTitle>
        <ul className="space-y-2">
          {report.timeline.length === 0 && <p className="text-sm text-zinc-500">이어지는 이슈 없음</p>}
          {report.timeline.map((t, i) => (
            <li key={i} className="text-sm text-zinc-200">
              {t.item_title} — {t.prior_cycle_id} 회차부터 이어짐{" "}
              <Tag>{t.repeat_count}회차째 반복</Tag>
            </li>
          ))}
        </ul>
      </Card>

      <div>
        <SectionTitle>Action Items</SectionTitle>
        <TableCard>
          <thead>
            <tr className="border-b border-zinc-800">
              <Th>항목</Th>
              <Th>담당</Th>
              <Th>기한</Th>
              <Th>우선순위</Th>
            </tr>
          </thead>
          <tbody>
            {report.action_items.length === 0 && (
              <tr>
                <Td className="text-zinc-500" colSpan={4}>
                  실행 항목 없음
                </Td>
              </tr>
            )}
            {report.action_items.map((a) => (
              <tr key={a.id} className="border-b border-zinc-800 last:border-0">
                <Td>{a.title}</Td>
                <Td>{a.owner}</Td>
                <Td>{a.due}</Td>
                <Td>
                  <PriorityBadge priority={a.priority} />
                </Td>
              </tr>
            ))}
          </tbody>
        </TableCard>
      </div>
    </div>
  );
}
