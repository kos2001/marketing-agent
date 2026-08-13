"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

// 백엔드가 저장소가 비어 있을 때 채워 넣는 데모 회차(app/demo_fixture.py).
export const DEFAULT_CYCLE_ID = "demo-2026-W30";

interface CycleContextValue {
  cycleId: string;
  setCycleId: (id: string) => void;
}

const CycleContext = createContext<CycleContextValue | null>(null);

// 페이지(대시보드/현황진단/전략·타임라인/Action Items/수집 자료)가 모두 같은
// 회차를 보도록 공유하는 컨텍스트 — mi-report식 다중 페이지 구조에서
// 사이드바로 페이지를 옮겨 다녀도 "지금 보고 있는 회차"가 유지되어야 한다.
export function CycleProvider({ children }: { children: ReactNode }) {
  const [cycleId, setCycleId] = useState(DEFAULT_CYCLE_ID);
  return <CycleContext.Provider value={{ cycleId, setCycleId }}>{children}</CycleContext.Provider>;
}

export function useCycle(): CycleContextValue {
  const ctx = useContext(CycleContext);
  if (!ctx) throw new Error("useCycle must be used within a CycleProvider");
  return ctx;
}
