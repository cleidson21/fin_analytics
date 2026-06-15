# REBUILD PIPELINE - FASE 10.2

Cronograma e esteira de entregas (Pipeline) projetado para a reengenharia do Fin Analytics V2, pautado em camadas de infraestrutura.

---

## FASE 1: Architecture Review
* **Foco:** Validação de todos os artefatos de auditoria congelados na Fase 10.
* **Ações:** 
  1. Revisão do `SYSTEM_REBUILD_PACKAGE.md` pelo comitê técnico.
  2. Setup inicial do ambiente docker/local.
  3. Confirmação do `API_CONTRACT_FREEZE.md` como imutável (Design-First).

## FASE 2: Database V2
* **Foco:** Persistência pura.
* **Ações:** 
  1. Reescrita das tabelas SQL, chaves primárias e views na branch `database-v2`.
  2. Implementação das travas de cascata rígidas documentadas (Governança e Deleção Segura).
  3. Descarte de tabelas legadas provadas mortas.

## FASE 3: Backend V2
* **Foco:** O coração matemático e lógico (FastAPI/Services).
* **Ações:** 
  1. Construção das rotas Dummy que respeitem os contratos JSON.
  2. Acoplamento de ORM ou Query Raw do DB ao serviço.
  3. Reconstrução do Motor de ETL, Categorizador de IA e Regex de Parcelamentos (conforme documentado no `BUSINESS_RULES.md`).

## FASE 4: Frontend V2
* **Foco:** Restauração Visual e Fluxos.
* **Ações:** 
  1. Refatoração UI (Next.js / App Router).
  2. Limpeza de pacotes obsoletos.
  3. Acoplamento transparente dos Hooks React às novas rotas (sem quebras, graças ao congelamento dos JSONs originais).

## FASE 5: Develop V2 Integration
* **Foco:** Colisão e Teste Cruzado.
* **Ações:** 
  1. Mescla de todas as branches na branch de choque (`develop-v2`).
  2. O Front invoca a API rodando conectada ao novo Banco V2. Testes manuais do fluxo E2E, importação de arquivo Nubank até o painel Dashboard.

## FASE 6: Certification
* **Foco:** Validação Estável Final (Release Candidate).
* **Ações:** 
  1. O comitê de Qualidade (QA) valida os deltas (Ritmo, YOC, Alocação). 
  2. Aprovando, inicia-se o Pull Request de `develop-v2` contra a sagrada `main`. A nova Era V2 inicia.
