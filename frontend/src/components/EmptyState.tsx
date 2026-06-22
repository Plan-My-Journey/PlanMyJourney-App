import { ReactNode } from "react";

export default function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-zinc-300 bg-white p-6 text-center">
      <p className="text-sm font-semibold text-zinc-900">{title}</p>
      {children && <div className="mt-2 text-sm text-zinc-600">{children}</div>}
    </div>
  );
}
