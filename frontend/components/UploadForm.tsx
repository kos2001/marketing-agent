"use client";
import { useState } from "react";
import { addSource, SOURCE_TYPE_LABEL, type SourceType } from "@/lib/api";
import { Button, Card, ErrorNote, SectionTitle } from "@/components/ui";

const SOURCE_TYPES = Object.keys(SOURCE_TYPE_LABEL) as SourceType[];

export function UploadForm({ cycleId, onUploaded }: { cycleId: string; onUploaded: () => void }) {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [sourceType, setSourceType] = useState<SourceType>("manual");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!title.trim() || !text.trim()) {
      setError("제목과 본문을 입력하세요.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await addSource(cycleId, title, text, sourceType);
      setTitle("");
      setText("");
      onUploaded();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <SectionTitle>자료 추가</SectionTitle>
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap gap-3">
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value as SourceType)}
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-sky-500"
          >
            {SOURCE_TYPES.map((t) => (
              <option key={t} value={t}>
                {SOURCE_TYPE_LABEL[t]}
              </option>
            ))}
          </select>
          <input
            placeholder="자료 제목 (예: 8월 이메일 캠페인)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="min-w-[200px] flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-sky-500"
          />
        </div>
        <textarea
          placeholder="본문 붙여넣기"
          rows={6}
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-sky-500"
        />
        {error && <ErrorNote message={error} />}
        <div>
          <Button onClick={submit} disabled={busy}>
            {busy ? "업로드 중..." : "자료 추가"}
          </Button>
        </div>
      </div>
    </Card>
  );
}
