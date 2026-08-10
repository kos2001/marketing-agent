"use client";
import { useState } from "react";
import { runPipeline, getReport, type CycleReport } from "@/lib/api";
import { UploadForm } from "@/components/UploadForm";
import { ReportView } from "@/components/ReportView";

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
    <main style={{ maxWidth: 900, margin: "0 auto", padding: 24 }}>
      <h1>marketing-agent</h1>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 16 }}>
        <label>회차: <input value={cycleId} onChange={(e) => setCycleId(e.target.value)} /></label>
        <button onClick={handleLoadExisting}>불러오기</button>
        <button onClick={handleRun} disabled={busy}>{busy ? "실행 중..." : "파이프라인 실행"}</button>
      </div>

      <UploadForm cycleId={cycleId} onUploaded={() => {}} />

      {error && <p style={{ color: "#f66" }}>{error}</p>}
      {report && <div style={{ marginTop: 24 }}><ReportView report={report} /></div>}
    </main>
  );
}
