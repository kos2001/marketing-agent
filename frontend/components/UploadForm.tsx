"use client";
import { useState } from "react";
import { addSource } from "@/lib/api";
import { Button, Card, ErrorNote, SectionTitle } from "@/components/ui";

export function UploadForm({ cycleId, onUploaded }: { cycleId: string; onUploaded: () => void }) {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
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
      await addSource(cycleId, title, text);
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
        <input
          placeholder="자료 제목 (예: 8월 이메일 캠페인)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-sky-500"
        />
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
