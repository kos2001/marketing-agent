import type { ActionItem, CycleReport } from "@/lib/api";
import {
  Card,
  LevelBadge,
  MetricStatusBadge,
  PriorityBadge,
  SectionTitle,
  StatusBadge,
  Tag,
  Td,
  Th,
  TableCard,
} from "@/components/ui";

function ActionItemsTable({ items }: { items: ActionItem[] }) {
  return (
    <TableCard>
      <thead>
        <tr className="border-b border-zinc-800">
          <Th>항목</Th>
          <Th>담당</Th>
          <Th>기한</Th>
          <Th>우선순위</Th>
          <Th>임팩트</Th>
          <Th>실행난이도</Th>
        </tr>
      </thead>
      <tbody>
        {items.length === 0 && (
          <tr>
            <Td className="text-zinc-500" colSpan={6}>
              항목 없음
            </Td>
          </tr>
        )}
        {items.map((a) => (
          <tr key={a.id} className="border-b border-zinc-800 last:border-0">
            <Td>{a.title}</Td>
            <Td>{a.owner}</Td>
            <Td>{a.due}</Td>
            <Td>
              <PriorityBadge priority={a.priority} />
            </Td>
            <Td>
              <LevelBadge label="임팩트" level={a.impact} />
            </Td>
            <Td>
              <LevelBadge label="난이도" level={a.effort} />
            </Td>
          </tr>
        ))}
      </tbody>
    </TableCard>
  );
}

