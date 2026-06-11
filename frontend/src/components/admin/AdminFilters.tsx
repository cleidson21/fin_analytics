import React from "react";

interface AdminFiltersProps {
  children: React.ReactNode;
}

export function AdminFilters({ children }: AdminFiltersProps) {
  return (
    <div className="flex flex-col gap-4 rounded-md border border-slate-800 bg-slate-900/50 p-4 mb-6 md:flex-row md:items-center md:justify-between">
      {children}
    </div>
  );
}
