"use client";

import React from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { CategoriesTab } from "@/components/governance/CategoriesTab";

import { DataNav } from "@/components/governance/DataNav";

export default function GovernanceCategoriesPage() {
  return (
    <PageLayout title="Dados - Categorias" hideTitle={true}>
      <DataNav />
      <CategoriesTab />
    </PageLayout>
  );
}
