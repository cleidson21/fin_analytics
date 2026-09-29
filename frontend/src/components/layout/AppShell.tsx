"use client";

import type { ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { SECONDARY_NAV, SIDEBAR_NAV } from "@/config/navigation";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";
  const isFinancialDomain =
    pathname === "/" ||
    pathname.startsWith("/transactions") ||
    pathname.startsWith("/categories") ||
    pathname.startsWith("/installments");

  if (isLoginPage) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      <div className="flex min-h-screen">
        <aside className="hidden w-72 shrink-0 flex-col border-r border-white/10 bg-white/5 px-6 py-8 backdrop-blur lg:flex">
          <Link href="/" className="mb-10 inline-flex items-center gap-3 self-start group">
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
              <span className="text-lg font-bold tracking-tight text-white">FinAnalytics</span>
              <span className="text-[11px] font-semibold tracking-widest text-emerald-400/70 uppercase">Finance OS</span>
            </div>
          </Link>


          <nav className="flex flex-1 flex-col gap-8">
            <div>
              <p className="mb-3 text-xs uppercase tracking-[0.24em] text-zinc-500">Plataforma</p>
              <div className="space-y-1">
                {SIDEBAR_NAV.map((item) => {
                  const isActive =
                    item.href === "/"
                      ? isFinancialDomain
                      : item.href.startsWith("/governance")
                        ? pathname.startsWith("/governance")
                      : item.href.startsWith("/wealth-intelligence")
                        ? pathname.startsWith("/wealth-intelligence") || pathname.startsWith("/goals")
                      : item.href === "/wealth"
                        ? pathname === "/wealth" || pathname.startsWith("/wealth/")
                      : pathname === item.href || pathname.startsWith(item.href);

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-colors",
                        isActive
                          ? "bg-emerald-400/10 text-emerald-300 ring-1 ring-inset ring-emerald-400/20"
                          : "text-zinc-300 hover:bg-white/5 hover:text-white"
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
              <p className="mb-3 text-xs uppercase tracking-[0.24em] text-zinc-500">Acesso rápido</p>
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
                        "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-colors",
                        isActive
                          ? "bg-white/10 text-white ring-1 ring-inset ring-white/15"
                          : "text-zinc-300 hover:bg-white/5 hover:text-white"
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
