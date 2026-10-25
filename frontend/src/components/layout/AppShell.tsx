"use client";

import type { ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { isSidebarNavigationActive, SECONDARY_NAV, SIDEBAR_NAV } from "@/config/navigation";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";

  if (isLoginPage) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="flex min-h-screen">
        <aside className="hidden w-72 shrink-0 flex-col border-r border-sidebar-border bg-sidebar px-6 py-8 text-sidebar-foreground lg:flex">
          <Link href="/" className="group mb-10 inline-flex items-center gap-3 self-start rounded-xl focus-visible:ring-2 focus-visible:ring-ring">
            {/* Logo FA — FinAnalytics */}
            <Image
              src="/logo.jpg"
              alt="FinAnalytics logo"
              width={48}
              height={48}
              priority
              className="shrink-0 rounded-xl transition-transform group-hover:scale-105"
            />
            <div className="flex flex-col leading-tight">
              <span className="text-lg font-bold tracking-tight text-foreground">FinAnalytics</span>
              <span className="text-[11px] font-semibold uppercase tracking-widest text-emerald-700 dark:text-emerald-400">Finance OS</span>
            </div>
          </Link>


          <nav className="flex flex-1 flex-col gap-8">
            <div>
              <p className="mb-3 text-xs uppercase tracking-[0.24em] text-muted-foreground">Plataforma</p>
              <div className="space-y-1">
                {SIDEBAR_NAV.map((item) => {
                  const isActive = isSidebarNavigationActive(pathname, item.href);

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-ring",
                        isActive
                          ? "bg-emerald-500/10 text-emerald-700 ring-1 ring-inset ring-emerald-500/25 dark:text-emerald-300"
                          : "text-sidebar-foreground/75 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                      )}
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            </div>

            <div>
              <p className="mb-3 text-xs uppercase tracking-[0.24em] text-muted-foreground">Acesso rápido</p>
              <div className="space-y-1">
                {SECONDARY_NAV.map((item) => {
                  const isActive = 
                    item.href === "/settings" 
                      ? pathname.startsWith("/settings") || pathname.startsWith("/accounts") || pathname.startsWith("/profile")
                      : pathname === item.href;

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-ring",
                        isActive
                          ? "bg-sidebar-accent text-sidebar-accent-foreground ring-1 ring-inset ring-sidebar-border"
                          : "text-sidebar-foreground/75 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                      )}
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          </nav>
        </aside>

        <main className="flex min-w-0 flex-1 flex-col overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
