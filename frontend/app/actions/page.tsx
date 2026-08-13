"use client";
import { useReport } from "@/lib/use-report";
import { CyclePicker } from "@/components/CyclePicker";
import { ActionItemsSection } from "@/components/report-sections";
import { EmptyState, ErrorNote, PageHeader } from "@/components/ui";

export default function ActionsPage() {
  const reportQuery = useReport();
  const report = reportQuery.data;

  return (
    <>
      <PageHeader title="Action Items" description="즉시 확인 → 조치 필요 → 최종 요약." />
      <CyclePicker />

      {reportQuery.error && <ErrorNote message={String(reportQuery.error)} />}
      {!reportQuery.isLoading && !report && (
        <EmptyState message="이 회차의 리포트가 아직 없습니다. 대시보드에서 파이프라인을 실행하세요." />
      )}
      {report && <ActionItemsSection report={report} />}
    </>
  );
}
