"use client";

import { useRef } from "react";
import { Monitor, Moon, Sun, type LucideIcon } from "lucide-react";

import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";
import type { ThemePreference } from "@/lib/theme";

const OPTIONS: Array<{
  value: ThemePreference;
  label: string;
  shortLabel: string;
  icon: LucideIcon;
}> = [
  { value: "system", label: "Usar tema do sistema", shortLabel: "Sistema", icon: Monitor },
  { value: "light", label: "Usar tema claro", shortLabel: "Claro", icon: Sun },
  { value: "dark", label: "Usar tema escuro", shortLabel: "Escuro", icon: Moon },
];

export function ThemeSwitcher({ compact = false }: { compact?: boolean }) {
  const { preference, setPreference } = useTheme();
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);

  function selectByKeyboard(index: number, event: React.KeyboardEvent<HTMLButtonElement>) {
    const lastIndex = OPTIONS.length - 1;
    let nextIndex: number | null = null;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") nextIndex = index === lastIndex ? 0 : index + 1;
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") nextIndex = index === 0 ? lastIndex : index - 1;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = lastIndex;
    if (nextIndex === null) return;

    event.preventDefault();
    setPreference(OPTIONS[nextIndex].value);
    optionRefs.current[nextIndex]?.focus();
  }

  return (
    <div
      role="radiogroup"
      aria-label="Tema da interface"
      className="inline-flex rounded-xl border border-border bg-muted/35 p-1"
    >
      {OPTIONS.map(({ value, label, shortLabel, icon: Icon }, index) => {
        const selected = preference === value;
        return (
          <button
            key={value}
            ref={(node) => { optionRefs.current[index] = node; }}
            type="button"
            role="radio"
            aria-checked={selected}
            tabIndex={selected ? 0 : -1}
            aria-label={label}
            title={label}
            onClick={() => setPreference(value)}
            onKeyDown={(event) => selectByKeyboard(index, event)}
            className={cn(
              "inline-flex min-h-9 items-center justify-center gap-1.5 rounded-lg px-2.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background motion-reduce:transition-none",
              selected
                ? "bg-background text-foreground shadow-sm ring-1 ring-border"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            )}
          >
            <Icon aria-hidden="true" className="size-3.5" />
            {compact ? <span className="sr-only">{shortLabel}</span> : <span>{shortLabel}</span>}
          </button>
        );
      })}
    </div>
  );
}
