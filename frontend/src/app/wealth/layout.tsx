"use client";

import { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Wallet, PieChart, Coins, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

const TAB_CONFIG = [
  {
    name: "Executive Home",
    href: "/wealth",
    icon: LayoutDashboard,
    color: "#4ecf98",
    activeBg: "rgba(78,207,152,0.1)",
    activeBorder: "rgba(78,207,152,0.2)",
  },
  {
    name: "Patrimônio",
    href: "/wealth/patrimonio",
    icon: Wallet,
    color: "#7EB8F7",
    activeBg: "rgba(126,184,247,0.1)",
    activeBorder: "rgba(126,184,247,0.2)",
  },
  {
    name: "Alocação",
    href: "/wealth/allocation",
    icon: PieChart,
    color: "#e97070",
    activeBg: "rgba(233,112,112,0.1)",
    activeBorder: "rgba(233,112,112,0.2)",
  },
  {
    name: "Dividendos",
    href: "/wealth/dividends",
    icon: Coins,
    color: "#f5a623",
    activeBg: "rgba(245,166,35,0.1)",
    activeBorder: "rgba(245,166,35,0.2)",
  },
  {
    name: "Evolução",
    href: "/wealth/evolution",
    icon: TrendingUp,
    color: "#7F77DD",
    activeBg: "rgba(127,119,221,0.1)",
    activeBorder: "rgba(127,119,221,0.2)",
  },
];

export default function WealthLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex flex-col min-h-screen bg-[#0f0f0f] text-white">
      {/* Top Navigation */}
      <div
        className="sticky top-0 z-10 px-6 py-3"
        style={{
          background: "rgba(14,14,14,0.95)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid rgba(255,255,255,0.04)",
        }}
      >
        <div className="flex items-center gap-1 max-w-7xl mx-auto overflow-x-auto">
          {TAB_CONFIG.map((tab) => {
            const isActive = pathname === tab.href;
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 whitespace-nowrap flex-shrink-0"
                style={
                  isActive
                    ? {
                        background: tab.activeBg,
                        border: `1px solid ${tab.activeBorder}`,
                        color: tab.color,
                      }
                    : {
                        background: "transparent",
                        border: "1px solid transparent",
                        color: "#6b7280",
                      }
                }
              >
                {isActive && (
                  <span
                    className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: tab.color, boxShadow: `0 0 6px ${tab.color}` }}
                  />
                )}
                <tab.icon size={14} />
                <span>{tab.name}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6">
        <div className="max-w-7xl mx-auto">{children}</div>
      </div>
    </div>
  );
}
