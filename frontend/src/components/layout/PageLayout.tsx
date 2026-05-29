import type { ReactNode } from "react";

import { TopNav } from "@/components/layout/TopNav";

export function PageLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <TopNav />

      <section className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-10 px-6 py-10 sm:px-10 lg:px-12">
        <header className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h1>
          {subtitle ? <p className="text-sm text-zinc-400">{subtitle}</p> : null}
        </header>

        <div className="space-y-6">{children}</div>
      </section>
    </div>
  );
}
