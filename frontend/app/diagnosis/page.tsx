"use client";
import { useReport } from "@/lib/use-report";
import { CyclePicker } from "@/components/CyclePicker";
import { DiagnosisSection, ReferenceSection } from "@/components/report-sections";
import { EmptyState, ErrorNote, PageHeader } from "@/components/ui";

export default function DiagnosisPage() {
  const reportQuery = useReport();
  const report = reportQuery.data;

  return (
    <>
      <PageHeader
        title="현황진단"
        description="Executive Summary, 지표 대시보드, 채널별 진단, 고객별 대응 전략, 법인 대응 Process."
      />
      <CyclePicker />

      {reportQuery.error && <ErrorNote message={String(reportQuery.error)} />}
      {!reportQuery.isLoading && !report && (
        <EmptyState message="이 회차의 리포트가 아직 없습니다. 대시보드에서 파이프라인을 실행하세요." />
      )}
      {report && (
        <div className="flex flex-col gap-8">
          <DiagnosisSection report={report} />
          <section>
            <h2 className="mb-4 text-lg font-semibold tracking-tight text-zinc-50">
              참고: 기회 / 리스크 / Critical Point
            </h2>
            <ReferenceSection report={report} />
          </section>
        </div>
      )}
    </>
  );
}
