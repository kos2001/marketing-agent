import { useQuery } from "@tanstack/react-query";
import { getReport } from "@/lib/api";
import { useCycle } from "@/lib/cycle-context";

// 페이지(현황진단/전략·타임라인/Action Items/대시보드)가 공유하는 리포트 조회.
// TanStack Query가 같은 queryKey를 캐시하므로, 사이드바로 페이지를 옮겨도
// 같은 회차라면 다시 fetch하지 않는다.
export function useReport() {
  const { cycleId } = useCycle();
  return useQuery({
    queryKey: ["report", cycleId],
    queryFn: () => getReport(cycleId),
  });
}
