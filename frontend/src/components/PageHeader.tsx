import { ReactNode } from "react";

export default function PageHeader({
  title,
  description,
  actions
}: {
  readonly title: string;
  readonly description?: string;
  readonly actions?: ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-950">{title}</h1>
        {description && <p className="mt-1 max-w-3xl text-sm text-zinc-600">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
