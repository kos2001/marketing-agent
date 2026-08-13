"use client";
import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { runPipeline } from "@/lib/api";
import { useCycle } from "@/lib/cycle-context";
import { useReport } from "@/lib/use-report";
import { CyclePicker } from "@/components/CyclePicker";
import { OverviewCard } from "@/components/report-sections";
import { Button, EmptyState, ErrorNote, PageHeader } from "@/components/ui";

export default function Home() {
  const { cycleId } = useCycle();
  const reportQuery = useReport();
  const queryClient = useQueryClient();

  const runMutation = useMutation({
    mutationFn: () => runPipeline(cycleId),
    onSuccess: (data) => {
      queryClient.setQueryData(["report", cycleId], data);
    },
  });

  const report = runMutation.data ?? reportQuery.data;

  return (
    <>
      <PageHeader
        title="marketing-agent"
        description="영업/마케팅 자료를 진단해 현황진단·전략/타임라인·Action Items를 생성합니다."
      />

      <CyclePicker />

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <Button onClick={() => runMutation.mutate()} disabled={runMutation.isPending}>
          {runMutation.isPending ? "실행 중..." : "파이프라인 실행"}
        </Button>
        <Link href="/sources">
          <Button variant="secondary">자료 추가하러 가기</Button>
        </Link>
        <p className="text-xs text-zinc-500">
          왼쪽 사이드바에서 수집 자료·현황진단·전략/타임라인·Action Items를 각각 확인할 수 있습니다.
        </p>
      </div>

      {runMutation.error && (
        <div className="mb-6">
          <ErrorNote message={String(runMutation.error)} />
        </div>
      )}
      {reportQuery.error && (
        <div className="mb-6">
          <ErrorNote message={String(reportQuery.error)} />
        </div>
      )}

      {report ? (
        <OverviewCard report={report} />
      ) : (
        !reportQuery.isLoading && (
          <EmptyState
            message="이 회차의 리포트가 아직 없습니다. 자료를 추가하고 파이프라인을 실행하세요."
            action={
              <Link href="/sources">
                <Button size="sm">자료 추가하러 가기</Button>
              </Link>
            }
          />
        )
      )}
    </>
  );
}
