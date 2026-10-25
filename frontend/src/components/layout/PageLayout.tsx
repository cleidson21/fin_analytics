import { Suspense, type ReactNode } from "react";

import { TopNav } from "@/components/layout/TopNav";

export function PageLayout({
  title,
  subtitle,
  hideTitle,
  breadcrumb,
  children,
}: {
  title?: string;
  subtitle?: string;
  hideTitle?: boolean;
  breadcrumb?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <Suspense fallback={<div aria-hidden="true" className="h-[68px]" />}>
        <TopNav />
      </Suspense>

      <section className={`mx-auto flex w-full max-w-7xl flex-1 flex-col gap-10 px-6 sm:px-10 lg:px-12 ${hideTitle ? "pt-6 pb-10" : "py-10"}`}>
        {!hideTitle && (
          <header className="space-y-2">
            {breadcrumb && <div className="mb-4">{breadcrumb}</div>}
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h1>
            {subtitle ? <p className="text-sm text-muted-foreground">{subtitle}</p> : null}
          </header>
        )}

        <div className="space-y-6">{children}</div>
      </section>
    </div>
  );
}
