"use client";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { listCycles } from "@/lib/api";
import { useCycle } from "@/lib/cycle-context";
import { Button, EmptyState, ErrorNote, PageHeader, TableCard, Td, Th } from "@/components/ui";

export default function HistoryPage() {
  const router = useRouter();
  const { cycleId, setCycleId } = useCycle();
  const cyclesQuery = useQuery({ queryKey: ["cycles"], queryFn: listCycles });

  function openCycle(id: string) {
    setCycleId(id);
    router.push("/diagnosis");
  }

  return (
    <>
      <PageHeader title="회차 히스토리" description="지금까지 생성된 모든 리포트 회차." />

      {cyclesQuery.error && <ErrorNote message={String(cyclesQuery.error)} />}
      {!cyclesQuery.isLoading && cyclesQuery.data?.length === 0 && (
        <EmptyState message="아직 생성된 리포트가 없습니다." />
      )}
      {cyclesQuery.data && cyclesQuery.data.length > 0 && (
        <TableCard>
          <thead>
            <tr className="border-b border-zinc-800">
              <Th>회차</Th>
              <Th>현재 선택</Th>
              <Th />
            </tr>
          </thead>
          <tbody>
            {cyclesQuery.data.map((id) => (
              <tr key={id} className="border-b border-zinc-800 last:border-0">
                <Td>{id}</Td>
                <Td>{id === cycleId ? "✓" : ""}</Td>
                <Td>
                  <Button variant="secondary" size="sm" onClick={() => openCycle(id)}>
                    현황진단 보기
                  </Button>
                </Td>
              </tr>
            ))}
          </tbody>
        </TableCard>
      )}
    </>
  );
}
