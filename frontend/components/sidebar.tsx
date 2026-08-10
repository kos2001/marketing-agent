"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

const nav: { href: string; label: string; icon: string }[] = [
  { href: "/", label: "대시보드", icon: "◧" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [pathname]);

  return (
    <>
      <div className="fixed inset-x-0 top-0 z-30 flex items-center gap-3 border-b border-zinc-800 bg-zinc-950 px-4 py-3 md:hidden">
        <button
          onClick={() => setOpen(true)}
          aria-label="메뉴 열기"
          className="rounded-md border border-zinc-700 px-2.5 py-1.5 text-zinc-300 hover:bg-zinc-800"
        >
          ☰
        </button>
        <span className="text-sm font-semibold text-zinc-100">marketing-agent</span>
      </div>
      {open && (
        <div onClick={() => setOpen(false)} className="fixed inset-0 z-30 bg-black/50 md:hidden" aria-hidden />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-60 shrink-0 flex-col overflow-y-auto border-r border-zinc-800 bg-zinc-950 transition-transform md:static md:z-auto md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="px-5 py-6">
          <p className="text-lg font-semibold tracking-tight text-zinc-50">marketing-agent</p>
          <p className="mt-1 text-xs text-zinc-500">영업/마케팅 Multi-Agent 진단 하네스</p>
        </div>

        <nav className="flex flex-col gap-1 px-3">
          {nav.map((item) => {
            const active = pathname === item.href;
            return (
              <a
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  active ? "bg-zinc-800 font-medium text-zinc-50" : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
                }`}
              >
                <span className="w-4 text-center text-zinc-500">{item.icon}</span>
                {item.label}
              </a>
            );
          })}
        </nav>

        <div className="mt-auto space-y-3 px-4 py-4">
          <p className="rounded-md border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-[11px] leading-relaxed text-zinc-500">
            D1~D3 병렬 진단 + V/V2 독립 교차검증 — 확정 항목만 신뢰, 확인 필요 항목은
            직접 검토가 필요합니다.
          </p>
        </div>
      </aside>
    </>
  );
}
