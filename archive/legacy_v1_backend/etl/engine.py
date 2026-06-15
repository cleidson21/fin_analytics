"""
etl/engine.py — Reconciliation Engine (Sprint 4.5)

Motor avançado de reconciliação cruzada. Substitui o EventReconciler básico.
Utiliza um sistema de Scoring e Bipartite Matching (Greedy Assignment)
para evitar links duplicados e classificar a confiança da ligação.
"""
from __future__ import annotations

import logging
import re
import uuid
from collections import defaultdict
from typing import NamedTuple

from models.core import EventType, RawFinancialEvent
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Palavras-chave herdadas do Reconciler antigo para boost de score
_DIVIDEND_KEYWORDS = re.compile(
    r"(rendimento|dividendo|provento|jscp|jcp|fii|fundo\s+imobil)",
    re.IGNORECASE,
)
_INVOICE_PAYMENT_KEYWORDS = re.compile(
    r"(pagamento\s+nubank|fatura\s+nubank|pg\s+nubank|nubank\s+cartao)",
    re.IGNORECASE,
)
_INVESTMENT_PURCHASE_KEYWORDS = re.compile(
    r"(compra|aplicacao|investimento|transferencia\s+para\s+corretora|rico|xp|clear|rdb)",
    re.IGNORECASE,
)

class EventLink(NamedTuple):
    id: str
    event_id_a: str
    event_id_b: str
    link_type: str
    confidence: float
    match_method: str
    status: str          # AUTO_CONFIRMED | SUGGESTED
    notes: str | None = None


