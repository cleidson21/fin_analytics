export interface CategoryAccent {
  color: string;
  name: string;
}

const CATEGORY_ACCENTS: readonly CategoryAccent[] = [
  { name: "cyan", color: "#67cbd8" },
  { name: "blue", color: "#6f9fd8" },
  { name: "indigo", color: "#858bd4" },
  { name: "violet", color: "#a184c7" },
  { name: "teal", color: "#63b9aa" },
  { name: "amber", color: "#c9a45f" },
  { name: "orange", color: "#c88963" },
  { name: "emerald", color: "#67b68d" },
  { name: "rose", color: "#c77c8c" },
  { name: "slate-blue", color: "#8193ad" },
];

export function getCategoryAccent(category: string): CategoryAccent {
  let hash = 2166136261;
  for (const character of category) {
    hash ^= character.codePointAt(0) ?? 0;
    hash = Math.imul(hash, 16777619);
  }
  return CATEGORY_ACCENTS[(hash >>> 0) % CATEGORY_ACCENTS.length];
}

export const healthMetricAccents = {
  income: {
    border: "border-t-emerald-400/50",
    icon: "border-emerald-400/15 bg-emerald-400/[0.07] text-success-foreground",
  },
  expense: {
    border: "border-t-rose-400/50",
    icon: "border-rose-400/15 bg-rose-400/[0.07] text-destructive",
  },
  net: {
    border: "border-t-sky-400/50",
    icon: "border-sky-400/15 bg-sky-400/[0.07] text-sky-700 dark:text-sky-300",
  },
  savings: {
    border: "border-t-violet-400/50",
    icon: "border-violet-400/15 bg-violet-400/[0.07] text-violet-700 dark:text-violet-300",
  },
} as const;
