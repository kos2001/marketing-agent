import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const BUTTON_VARIANTS: Record<ButtonVariant, string> = {
  // 주 액션 (실행·조회) — 흰색 채움
  primary: "bg-zinc-100 text-zinc-900 hover:bg-white",
  // 보조 액션 (불러오기) — 외곽선
  secondary: "border border-zinc-600 text-zinc-200 hover:bg-zinc-800",
  // 약한 액션
  ghost: "text-zinc-300 hover:bg-zinc-800",
  danger: "border border-red-800/60 text-red-300 hover:bg-red-950/40",
};

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: "sm" | "md";
}) {
  const sz = size === "sm" ? "px-3 py-1.5 text-xs" : "px-5 py-2.5 text-sm";
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg font-medium outline-none transition focus-visible:ring-2 focus-visible:ring-sky-500 disabled:opacity-40 ${sz} ${BUTTON_VARIANTS[variant]} ${className}`}
    />
  );
}

export function EmptyState({
  message,
  icon = "◍",
  action,
}: {
  message: string;
  icon?: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 px-6 py-10 text-center">
      <p className="text-2xl text-zinc-600">{icon}</p>
      <p className="mt-2 text-sm text-zinc-500">{message}</p>
      {action && <div className="mt-3 flex justify-center">{action}</div>}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <header className="mb-8 flex items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-50">{title}</h1>
        <p className="mt-1.5 text-sm text-zinc-400">{description}</p>
      </div>
      {action}
    </header>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 ${className}`}>{children}</div>;
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="mb-3 text-sm font-semibold tracking-tight text-zinc-200">{children}</h2>;
}

const statusStyle: Record<string, string> = {
  confirmed: "bg-emerald-950/60 text-emerald-400 border-emerald-900/60",
  needs_review: "bg-amber-950/60 text-amber-400 border-amber-900/60",
  unfounded: "bg-red-950/60 text-red-400 border-red-900/60",
};

const statusLabel: Record<string, string> = {
  confirmed: "확정",
  needs_review: "확인 필요",
  unfounded: "근거 미확인",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${statusStyle[status] ?? statusStyle.needs_review}`}
    >
      {statusLabel[status] ?? status}
    </span>
  );
}

const priorityStyle: Record<string, string> = {
  high: "bg-red-950/60 text-red-400 border-red-900/60",
  mid: "bg-amber-950/60 text-amber-400 border-amber-900/60",
  low: "bg-zinc-800/80 text-zinc-400 border-zinc-700/60",
};

const priorityLabel: Record<string, string> = { high: "상", mid: "중", low: "하" };

export function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${priorityStyle[priority] ?? priorityStyle.low}`}
    >
      우선순위 {priorityLabel[priority] ?? priority}
    </span>
  );
}

export function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-md bg-zinc-800 px-2 py-0.5 text-[11px] text-zinc-400">
      {children}
    </span>
  );
}

export function Th({ children, className = "" }: { children?: ReactNode; className?: string }) {
  return (
    <th className={`px-4 py-2.5 text-left text-[11px] font-medium uppercase tracking-wider text-zinc-500 ${className}`}>
      {children}
    </th>
  );
}

export function Td({
  children,
  className = "",
  colSpan,
}: {
  children?: ReactNode;
  className?: string;
  colSpan?: number;
}) {
  return (
    <td colSpan={colSpan} className={`px-4 py-2.5 align-top text-zinc-300 ${className}`}>
      {children}
    </td>
  );
}

export function TableCard({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/60">
      <table className="w-full text-sm">{children}</table>
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <p className="rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-400">{message}</p>
  );
}
