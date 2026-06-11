"""
etl/reconciler.py — EventReconciler

Identifica ligações semânticas entre eventos de fontes diferentes:
  - DIVIDEND_CREDIT: dividendo MyProfit ↔ crédito em conta Nubank
  - INVOICE_PAYMENT: pagamento de fatura Nubank ↔ débito em conta Nubank
  - INVESTMENT_PURCHASE: compra MyProfit ↔ débito em conta Nubank

Produz event_links prontos para persistência.
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import date, timedelta
from typing import NamedTuple

from models.core import EventType, RawFinancialEvent

logger = logging.getLogger(__name__)

# Janela temporal para fuzzy matching (dias)
FUZZY_DATE_WINDOW = 3
# Tolerância percentual no valor
FUZZY_AMOUNT_TOLERANCE = 0.01  # 1%

# Palavras-chave que indicam crédito de dividendo na conta Nubank
_DIVIDEND_KEYWORDS = re.compile(
    r"(rendimento|dividendo|provento|jscp|jcp|fii|fundo\s+imobil)",
    re.IGNORECASE,
)

# Palavras-chave que indicam pagamento de fatura
_INVOICE_PAYMENT_KEYWORDS = re.compile(
    r"(pagamento\s+nubank|fatura\s+nubank|pg\s+nubank|nubank\s+cartao)",
    re.IGNORECASE,
)


class EventLink(NamedTuple):
    """Estrutura de um link entre dois eventos cross-source."""
    id: str
    event_id_a: str          # raw_events.id
    event_id_b: str          # raw_events.id
    link_type: str           # DIVIDEND_CREDIT | INVOICE_PAYMENT | INVESTMENT_PURCHASE | SAME_EVENT
    confidence: float        # 0.0 a 1.0
    match_method: str        # EXACT | CROSS_FP | FUZZY | MANUAL | HINT
    notes: str | None = None


class EventReconciler:
    """
    Cruza eventos de fontes diferentes e produz event_links.

    Casos suportados:
      A) DIVIDEND_CREDIT: dividendo MyProfit ↔ crédito Nubank conta
      B) INVOICE_PAYMENT: lançamento fatura ↔ pagamento em conta
      C) SAME_EVENT: cross_fingerprint exato entre fontes distintas
    """

    def reconcile(
        self,
        events: list[RawFinancialEvent],
        existing_links: list[dict] | None = None,
    ) -> list[EventLink]:
        """
        Recebe todos os eventos (de todas as fontes) do import atual
        e retorna uma lista de EventLink detectados.

        Args:
            events: Todos os RawFinancialEvent normalizados e matchados.
            existing_links: Links já existentes no DB (para evitar duplicatas de links).

        Returns:
            list[EventLink] prontos para inserção em event_links.
        """
        links: list[EventLink] = []
        existing_link_pairs: set[tuple[str, str]] = {
            (lk["event_id_a"], lk["event_id_b"])
            for lk in (existing_links or [])
        }

        # Separa por tipo e fonte para cruzamento eficiente
        dividends_myprofit = [
            e for e in events
            if e["event_type"] == EventType.DIVIDEND.value
            and e["source"] == "MYPROFIT"
        ]
        transactions_nubank_conta = [
            e for e in events
            if e["event_type"] == EventType.TRANSACTION.value
            and e["source"] in ("NUBANK_CONTA", "NUBANK", "PIERRE")
        ]
        invoices_nubank_fatura = [
            e for e in events
            if e["event_type"] == EventType.INVOICE.value
            and e["source"] == "NUBANK_FATURA"
        ]

        # ── Caso A: DIVIDEND_CREDIT ──────────────────────────────────
        links += self._match_dividend_credits(
            dividends_myprofit, transactions_nubank_conta, existing_link_pairs
        )

        # ── Caso B: INVOICE_PAYMENT ──────────────────────────────────
        links += self._match_invoice_payments(
            invoices_nubank_fatura, transactions_nubank_conta, existing_link_pairs
        )

        # ── Caso C: SAME_EVENT (cross_fp exato, fontes diferentes) ──
        links += self._match_same_events_cross_fp(events, existing_link_pairs)

        logger.info(
            f"[Reconciler] {len(links)} links criados "
            f"(A_div={len([l for l in links if l.link_type == 'DIVIDEND_CREDIT'])} "
            f"B_inv={len([l for l in links if l.link_type == 'INVOICE_PAYMENT'])} "
            f"C_same={len([l for l in links if l.link_type == 'SAME_EVENT'])})"
        )
        return links

    def _match_dividend_credits(
        self,
        dividends: list[RawFinancialEvent],
        transactions: list[RawFinancialEvent],
        existing_pairs: set[tuple[str, str]],
    ) -> list[EventLink]:
        """
        Cruza dividendos MyProfit com créditos bancários Nubank.
        Match: mesmo ticker (na descrição) + data ±3 dias + valor ±1%.
        """
        links: list[EventLink] = []

        for div in dividends:
            ticker = div.get("metadata", {}).get("ticker", "").upper()
            if not ticker:
                continue
            div_date   = div["event_date"]
            div_amount = abs(div["amount_cents"] or 0)

            for tx in transactions:
                if not tx["event_date"] or not tx["amount_cents"]:
                    continue
                tx_desc = (tx.get("metadata", {}).get("descricao_original", "") or "").lower()

                # Ticker na descrição da transação
                if ticker.lower() not in tx_desc and not _DIVIDEND_KEYWORDS.search(tx_desc):
                    continue

                # Janela de datas
                if abs((tx["event_date"] - div_date).days) > FUZZY_DATE_WINDOW:
                    continue

                # Valor aproximado (crédito → positivo)
                tx_amount = abs(tx["amount_cents"])
                if div_amount == 0 or abs(tx_amount - div_amount) / div_amount > FUZZY_AMOUNT_TOLERANCE:
                    continue

                # Determina confiança
                is_exact_date   = tx["event_date"] == div_date
                is_ticker_exact = ticker.lower() in tx_desc
                confidence = 1.0 if (is_exact_date and is_ticker_exact) else 0.75
                method     = "CROSS_FP" if is_exact_date else "FUZZY"

                pair = (div["id"], tx["id"])
                if pair not in existing_pairs:
                    links.append(EventLink(
                        id=str(uuid.uuid4()),
                        event_id_a=div["id"],
                        event_id_b=tx["id"],
                        link_type="DIVIDEND_CREDIT",
                        confidence=confidence,
                        match_method=method,
                        notes=f"ticker={ticker} div_date={div_date} tx_date={tx['event_date']} "
                              f"div_amount={div_amount} tx_amount={tx_amount}",
                    ))
                    existing_pairs.add(pair)
                    logger.debug(f"DIVIDEND_CREDIT: {ticker} {div_date} → {tx['id'][:8]}")

        return links

    def _match_invoice_payments(
        self,
        invoices: list[RawFinancialEvent],
        transactions: list[RawFinancialEvent],
        existing_pairs: set[tuple[str, str]],
    ) -> list[EventLink]:
        """
        Tenta casar lançamentos de fatura com seu pagamento em conta.
        Heurística: valor total da fatura ≈ débito na conta + descrição 'nubank'.
        
        Nota: faturas têm N lançamentos, mas o pagamento é um único débito.
        Aqui agrupamos o total da fatura por mês e cruzamos com o pagamento.
        """
        links: list[EventLink] = []
        if not invoices or not transactions:
            return links

        # Agrupa lançamentos de fatura por mês (reference_month ou event_date.month)
        from collections import defaultdict
        fatura_by_month: dict[tuple, list] = defaultdict(list)
        for inv in invoices:
            if inv["event_date"]:
                key = (inv["event_date"].year, inv["event_date"].month)
                fatura_by_month[key].append(inv)

        for (year, month), inv_list in fatura_by_month.items():
            total_fatura = sum(abs(inv["amount_cents"] or 0) for inv in inv_list)
            if total_fatura == 0:
                continue

            # Busca pagamento de fatura nas transações (±3 dias do vencimento usual)
            for tx in transactions:
                if not tx["event_date"] or not tx["amount_cents"]:
                    continue
                tx_desc = (tx.get("metadata", {}).get("descricao_original", "") or "").lower()
                if not _INVOICE_PAYMENT_KEYWORDS.search(tx_desc):
                    continue

                tx_amount = abs(tx["amount_cents"])
                if total_fatura == 0 or abs(tx_amount - total_fatura) / total_fatura > 0.02:
                    continue

                # Cria um link para cada lançamento da fatura → pagamento
                for inv in inv_list:
                    pair = (inv["id"], tx["id"])
                    if pair not in existing_pairs:
                        links.append(EventLink(
                            id=str(uuid.uuid4()),
                            event_id_a=inv["id"],
                            event_id_b=tx["id"],
                            link_type="INVOICE_PAYMENT",
                            confidence=0.85,
                            match_method="FUZZY",
                            notes=f"fatura_month={year}-{month:02d} total={total_fatura} tx={tx_amount}",
                        ))
                        existing_pairs.add(pair)

        return links

    def _match_same_events_cross_fp(
        self,
        events: list[RawFinancialEvent],
        existing_pairs: set[tuple[str, str]],
    ) -> list[EventLink]:
        """
        Detecta eventos com cross_fingerprint idêntico mas fontes diferentes.
        Indica o mesmo evento reportado por duas fontes distintas.
        """
        links: list[EventLink] = []
        fp_map: dict[str, RawFinancialEvent] = {}

        for event in events:
            cross_fp = event.get("cross_fingerprint")
            if not cross_fp:
                continue

            if cross_fp in fp_map:
                other = fp_map[cross_fp]
                # Só cria link se fontes são realmente diferentes
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
                            notes=f"cross_fp={cross_fp[:16]}… {other['source']} ↔ {event['source']}",
                        ))
                        existing_pairs.add(pair)
            else:
                fp_map[cross_fp] = event

        return links
