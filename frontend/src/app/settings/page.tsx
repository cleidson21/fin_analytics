"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <PageLayout title="Configurações Gerais">
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/[0.03] text-zinc-500 ring-1 ring-inset ring-white/10">
          <Settings className="w-8 h-8" />
        </div>
        <div className="text-center">
          <h2 className="text-lg font-medium text-zinc-100">Configurações Gerais</h2>
          <p className="text-sm text-zinc-500 mt-1 max-w-sm mx-auto">
            Esta seção será implementada em breve. Use as abas no menu superior para gerenciar suas Contas.
          </p>
        </div>
      </div>
    </PageLayout>
  );
}
