"use client";
import { useReport } from "@/lib/use-report";
import { CyclePicker } from "@/components/CyclePicker";
import { StrategySection } from "@/components/report-sections";
import { EmptyState, ErrorNote, PageHeader } from "@/components/ui";

export default function StrategyPage() {
  const reportQuery = useReport();
  const report = reportQuery.data;

  return (
    <>
      <PageHeader
        title="전략 / 타임라인"
        description="사안별 전략 가이드, 전략의 3축, 권장 타임라인, 회차 간 연속성."
      />
      <CyclePicker />

      {reportQuery.error && <ErrorNote message={String(reportQuery.error)} />}
      {!reportQuery.isLoading && !report && (
        <EmptyState message="이 회차의 리포트가 아직 없습니다. 대시보드에서 파이프라인을 실행하세요." />
      )}
      {report && <StrategySection report={report} />}
    </>
  );
}
