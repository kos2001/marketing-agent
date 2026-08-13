"use client";
import { useQuery } from "@tanstack/react-query";
import { getSources, SOURCE_TYPE_LABEL } from "@/lib/api";
import { useCycle } from "@/lib/cycle-context";
import { CyclePicker } from "@/components/CyclePicker";
import { Card, EmptyState, ErrorNote, PageHeader, SectionTitle, Tag } from "@/components/ui";

export default function SourcesPage() {
  const { cycleId } = useCycle();
  const sourcesQuery = useQuery({
    queryKey: ["sources", cycleId],
    queryFn: () => getSources(cycleId),
  });

  return (
    <>
      <PageHeader
        title="수집 자료"
        description="이 회차에 업로드된 원문 — 이메일 캠페인·소셜미디어·CRM·애널리틱스·고객 피드백 등 다양한 소스를 태깅해 모읍니다."
      />
      <CyclePicker />

      {sourcesQuery.error && <ErrorNote message={String(sourcesQuery.error)} />}
      {!sourcesQuery.isLoading && sourcesQuery.data?.length === 0 && (
        <EmptyState message="이 회차에 업로드된 자료가 없습니다. 대시보드에서 자료를 추가하세요." />
      )}
      <div className="flex flex-col gap-4">
        {sourcesQuery.data?.map((s) => (
          <Card key={s.id}>
            <div className="flex flex-wrap items-center gap-2">
              <SectionTitle>{s.title}</SectionTitle>
              <Tag>{SOURCE_TYPE_LABEL[s.source_type]}</Tag>
            </div>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-400">{s.text}</p>
          </Card>
        ))}
      </div>
    </>
  );
}
