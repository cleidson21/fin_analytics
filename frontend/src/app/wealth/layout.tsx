import { ReactNode } from "react";
import { PageLayout } from "@/components/layout/PageLayout";

export default function WealthLayout({ children }: { children: ReactNode }) {
  return (
    <PageLayout title="Investimentos" hideTitle={true}>
      {children}
    </PageLayout>
  );
}
