import "./globals.css";
import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import { AppShell } from "@/components/app-shell";
import { QueryProvider } from "@/lib/query-provider";
import { CycleProvider } from "@/lib/cycle-context";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = { title: "marketing-agent" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body className={`${geistSans.variable} ${geistMono.variable} flex min-h-screen`}>
        <QueryProvider>
          <CycleProvider>
            <AppShell>{children}</AppShell>
          </CycleProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
