"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { search, getSearchStatus, SOURCE_TYPE_LABEL } from "@/lib/api";
import { useCycle } from "@/lib/cycle-context";
import { Button, Card, EmptyState, ErrorNote, PageHeader, SectionTitle, Tag } from "@/components/ui";

export default function SearchPage() {
  const { cycleId } = useCycle();
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");
  const [scopeToCycle, setScopeToCycle] = useState(false);

  const statusQuery = useQuery({ queryKey: ["search-status"], queryFn: getSearchStatus });
  const resultsQuery = useQuery({
    queryKey: ["search", query, scopeToCycle ? cycleId : null],
    queryFn: () => search(query, scopeToCycle ? cycleId : undefined),
    enabled: query.length > 0,
  });

  function runSearch() {
    setQuery(input.trim());
  }

  return (
    <>
      <PageHeader
        title="검색"
        description="모든 회차의 수집 자료를 BM25 어휘 검색으로 찾습니다 (전문 색인은 SQLite FTS5)."
      />

      {statusQuery.data && (
        <p className="mb-4 text-xs text-zinc-500">
          {statusQuery.data.embeddings_available
            ? "의미 임베딩 검색이 함께 켜져 있습니다 (BM25 + 벡터 하이브리드, RRF 결합)."
            : "현재는 BM25 어휘 검색만 동작합니다 — 의미 임베딩은 MA_EMBEDDINGS=1로 켤 수 있습니다."}
        </p>
      )}

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runSearch()}
          placeholder="예: 오픈율 하락, ACME, 구독 해지"
          className="min-w-[240px] flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-sky-500"
        />
        <Button size="sm" onClick={runSearch}>
          검색
        </Button>
        <label className="flex items-center gap-2 text-xs text-zinc-400">
          <input type="checkbox" checked={scopeToCycle} onChange={(e) => setScopeToCycle(e.target.checked)} />
          현재 회차({cycleId})로 제한
        </label>
      </div>

      {resultsQuery.error && <ErrorNote message={String(resultsQuery.error)} />}
      {query && !resultsQuery.isLoading && resultsQuery.data?.length === 0 && (
        <EmptyState message={`"${query}"에 대한 결과가 없습니다.`} />
      )}

      <div className="flex flex-col gap-3">
        {resultsQuery.data?.map((r) => (
          <Card key={r.id}>
            <div className="flex flex-wrap items-center gap-2">
              <SectionTitle>{r.title}</SectionTitle>
              <Tag>{SOURCE_TYPE_LABEL[r.source_type]}</Tag>
              <Link href="/sources" className="text-xs text-sky-400 hover:underline">
                {r.cycle_id} 회차
              </Link>
            </div>
            <p className="text-sm leading-relaxed text-zinc-400">{r.snippet}</p>
          </Card>
        ))}
      </div>
    </>
  );
}
