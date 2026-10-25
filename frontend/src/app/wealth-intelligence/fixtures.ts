import type { WealthHomeFixture } from "./types";

export const SYNTHETIC_WEALTH_HOME_FIXTURE: WealthHomeFixture = {
  fixtureId: "wealth-home-demo-v1",
  referencePeriod: "Setembro de 2026",
  scopeLabel: "Cenário sintético em BRL · nenhuma conta pessoal conectada",
  metrics: [
    {
      id: "monthly-balance",
      label: "Saldo mensal",
      value: "R$ 3.420,00",
      context: "Receitas menos despesas no período demonstrado",
      source: "Contrato Financial Health · fixture",
      tone: "emerald",
    },
    {
      id: "investment-wealth",
      label: "Carteira de investimentos",
      value: "R$ 842.450,00",
      context: "Patrimônio de investimentos — não é patrimônio líquido total",
      source: "Snapshot MyProfit · fixture",
      tone: "sky",
    },
    {
      id: "active-goals",
      label: "Metas ativas",
      value: "3",
      context: "Duas no ritmo esperado e uma pedindo atenção",
      source: "Contrato Goals · fixture",
      tone: "violet",
    },
    {
      id: "fire-gap",
      label: "Distância para a meta FIRE",
      value: "R$ 657.550,00",
      context: "Resultado de um cenário determinístico demonstrativo",
      source: "Contrato FIRE · fixture",
      tone: "amber",
    },
  ],
  investmentWealthHistory: [
    { period: "Abr", value: "R$ 758.300", visualHeight: "54%" },
    { period: "Mai", value: "R$ 773.100", visualHeight: "62%" },
    { period: "Jun", value: "R$ 789.600", visualHeight: "69%" },
    { period: "Jul", value: "R$ 806.900", visualHeight: "77%" },
    { period: "Ago", value: "R$ 823.700", visualHeight: "86%" },
    { period: "Set", value: "R$ 842.450", visualHeight: "96%" },
  ],
  allocation: [
    {
      label: "Renda variável Brasil",
      value: "R$ 353.829,00",
      share: "42%",
      visualWidth: "42%",
      color: "#4ecf98",
    },
    {
      label: "Renda fixa",
      value: "R$ 269.584,00",
      share: "32%",
      visualWidth: "32%",
      color: "#7eb8f7",
    },
    {
      label: "Fundos imobiliários",
      value: "R$ 143.217,00",
      share: "17%",
      visualWidth: "17%",
      color: "#c4b5fd",
    },
    {
      label: "Caixa de investimentos",
      value: "R$ 75.820,00",
      share: "9%",
      visualWidth: "9%",
      color: "#f5a623",
    },
  ],
  advisor: {
    question: "O que merece minha atenção neste mês?",
    context: [
      {
        label: "Saúde financeira",
        value: "Saldo mensal positivo no cenário",
        provenance: "Financial Health · set/2026 · sintético",
      },
      {
        label: "Metas",
        value: "1 de 3 metas sinalizada para revisão",
        provenance: "Goals · set/2026 · sintético",
      },
      {
        label: "Carteira",
        value: "Concentração demonstrativa de 42% na maior classe",
        provenance: "MyProfit · set/2026 · sintético",
      },
    ],
    sources: [
      "Financial Health / cashflow",
      "Goals / lifecycle",
      "Investment portfolio snapshot",
    ],
    response:
      "Demonstração: o saldo mensal está positivo, mas uma meta e a concentração da maior classe merecem revisão. Esta frase é uma fixture de interface; não foi gerada nem validada por um modelo.",
    limitations: [
      "Inferência local desativada",
      "Sem execução de ferramentas",
      "Sem acesso a dados pessoais ou produção",
      "Validação factual não executada",
    ],
  },
};