class ReconciliationEngine:
    def __init__(self, hints: list[dict] | None = None):
        self.hints = hints or []

    def reconcile(
        self,
        events: list[RawFinancialEvent],
        existing_links: list[dict] | None = None,
    ) -> list[EventLink]:
        """
        Gera, pontua e resolve conflitos para criar links otimizados.
        """
        existing_pairs = {
            (lk["event_id_a"], lk["event_id_b"])
            for lk in (existing_links or [])
        }

        # 1. Separar eventos por tipo/fonte para otimizar candidate generation
        dividends_myprofit = [
            e for e in events
            if e["event_type"] == EventType.DIVIDEND.value
            and e["source"] == "MYPROFIT"
        ]
        transactions_nubank = [
            e for e in events
            if e["event_type"] == EventType.TRANSACTION.value
            and e["source"] in ("NUBANK_CONTA", "NUBANK", "PIERRE")
        ]
        invoices_nubank = [
            e for e in events
            if e["event_type"] == EventType.INVOICE.value
            and e["source"] == "NUBANK_FATURA"
        ]

        all_links = []

        # -- Caso A: DIVIDEND_CREDIT (1:1) --
        candidates_div = self._generate_candidates_1to1(dividends_myprofit, transactions_nubank, window_days=5)
        scored_div = self._score_dividend_candidates(candidates_div)
        all_links.extend(self._resolve_conflicts(scored_div, "DIVIDEND_CREDIT", existing_pairs))

        # -- Caso B: INVOICE_PAYMENT (N:1) --
        # Faturas são agregadas por mês. Se der match no total, lincamos todos os eventos daquele mês à transação.
        candidates_inv = self._generate_invoice_candidates(invoices_nubank, transactions_nubank, window_days=5)
        scored_inv = self._score_invoice_candidates(candidates_inv)
        all_links.extend(self._resolve_invoice_conflicts(scored_inv, existing_pairs))

        # -- Caso C: INVESTMENT_PURCHASE (1:1) --
        investments_myprofit = [
            e for e in events
            if e["event_type"] == EventType.TRANSACTION.value
            and e["source"] == "MYPROFIT"
        ]
        candidates_inv_purch = self._generate_candidates_1to1(investments_myprofit, transactions_nubank, window_days=5)
        scored_inv_purch = self._score_investment_candidates(candidates_inv_purch)
        all_links.extend(self._resolve_conflicts(scored_inv_purch, "INVESTMENT_PURCHASE", existing_pairs))

        # -- Caso C: SAME_EVENT (Cross FP) --
        all_links.extend(self._match_same_events_cross_fp(events, existing_pairs))

        logger.info(
            f"[ReconciliationEngine] Gerados {len(all_links)} links "
            f"(AUTO: {sum(1 for lk in all_links if lk.status == 'AUTO_CONFIRMED')}, "
            f"SUGGESTED: {sum(1 for lk in all_links if lk.status == 'SUGGESTED')})"
        )
        return all_links

    def _generate_candidates_1to1(self, events_a, events_b, window_days=5):
        candidates = []
        for a in events_a:
            for b in events_b:
                if not a["event_date"] or not b["event_date"]:
                    continue
                if abs((a["event_date"] - b["event_date"]).days) <= window_days:
                    candidates.append((a, b))
        return candidates

    def _generate_invoice_candidates(self, invoices, transactions, window_days=5):
        # Agrupa faturas por ano/mês
        fatura_by_month = defaultdict(list)
        for inv in invoices:
            if inv["event_date"]:
                key = (inv["event_date"].year, inv["event_date"].month)
                fatura_by_month[key].append(inv)

        candidates = []
        for (year, month), inv_list in fatura_by_month.items():
            total_fatura = sum(abs(inv["amount_cents"] or 0) for inv in inv_list)
            if total_fatura == 0:
                continue
            
            # Usamos a data do último lançamento do mês como referência aproximada de vencimento
            ref_date = max(inv["event_date"] for inv in inv_list)
            
            for tx in transactions:
                if not tx["event_date"]: continue
                # Permite uma janela maior (ex: fatura fecha dia 25, paga dia 5) -> Até 15 dias de janela
                if abs((ref_date - tx["event_date"]).days) <= 15:
                    candidates.append((inv_list, total_fatura, tx))
        return candidates

    def _score_dividend_candidates(self, candidates):
        scored = []
        for a, b in candidates:
            # ETAPA 1: Validação de Natureza Financeira (Sinal deve ser igual)
            a_val = a["amount_cents"] or 0
            b_val = b["amount_cents"] or 0
            if a_val * b_val < 0:
                continue # Natureza incompatível (Receita vs Despesa)

            score = 0
            
            # 1. Date Score (Max 40)
            diff_days = abs((a["event_date"] - b["event_date"]).days)
            if diff_days == 0: score += 40
            elif diff_days == 1: score += 25
            elif diff_days <= 3: score += 10
            
            # 2. Amount Score (Max 40)
            a_amount = abs(a["amount_cents"] or 0)
            b_amount = abs(b["amount_cents"] or 0)
            if a_amount > 0:
                diff_pct = abs(a_amount - b_amount) / a_amount
                if diff_pct == 0: score += 40
                elif diff_pct <= 0.01: score += 20
                elif diff_pct <= 0.05: score += 5
            
            # 3. Description/Ticker Score (Max 20)
            ticker = a.get("metadata", {}).get("ticker", "").upper()
            b_desc = (b.get("metadata", {}).get("descricao_original", "") or "").lower()
            
            if ticker and ticker.lower() in b_desc:
                score += 20
            elif _DIVIDEND_KEYWORDS.search(b_desc):
                score += 15
            else:
                # Fuzzy match se houver alguma hint de substring
                if self._check_hints(ticker, b_desc):
                    score += 20

            confidence = score / 100.0
            if confidence >= 0.50:  # Threshold mínimo para ser considerado candidato
                scored.append({'a': a, 'b': b, 'conf': confidence, 'score_details': f"D{diff_days} A{a_amount}/{b_amount} T{ticker}"})
                
        return scored

    def _score_invoice_candidates(self, candidates):
        scored = []
        for inv_list, total_fatura, tx in candidates:
            # ETAPA 1: Validação de Natureza Financeira (Pagamento de fatura deve ser saída)
            if (tx["amount_cents"] or 0) > 0:
                continue # Receitas não podem ser pagamentos de fatura

            score = 0
            
            # 1. Amount Score (Max 40)
            tx_amount = abs(tx["amount_cents"] or 0)
            diff_pct = abs(total_fatura - tx_amount) / total_fatura if total_fatura > 0 else 1.0
            
            if diff_pct == 0: score += 40
            elif diff_pct <= 0.01: score += 30
            elif diff_pct <= 0.02: score += 20
            
            # 2. Date Score (Max 40)
            # Para faturas, a data de pagamento varia. Se for no mesmo mês/próximo mês e valor bater, confia mais no valor.
            # Aqui damos pontos pela proximidade do último lançamento.
            ref_date = max(inv["event_date"] for inv in inv_list)
            diff_days = abs((ref_date - tx["event_date"]).days)
            if diff_days <= 5: score += 40
            elif diff_days <= 10: score += 20
            elif diff_days <= 15: score += 10
            
            # 3. Description Score (Max 20)
            tx_desc = (tx.get("metadata", {}).get("descricao_original", "") or "").lower()
            if _INVOICE_PAYMENT_KEYWORDS.search(tx_desc):
                score += 20
                
            confidence = score / 100.0
            if confidence >= 0.60:
                scored.append({'inv_list': inv_list, 'tx': tx, 'conf': confidence})
                
        return scored

    def _score_investment_candidates(self, candidates):
        scored = []
        for a, b in candidates:
            # Validação de Natureza (Ambos devem ser saídas/despesas, ou pelo menos mesmo sinal)
            a_val = a["amount_cents"] or 0
            b_val = b["amount_cents"] or 0
            if a_val * b_val < 0:
                continue # Natureza incompatível
            
            score = 0
            
            # 1. Date Score (Max 40)
            diff_days = abs((a["event_date"] - b["event_date"]).days)
            if diff_days == 0: score += 40
            elif diff_days == 1: score += 25
            elif diff_days <= 3: score += 10
            
            # 2. Amount Score (Max 40)
            a_amount = abs(a_val)
            b_amount = abs(b_val)
            if a_amount > 0:
                diff_pct = abs(a_amount - b_amount) / a_amount
                if diff_pct == 0: score += 40
                elif diff_pct <= 0.01: score += 20
                elif diff_pct <= 0.05: score += 5
                
            # 3. Description Score (Max 20)
            ticker = a.get("metadata", {}).get("ticker", "").upper()
            b_desc = (b.get("metadata", {}).get("descricao_original", "") or "").lower()
            
            if ticker and ticker.lower() in b_desc:
                score += 20
            elif _INVESTMENT_PURCHASE_KEYWORDS.search(b_desc):
                score += 15
            else:
                if self._check_hints(ticker, b_desc):
                    score += 20

            confidence = score / 100.0
            if confidence >= 0.50:
                scored.append({'a': a, 'b': b, 'conf': confidence, 'score_details': f"D{diff_days} A{a_amount}/{b_amount} T{ticker}"})
                
        return scored

    def _resolve_conflicts(self, scored_candidates, link_type, existing_pairs) -> list[EventLink]:
        # Greedy Assignment (1:1)
        scored_candidates.sort(key=lambda x: x['conf'], reverse=True)
        consumed_a = set()
        consumed_b = set()
        links = []

        for match in scored_candidates:
            a_id = match['a']["id"]
            b_id = match['b']["id"]
            
            if a_id in consumed_a or b_id in consumed_b:
                continue
                
            pair = (a_id, b_id)
            if pair not in existing_pairs:
                status = 'AUTO_CONFIRMED' if match['conf'] >= 0.85 else 'SUGGESTED'
                links.append(EventLink(
                    id=str(uuid.uuid4()),
                    event_id_a=a_id,
                    event_id_b=b_id,
                    link_type=link_type,
                    confidence=match['conf'],
                    match_method="SCORING_ENGINE",
                    status=status,
                    notes=match.get('score_details', '')
                ))
                existing_pairs.add(pair)
            
            consumed_a.add(a_id)
            consumed_b.add(b_id)
            
        return links

    def _resolve_invoice_conflicts(self, scored_candidates, existing_pairs) -> list[EventLink]:
        # Greedy Assignment (N:1 para Faturas)
        scored_candidates.sort(key=lambda x: x['conf'], reverse=True)
        consumed_tx = set()
        consumed_inv_months = set()
        links = []

        for match in scored_candidates:
            tx_id = match['tx']["id"]
            inv_list = match['inv_list']
            # Identificador do mês
            ref_date = inv_list[0]["event_date"]
            month_key = f"{ref_date.year}-{ref_date.month}"
            
            if tx_id in consumed_tx or month_key in consumed_inv_months:
                continue
                
            status = 'AUTO_CONFIRMED' if match['conf'] >= 0.85 else 'SUGGESTED'
            
            for inv in inv_list:
                pair = (inv["id"], tx_id)
                if pair not in existing_pairs:
                    links.append(EventLink(
                        id=str(uuid.uuid4()),
                        event_id_a=inv["id"],
                        event_id_b=tx_id,
                        link_type="INVOICE_PAYMENT",
                        confidence=match['conf'],
                        match_method="SCORING_ENGINE",
                        status=status,
                        notes=f"fatura_month={month_key}"
                    ))
                    existing_pairs.add(pair)
                    
            consumed_tx.add(tx_id)
            consumed_inv_months.add(month_key)
            
        return links

    def _match_same_events_cross_fp(self, events, existing_pairs) -> list[EventLink]:
        links = []
        fp_map = {}

        for event in events:
            cross_fp = event.get("cross_fingerprint")
            if not cross_fp: continue

            if cross_fp in fp_map:
                other = fp_map[cross_fp]
                if event["source"] != other["source"]:
                    pair = (other["id"], event["id"])
                    if pair not in existing_pairs:
                        links.append(EventLink(
                            id=str(uuid.uuid4()),
                            event_id_a=other["id"],
                            event_id_b=event["id"],
                            link_type="SAME_EVENT",
                            confidence=1.0,
                            match_method="CROSS_FP",
                            status="AUTO_CONFIRMED",
                            notes=f"cross_fp={cross_fp[:16]}"
                        ))
                        existing_pairs.add(pair)
            else:
                fp_map[cross_fp] = event
        return links

    def _check_hints(self, ticker, desc):
        for h in self.hints:
            if h["pattern_a"].lower() in ticker.lower() and h["pattern_b"].lower() in desc:
                return True
        return False
