import React from "react";
import { cn } from "@/lib/utils";

export interface PillTabItem {
  id: string;
  label: string;
}

interface PillTabsProps {
  tabs: PillTabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  activeColor?: string;
  activeBg?: string;
  className?: string;
}

export function PillTabs({
  tabs,
  activeTab,
  onChange,
  activeColor = "#4ecf98",
  activeBg = "rgba(78,207,152,0.12)",
  className,
}: PillTabsProps) {
  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={cn(
              "px-4 py-1.5 rounded-full text-xs font-semibold transition-colors",
              isActive ? "" : "text-neutral-500 hover:text-neutral-300 hover:bg-white/5 border border-transparent"
            )}
            style={{
              backgroundColor: isActive ? activeBg : "transparent",
              color: isActive ? activeColor : undefined,
              borderColor: isActive ? activeColor.replace("1)", "0.3)") : undefined, // fallback if hex
              borderWidth: isActive ? 1 : 1,
              borderStyle: "solid",
            }}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
