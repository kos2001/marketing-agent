"use client";
import { useState } from "react";
import { runPipeline, getReport, type CycleReport } from "@/lib/api";
import { UploadForm } from "@/components/UploadForm";
import { ReportView } from "@/components/ReportView";
import { Button, ErrorNote, PageHeader } from "@/components/ui";

export default function Home() {
  const [cycleId, setCycleId] = useState("2026-W32");
  const [report, setReport] = useState<CycleReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleRun() {
    setBusy(true);
    setError("");
    try {
      const result = await runPipeline(cycleId);
      setReport(result);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleLoadExisting() {
    setError("");
    try {
      const result = await getReport(cycleId);
      setReport(result);
      if (!result) setError("이 회차의 리포트가 아직 없습니다.");
    } catch (e) {
      setError(String(e));
    }
  }

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
        <Button variant="secondary" size="sm" onClick={handleLoadExisting}>
          불러오기
        </Button>
        <Button size="sm" onClick={handleRun} disabled={busy}>
          {busy ? "실행 중..." : "파이프라인 실행"}
        </Button>
      </div>

      <div className="mb-6">
        <UploadForm cycleId={cycleId} onUploaded={() => {}} />
      </div>

      {error && (
        <div className="mb-6">
          <ErrorNote message={error} />
        </div>
      )}
      {report && <ReportView report={report} />}
    </>
  );
}
