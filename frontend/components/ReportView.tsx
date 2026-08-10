import type { CycleReport } from "@/lib/api";

export function ReportView({ report }: { report: CycleReport }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <section>
        <h2>총평</h2>
        <p>{report.overview}</p>
        {report.overview_warnings.length > 0 && (
          <ul style={{ color: "#f0b429" }}>
            {report.overview_warnings.map((w, i) => <li key={i}>근거 미확인: {w}</li>)}
          </ul>
        )}
        <p style={{ opacity: 0.7 }}>{report.coverage_note}</p>
      </section>

      <section>
        <h2>현황진단</h2>
        <ul>
          {report.diagnosis.map((d) => (
            <li key={d.id}>
              [{d.channel}] {d.summary} — {d.kind === "strength" ? "강점" : "약점"}
              {" "}<span style={{ opacity: 0.7 }}>({statusLabel(d.status)})</span>
              {d.citations.length > 0 && (
                <ul>{d.citations.map((c, i) => <li key={i} style={{ opacity: 0.7 }}>&quot;{c.quote}&quot;</li>)}</ul>
              )}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>기회 / 리스크</h2>
        <ul>
          {report.opportunities_risks.map((o) => (
            <li key={o.id}>
              [{o.kind === "opportunity" ? "기회" : "리스크"}] {o.title} — {o.rationale}
              {o.additionally_flagged && <span> (추가 지적 항목)</span>}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Critical Point</h2>
        <ul>
          {report.critical_points.map((cp) => (
            <li key={cp.id}>{cp.title} — 임팩트: {cp.impact}, 시급성: {cp.urgency}, 필요 결정: {cp.decision_needed}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2>타임라인</h2>
        <ul>
          {report.timeline.map((t, i) => (
            <li key={i}>{t.item_title} — {t.prior_cycle_id} 회차부터 이어짐 ({t.repeat_count}회차째 반복)</li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Action Items</h2>
        <table>
          <thead><tr><th>항목</th><th>담당</th><th>기한</th><th>우선순위</th></tr></thead>
          <tbody>
            {report.action_items.map((a) => (
              <tr key={a.id}><td>{a.title}</td><td>{a.owner}</td><td>{a.due}</td><td>{a.priority}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function statusLabel(status: string): string {
  if (status === "confirmed") return "확정";
  if (status === "unfounded") return "근거 미확인";
  return "확인 필요";
}
