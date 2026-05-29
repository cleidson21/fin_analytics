"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { getTabsForPath } from "@/config/navigation";

export function TopNav() {
  const pathname = usePathname();

  const tabs = getTabsForPath(pathname);

  if (!tabs || tabs.length === 0) {
    return null;
  }

  return (
    <div className="border-b border-white/10 bg-zinc-950/80 px-6 py-4 backdrop-blur lg:px-10">
      <nav className="flex items-center gap-2 overflow-x-auto">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href;

          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={cn(
                "relative whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition-colors",
                isActive ? "text-white" : "text-zinc-400 hover:text-zinc-100"
              )}
            >
              {tab.name}
              {isActive && <span className="absolute inset-x-4 -bottom-px h-0.5 rounded-full bg-emerald-400" />}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}