import "./globals.css";
import type { ReactNode } from "react";
import { AppShell } from "@/components/app-shell";

export const metadata = { title: "marketing-agent" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body className="flex min-h-screen">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
