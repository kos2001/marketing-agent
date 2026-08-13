import { Card, PageHeader, SectionTitle } from "@/components/ui";

export default function ManualPage() {
  return (
    <>
      <PageHeader title="사용 안내" description="marketing-agent를 쓰는 순서." />
      <div className="flex flex-col gap-4">
        <Card>
          <SectionTitle>1. 자료 추가</SectionTitle>
          <p className="text-sm leading-relaxed text-zinc-300">
            <strong>수집 자료</strong> 페이지에서 회차(예: 2026-W33)를 정하고, 영업/마케팅
            자료를 소스 종류(이메일 캠페인·소셜미디어·CRM·애널리틱스·고객 피드백/VoC·뉴스·
            업로드 문서·직접 입력)와 함께 텍스트로 붙여넣거나 문서(txt/md/pdf/docx)로
            업로드합니다. 같은 회차에 여러 자료를 올릴수록 진단이 다양한 채널을 아우르게
            됩니다.
          </p>
        </Card>
        <Card>
          <SectionTitle>2. 파이프라인 실행</SectionTitle>
          <p className="text-sm leading-relaxed text-zinc-300">
            대시보드에서 "파이프라인 실행"을 누르면 10개 에이전트(현황진단·기회리스크·
            Critical Point·독립 교차검증·타임라인·종합·전략·Action Items·총평 사실검증)가
            원문만 근거로 돌아갑니다. 자료 양에 따라 수 분이 걸릴 수 있습니다.
          </p>
        </Card>
        <Card>
          <SectionTitle>3. 결과 확인</SectionTitle>
          <p className="text-sm leading-relaxed text-zinc-300">
            왼쪽 사이드바에서 <strong>현황진단</strong>(Executive Summary·지표 대시보드·
            고객별 대응 전략·법인 대응 Process), <strong>전략/타임라인</strong>(전략의
            3축·사안별 전략 가이드·권장 타임라인), <strong>Action Items</strong>(즉시
            확인·조치 필요·최종 요약)을 각각 확인합니다.
          </p>
        </Card>
        <Card>
          <SectionTitle>4. 근거 확인하는 법</SectionTitle>
          <p className="text-sm leading-relaxed text-zinc-300">
            대부분의 항목에는 원문에서 그대로 가져온 인용이 붙습니다. &quot;확정&quot;은
            독립 재도출로 재확인된 항목, &quot;확인 필요&quot;는 한쪽에서만 찾은 항목입니다.
            법인 대응 Process, 권장 타임라인처럼 절차 제안 성격의 항목은 인용을 요구하지
            않습니다.
          </p>
        </Card>
        <Card>
          <SectionTitle>5. 회차를 이어가는 이유</SectionTitle>
          <p className="text-sm leading-relaxed text-zinc-300">
            매 회차 같은 이슈가 반복되면 &quot;N회차째 반복&quot;으로 표시됩니다. 이 신호는
            권장 타임라인에서 더 이른 시점에 배치되는 데 쓰입니다 — <strong>회차
            히스토리</strong> 페이지에서 과거 회차를 다시 열어볼 수 있습니다.
          </p>
        </Card>
      </div>
    </>
  );
}