export function ReportView({ report }: { report: CycleReport }) {
  const summary = report.diagnosis_summary;
  const strategy = report.strategy_timeline;

  return (
    <div className="flex flex-col gap-8">
      <Card>
        <SectionTitle>총평 (사실검증됨)</SectionTitle>
        <p className="text-sm leading-relaxed text-zinc-200">{report.overview}</p>
      </Card>

      {/* 현황진단: Executive Summary / 고객별 대응 전략 / 법인 대응 process */}
      <section>
        <h2 className="mb-4 text-lg font-semibold tracking-tight text-zinc-50">현황진단</h2>
        <div className="flex flex-col gap-4">
          <Card>
            <SectionTitle>Executive Summary</SectionTitle>
            <p className="text-sm leading-relaxed text-zinc-200">{summary.executive_summary}</p>
            <p className="mt-3 text-xs text-zinc-500">{report.coverage_note}</p>
          </Card>

          <div>
            <SectionTitle>지표 대시보드</SectionTitle>
            <TableCard>
              <thead>
                <tr className="border-b border-zinc-800">
                  <Th>지표</Th>
                  <Th>이번 값</Th>
                  <Th>이전 값</Th>
                  <Th>변화</Th>
                  <Th>목표</Th>
                  <Th>상태</Th>
                </tr>
              </thead>
              <tbody>
                {summary.metrics.length === 0 && (
                  <tr>
                    <Td className="text-zinc-500" colSpan={6}>
                      원문에서 식별된 정량 지표 없음
                    </Td>
                  </tr>
                )}
                {summary.metrics.map((m, i) => (
                  <tr key={i} className="border-b border-zinc-800 last:border-0">
                    <Td>{m.metric}</Td>
                    <Td>{m.current}</Td>
                    <Td>{m.prior || "—"}</Td>
                    <Td>{m.change || "—"}</Td>
                    <Td>{m.target || "—"}</Td>
                    <Td>
                      <MetricStatusBadge status={m.status} />
                    </Td>
                  </tr>
                ))}
              </tbody>
            </TableCard>
          </div>

          <Card>
            <SectionTitle>채널별 진단</SectionTitle>
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
            <SectionTitle>고객별 대응 전략</SectionTitle>
            <ul className="space-y-3">
              {summary.customer_strategies.length === 0 && (
                <p className="text-sm text-zinc-500">식별된 개별 고객 없음</p>
              )}
              {summary.customer_strategies.map((c) => (
                <li key={c.id} className="border-b border-zinc-800 pb-3 last:border-0 last:pb-0">
                  <p className="text-sm font-medium text-zinc-100">{c.customer}</p>
                  <p className="mt-1 text-xs text-zinc-400">현황: {c.situation}</p>
                  <p className="mt-1 text-xs text-zinc-400">대응: {c.strategy}</p>
                </li>
              ))}
            </ul>
          </Card>

          <div>
            <SectionTitle>법인 대응 Process</SectionTitle>
            <TableCard>
              <thead>
                <tr className="border-b border-zinc-800">
                  <Th>순서</Th>
                  <Th>단계</Th>
                  <Th>설명</Th>
                  <Th>담당</Th>
                </tr>
              </thead>
              <tbody>
                {summary.corporate_response_process.length === 0 && (
                  <tr>
                    <Td className="text-zinc-500" colSpan={4}>
                      절차 없음
                    </Td>
                  </tr>
                )}
                {summary.corporate_response_process.map((p) => (
                  <tr key={p.order} className="border-b border-zinc-800 last:border-0">
                    <Td>{p.order}</Td>
                    <Td>{p.title}</Td>
                    <Td>{p.description}</Td>
                    <Td>{p.owner || "—"}</Td>
                  </tr>
                ))}
              </tbody>
            </TableCard>
          </div>
        </div>
      </section>

      {/* 전략/타임라인: 사안별 전략 가이드 / 전략의 3축 / 권장 타임라인 */}
      <section>
        <h2 className="mb-4 text-lg font-semibold tracking-tight text-zinc-50">전략 / 타임라인</h2>
        <div className="flex flex-col gap-4">
          <Card>
            <SectionTitle>전략의 3축</SectionTitle>
            <div className="grid gap-3 sm:grid-cols-3">
              {strategy.strategic_axes.map((a) => (
                <div key={a.id} className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                  <p className="text-sm font-medium text-zinc-100">{a.title}</p>
                  <p className="mt-1 text-xs text-zinc-400">{a.description}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <SectionTitle>사안별 전략 가이드</SectionTitle>
            <ul className="space-y-3">
              {strategy.issue_guides.length === 0 && <p className="text-sm text-zinc-500">항목 없음</p>}
              {strategy.issue_guides.map((g) => (
                <li key={g.id} className="border-b border-zinc-800 pb-3 last:border-0 last:pb-0">
                  <p className="text-sm font-medium text-zinc-100">{g.issue_title}</p>
                  <p className="mt-1 text-xs text-zinc-400">{g.guide}</p>
                </li>
              ))}
            </ul>
          </Card>

          <div>
            <SectionTitle>권장 타임라인</SectionTitle>
            <TableCard>
              <thead>
                <tr className="border-b border-zinc-800">
                  <Th>순서</Th>
                  <Th>시점</Th>
                  <Th>실행 항목</Th>
                  <Th>담당</Th>
                </tr>
              </thead>
              <tbody>
                {strategy.recommended_timeline.length === 0 && (
                  <tr>
                    <Td className="text-zinc-500" colSpan={4}>
                      제안 없음
                    </Td>
                  </tr>
                )}
                {strategy.recommended_timeline.map((s) => (
                  <tr key={s.order} className="border-b border-zinc-800 last:border-0">
                    <Td>{s.order}</Td>
                    <Td>{s.when}</Td>
                    <Td>{s.action}</Td>
                    <Td>{s.owner || "—"}</Td>
                  </tr>
                ))}
              </tbody>
            </TableCard>
          </div>

          <Card>
            <SectionTitle>회차 간 연속성</SectionTitle>
            <ul className="space-y-2">
              {report.timeline.length === 0 && <p className="text-sm text-zinc-500">이어지는 이슈 없음</p>}
              {report.timeline.map((t, i) => (
                <li key={i} className="text-sm text-zinc-200">
                  {t.item_title} — {t.prior_cycle_id} 회차부터 이어짐 <Tag>{t.repeat_count}회차째 반복</Tag>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </section>

      {/* Action Items: 즉시 확인 -> 조치 필요 -> 최종 요약 */}
      <section>
        <h2 className="mb-4 text-lg font-semibold tracking-tight text-zinc-50">Action Items</h2>
        <div className="flex flex-col gap-4">
          <div>
            <SectionTitle>즉시 확인</SectionTitle>
            <ActionItemsTable items={report.action_items.immediate_check} />
          </div>
          <div>
            <SectionTitle>조치 필요</SectionTitle>
            <ActionItemsTable items={report.action_items.action_needed} />
          </div>
          <Card>
            <SectionTitle>최종 요약</SectionTitle>
            <p className="text-sm leading-relaxed text-zinc-200">{report.action_items.final_summary}</p>
          </Card>
        </div>
      </section>

      {/* 기회/리스크, Critical Point는 진단의 원재료로 참고용 노출 */}
      <section>
        <h2 className="mb-4 text-lg font-semibold tracking-tight text-zinc-50">참고: 기회 / 리스크 / Critical Point</h2>
        <div className="flex flex-col gap-4">
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

          {report.overview_warnings.length > 0 && (
            <Card>
              <SectionTitle>총평 근거 미확인 경고</SectionTitle>
              <ul className="space-y-1">
                {report.overview_warnings.map((w, i) => (
                  <li key={i} className="text-xs text-amber-400">
                    근거 미확인: {w}
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      </section>
    </div>
  );
}
