"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import { GovernanceClassificationsTab } from "@/components/governance/GovernanceClassificationsTab";

/**
 * /governance/classify — Pierre Finance
 *
 * Classificacao manual de transacoes importadas via Open Finance Pierre.
 * Responsabilidade: decidir ENTRADA / SAIDA / IGNORAR para cada transacao PENDING.
 *
 * Separado de /governance/data (MyProfit) — futuras fontes de dados externas.
 */
export default function GovernanceClassifyPage() {
  return (
    <PageLayout title="Pierre Finance" hideTitle={true}>
      <GovernanceClassificationsTab />
    </PageLayout>
  );
}
