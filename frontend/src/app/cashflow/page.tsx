"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * /cashflow foi integrado em Controle Financeiro / Transacoes.
 * Este redirect garante que bookmarks antigos continuem funcionando.
 */
export default function CashflowRedirectPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/transactions");
  }, [router]);

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "60vh", color: "#64748b", fontSize: "14px" }}>
      Redirecionando...
    </div>
  );
}
