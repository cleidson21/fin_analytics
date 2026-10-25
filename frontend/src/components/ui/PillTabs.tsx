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
  activeColor = "var(--financial-positive)",
  activeBg = "color-mix(in oklab, var(--financial-positive) 12%, transparent)",
  className,
}: PillTabsProps) {
  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={cn(
              "px-4 py-1.5 rounded-full text-xs font-semibold transition-colors",
              isActive ? "" : "border border-transparent text-muted-foreground hover:bg-muted/40 hover:text-foreground"
            )}
            style={{
              backgroundColor: isActive ? activeBg : "transparent",
              color: isActive ? activeColor : undefined,
              borderColor: isActive ? `color-mix(in oklab, ${activeColor} 35%, transparent)` : undefined,
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
