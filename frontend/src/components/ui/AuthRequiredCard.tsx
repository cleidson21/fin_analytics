import { ShieldAlert } from "lucide-react";
import Link from "next/link";
import { PageLayout } from "@/components/layout/PageLayout";

export function AuthRequiredCard({ title = "Área Restrita" }: { title?: string }) {
  return (
    <PageLayout title={title} hideTitle={true}>
      <div className="flex flex-col items-center justify-center py-20">
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center max-w-md w-full">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-500/20 mb-4">
            <ShieldAlert className="h-6 w-6 text-red-400" />
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">Área administrativa protegida</h2>
          <p className="text-sm text-zinc-400 mb-6">
            Autenticação necessária. Você precisa fazer login para acessar este recurso.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500"
          >
            Ir para Login
          </Link>
        </div>
      </div>
    </PageLayout>
  );
}
