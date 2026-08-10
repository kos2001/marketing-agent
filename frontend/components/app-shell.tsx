"use client";

import type { ReactNode } from "react";
import { Sidebar } from "@/components/sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:border focus:border-zinc-600 focus:bg-zinc-900 focus:px-3 focus:py-2 focus:text-sm focus:text-zinc-100"
      >
        본문으로 건너뛰기
      </a>
      <Sidebar />
      <main id="main" className="min-w-0 flex-1 overflow-y-auto px-4 pb-8 pt-16 sm:px-8 md:pt-8">
        <div className="mx-auto max-w-5xl">{children}</div>
      </main>
    </>
  );
}
