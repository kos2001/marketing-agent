"use client";
import { useRef, useState } from "react";
import { addSource, uploadSourceFile, SOURCE_TYPE_LABEL, type SourceType } from "@/lib/api";
import { Button, Card, ErrorNote, SectionTitle } from "@/components/ui";

const SOURCE_TYPES = Object.keys(SOURCE_TYPE_LABEL) as SourceType[];
// backend/app/doctext.py의 SUPPORTED_EXTENSIONS와 맞춘다.
const ACCEPTED_EXTENSIONS = ".txt,.md,.pdf,.docx";

type Mode = "paste" | "file";

export function UploadForm({ cycleId, onUploaded }: { cycleId: string; onUploaded: () => void }) {
  const [mode, setMode] = useState<Mode>("paste");
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [sourceType, setSourceType] = useState<SourceType>("manual");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function submitPaste() {
    if (!title.trim() || !text.trim()) {
      setError("제목과 본문을 입력하세요.");
      return;
    }
    setBusy(true);
    setError("");
    setInfo("");
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

  async function submitFile() {
    if (!file) {
      setError("업로드할 문서를 선택하세요.");
      return;
    }
    setBusy(true);
    setError("");
    setInfo("");
    try {
      const result = await uploadSourceFile(cycleId, file, sourceType, title || undefined);
      setInfo(`텍스트 ${result.extracted_chars.toLocaleString()}자를 추출했습니다.`);
      setFile(null);
      setTitle("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      onUploaded();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <SectionTitle>자료 추가</SectionTitle>
        <div className="flex gap-1 rounded-lg border border-zinc-700 p-0.5 text-xs">
          <button
            onClick={() => setMode("paste")}
            className={`rounded-md px-2.5 py-1 ${mode === "paste" ? "bg-zinc-800 text-zinc-50" : "text-zinc-400"}`}
          >
            텍스트 붙여넣기
          </button>
          <button
            onClick={() => setMode("file")}
            className={`rounded-md px-2.5 py-1 ${mode === "file" ? "bg-zinc-800 text-zinc-50" : "text-zinc-400"}`}
          >
            문서 업로드
          </button>
        </div>
      </div>

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
            placeholder={mode === "paste" ? "자료 제목 (예: 8월 이메일 캠페인)" : "제목 (비우면 파일명 사용)"}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="min-w-[200px] flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-sky-500"
          />
        </div>

        {mode === "paste" ? (
          <>
            <textarea
              placeholder="본문 붙여넣기"
              rows={6}
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-sky-500"
            />
            {error && <ErrorNote message={error} />}
            <div>
              <Button onClick={submitPaste} disabled={busy}>
                {busy ? "업로드 중..." : "자료 추가"}
              </Button>
            </div>
          </>
        ) : (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_EXTENSIONS}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 file:mr-3 file:rounded-md file:border-0 file:bg-zinc-800 file:px-3 file:py-1.5 file:text-xs file:text-zinc-200"
            />
            <p className="text-xs text-zinc-500">지원 형식: txt, md, pdf, docx (최대 10MB)</p>
            {info && <p className="text-xs text-emerald-400">{info}</p>}
            {error && <ErrorNote message={error} />}
            <div>
              <Button onClick={submitFile} disabled={busy || !file}>
                {busy ? "업로드 중..." : "문서 업로드"}
              </Button>
            </div>
          </>
        )}
      </div>
    </Card>
  );
}
