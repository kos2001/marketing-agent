"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useCycle } from "@/lib/cycle-context";
import { Button } from "@/components/ui";

// 모든 리포트 페이지 상단에 공통으로 쓰는 회차 선택기 — 값을 바꾸면
// CycleProvider의 cycleId가 바뀌고, 그 회차를 쓰는 모든 페이지의
// useReport()가 자동으로 새 쿼리를 낸다(같은 회차면 캐시를 재사용한다).
export function CyclePicker() {
  const { cycleId, setCycleId } = useCycle();
  const [draft, setDraft] = useState(cycleId);
  const queryClient = useQueryClient();

  function apply() {
    setCycleId(draft);
  }

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ["report", cycleId] });
  }

  return (
    <div className="mb-6 flex flex-wrap items-center gap-3">
      <label className="flex items-center gap-2 text-sm text-zinc-300">
        회차
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && apply()}
          className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-1.5 text-sm text-zinc-100 outline-none focus:border-sky-500"
        />
      </label>
      <Button variant="secondary" size="sm" onClick={apply}>
        이 회차 보기
      </Button>
      <Button variant="ghost" size="sm" onClick={refresh}>
        새로고침
      </Button>
    </div>
  );
}
