"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Database, LineChart, Tag, PieChart } from "lucide-react";

export function DataNav() {
  const pathname = usePathname();

  const tabs = [
    { name: "Posições", href: "/governance/data/positions", icon: PieChart },
    { name: "Proventos", href: "/governance/data/dividends", icon: LineChart },
    { name: "Categorias", href: "/governance/data/categories", icon: Tag },
  ];

  return (
    <div className="mb-6 flex space-x-4 border-b border-white/10 pb-4">
      {tabs.map((tab) => {
        const isActive = pathname === tab.href;
        return (
          <Link
            key={tab.name}
            href={tab.href}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              isActive
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : "text-zinc-400 hover:bg-white/5 hover:text-white"
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.name}
          </Link>
        );
      })}
    </div>
  );
}
