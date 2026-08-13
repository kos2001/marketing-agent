"use client";
import { useQuery } from "@tanstack/react-query";
import { getSources, listCycles, SOURCE_TYPE_LABEL, type SourceType } from "@/lib/api";
import { useCycle } from "@/lib/cycle-context";
import { CyclePicker } from "@/components/CyclePicker";
import { Card, EmptyState, ErrorNote, PageHeader, SectionTitle, Td, Th, TableCard } from "@/components/ui";

// mi-report(~/gitspace/mi-report/frontend/src/app/collection/results/page.tsx)의
// KPI 카드 + 소스별 집계 패턴을 옮겼다. 그쪽은 커넥터가 지속 수집한 전체
// 코퍼스를 다루지만, 이 프로젝트는 회차 단위라 "이 회차의 수집 현황"으로
// 범위를 좁혔다(전체 회차 수는 참고용으로만 곁들인다).
function Kpi({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <Card>
      <p className="text-xs text-zinc-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-zinc-50">{value}</p>
      {hint && <p className="mt-1 text-[11px] text-zinc-500">{hint}</p>}
    </Card>
  );
}

export default function CollectionResultsPage() {
  const { cycleId } = useCycle();
  const sourcesQuery = useQuery({ queryKey: ["sources", cycleId], queryFn: () => getSources(cycleId) });
  const cyclesQuery = useQuery({ queryKey: ["cycles"], queryFn: listCycles });

  const sources = sourcesQuery.data ?? [];
  const totalChars = sources.reduce((sum, s) => sum + s.text.length, 0);
  const byType = new Map<SourceType, number>();
  for (const s of sources) byType.set(s.source_type, (byType.get(s.source_type) ?? 0) + 1);
  const typeBreakdown = Array.from(byType.entries()).sort((a, b) => b[1] - a[1]);

  return (
    <>
      <PageHeader
        title="수집 결과"
        description="이 회차의 수집 현황 요약 — 소스 종류별 건수와 분량."
      />
      <CyclePicker />

      {sourcesQuery.error && <ErrorNote message={String(sourcesQuery.error)} />}
      {!sourcesQuery.isLoading && sources.length === 0 && (
        <EmptyState message="이 회차에 수집된 자료가 없습니다. 위 '수집 자료' 페이지에서 추가하세요." />
      )}

      {sources.length > 0 && (
        <div className="flex flex-col gap-8">
          <section className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Kpi label="수집 자료" value={sources.length} hint={`${cycleId} 회차`} />
            <Kpi label="소스 종류" value={typeBreakdown.length} hint={`전체 ${Object.keys(SOURCE_TYPE_LABEL).length}종 중`} />
            <Kpi label="총 텍스트 분량" value={totalChars.toLocaleString()} hint="글자 수 합계" />
            <Kpi label="전체 회차" value={cyclesQuery.data?.length ?? "—"} hint="리포트가 생성된 회차 수" />
          </section>

          <div>
            <SectionTitle>소스 종류별 집계</SectionTitle>
            <TableCard>
              <thead>
                <tr className="border-b border-zinc-800">
                  <Th>소스 종류</Th>
                  <Th>건수</Th>
                  <Th>비율</Th>
                </tr>
              </thead>
              <tbody>
                {typeBreakdown.map(([type, count]) => (
                  <tr key={type} className="border-b border-zinc-800 last:border-0">
                    <Td>{SOURCE_TYPE_LABEL[type]}</Td>
                    <Td>{count}</Td>
                    <Td>{Math.round((count / sources.length) * 100)}%</Td>
                  </tr>
                ))}
              </tbody>
            </TableCard>
          </div>
        </div>
      )}
    </>
  );
}
