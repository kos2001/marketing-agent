"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { runPipeline, getReport } from "@/lib/api";
import { UploadForm } from "@/components/UploadForm";
import { ReportView } from "@/components/ReportView";
import { Button, ErrorNote, PageHeader } from "@/components/ui";

export default function Home() {
  const [cycleId, setCycleId] = useState("2026-W32");
  const queryClient = useQueryClient();

  const reportQuery = useQuery({
    queryKey: ["report", cycleId],
    queryFn: () => getReport(cycleId),
    enabled: false,
  });

  const runMutation = useMutation({
    mutationFn: () => runPipeline(cycleId),
    onSuccess: (data) => {
      queryClient.setQueryData(["report", cycleId], data);
    },
  });

  const report = runMutation.data ?? reportQuery.data;
  const error = runMutation.error ?? reportQuery.error;
  const notFound = reportQuery.isFetched && reportQuery.data === null && !runMutation.data;

  return (
    <>
      <PageHeader
        title="marketing-agent"
        description="영업/마케팅 자료를 업로드하고 현황진단·타임라인·Action Items를 생성합니다."
      />

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-sm text-zinc-300">
          회차
          <input
            value={cycleId}
            onChange={(e) => setCycleId(e.target.value)}
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-1.5 text-sm text-zinc-100 outline-none focus:border-sky-500"
          />
        </label>
        <Button variant="secondary" size="sm" onClick={() => reportQuery.refetch()} disabled={reportQuery.isFetching}>
          {reportQuery.isFetching ? "불러오는 중..." : "불러오기"}
        </Button>
        <Button size="sm" onClick={() => runMutation.mutate()} disabled={runMutation.isPending}>
          {runMutation.isPending ? "실행 중..." : "파이프라인 실행"}
        </Button>
      </div>

      <div className="mb-6">
        <UploadForm cycleId={cycleId} onUploaded={() => {}} />
      </div>

      {error && (
        <div className="mb-6">
          <ErrorNote message={String(error)} />
        </div>
      )}
      {notFound && (
        <div className="mb-6">
          <ErrorNote message="이 회차의 리포트가 아직 없습니다." />
        </div>
      )}
      {report && <ReportView report={report} />}
    </>
  );
}
