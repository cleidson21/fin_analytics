"""
etl/classifier.py — EventClassifier

Wraps o SmartCategorizer existente e adiciona regras cross-source baseadas
nos event_links gerados pelo EventReconciler.

Atualiza o pipeline_status dos eventos para CLASSIFIED.
"""
from __future__ import annotations

import logging
from pathlib import Path

from models.core import EventType, PipelineStatus, RawFinancialEvent

logger = logging.getLogger(__name__)


class EventClassifier:
    """
    Classifica eventos financeiros usando:
    1. SmartCategorizer (regras CSV + heurísticas) para TRANSACTIONs
    2. Regras hard-coded para eventos com context cross-source (DIVIDEND, INVOICE, etc.)
    3. Context boost: se um evento tem event_link, a classificação é enriquecida
    """

    def __init__(self, rules_path: Path | None = None, db_manager=None):
        self._categorizer = None
        self._db_manager = db_manager
        self._active_rules = []
        if self._db_manager:
            try:
                self._active_rules = self._db_manager.get_active_rules()
            except Exception as e:
                logger.warning(f"[Classifier] Erro ao carregar regras da Memória Financeira: {e}")

        if rules_path and rules_path.exists():
            try:
                from services.categorizer import SmartCategorizer
                self._categorizer = SmartCategorizer(rules_path)
            except Exception as e:
                logger.warning(f"[Classifier] SmartCategorizer não carregado: {e}")

    def classify(
        self,
        events: list[RawFinancialEvent],
        event_links: list | None = None,
    ) -> list[RawFinancialEvent]:
        """
        Classifica cada evento e atualiza pipeline_status para CLASSIFIED.

        Args:
            events: Eventos com pipeline_status >= MATCHED
            event_links: EventLink gerados pelo Reconciler (para context boost)

        Returns:
            Mesmos eventos com metadata enriquecido e pipeline_status = CLASSIFIED
        """
        # Índice de links para lookup rápido
        linked_ids: dict[str, str] = {}  # event_id → link_type
        for lk in (event_links or []):
            link_type = lk.link_type if hasattr(lk, "link_type") else lk.get("link_type", "")
            linked_ids[lk.event_id_a if hasattr(lk, "event_id_a") else lk.get("event_id_a")] = link_type
            linked_ids[lk.event_id_b if hasattr(lk, "event_id_b") else lk.get("event_id_b")] = link_type

        for event in events:
            event_type = event["event_type"]
            link_type  = linked_ids.get(event["id"])

            if event_type == EventType.TRANSACTION.value or event_type == EventType.INVOICE.value:
                self._classify_transaction(event, link_type)
            elif event_type == EventType.DIVIDEND.value:
                self._classify_dividend(event, link_type)
            elif event_type == EventType.POSITION.value:
                event["metadata"]["macro_categoria"] = "INVESTIMENTOS"
                event["metadata"]["natureza"]        = "PATRIMONIAL"
            elif event_type == EventType.PORTFOLIO_EVO.value:
                event["metadata"]["macro_categoria"] = "INVESTIMENTOS"
                event["metadata"]["natureza"]        = "EVOLUCAO_PATRIMONIAL"

            event["pipeline_status"] = PipelineStatus.CLASSIFIED.value

        classified = sum(1 for e in events if e["pipeline_status"] == PipelineStatus.CLASSIFIED.value)
        logger.info(f"[Classifier] {classified} eventos classificados")
        return events

    def _classify_transaction(
        self,
        event: RawFinancialEvent,
        link_type: str | None,
    ) -> None:
        """Classifica uma TRANSACTION ou INVOICE com prioridade estrita de regras."""
        meta = event.get("metadata", {})
        desc = meta.get("descricao_normalizada") or meta.get("descricao_original", "")

        import json
        import re
        from models.core import ClassificationSource

        # PRIORITY 1: NEGATIVE_MATCH
        # PRIORITY 2: RECONCILIATION
        # PRIORITY 3: TICKER_TRANSLATION
        # PRIORITY 4: DIVIDEND_TRANSLATION
        # PRIORITY 5: CATEGORIZATION

        # Context boost a partir de event_links (Isso engloba RECONCILIATION rules já consolidadas)
        if link_type == "DIVIDEND_CREDIT":
            event["metadata"]["macro_categoria"] = "RENDA_PASSIVA"
            event["metadata"]["sub_categoria"]   = "DIVIDENDO"
            event["metadata"]["natureza"]        = "RECEITA"
            event["metadata"]["classificacao_fonte"] = ClassificationSource.RULE.value
            return

        if link_type == "INVOICE_PAYMENT":
            event["metadata"]["macro_categoria"] = "FINANCEIRO"
            event["metadata"]["sub_categoria"]   = "PAGAMENTO_CARTAO"
            event["metadata"]["natureza"]        = "DESPESA"
            event["metadata"]["classificacao_fonte"] = ClassificationSource.RULE.value
            return

        if link_type == "INVESTMENT_PURCHASE":
            event["metadata"]["macro_categoria"] = "INVESTIMENTOS"
            event["metadata"]["sub_categoria"]   = "COMPRA_ATIVO"
            event["metadata"]["natureza"]        = "DESPESA"
            event["metadata"]["classificacao_fonte"] = ClassificationSource.RULE.value
            return

        # PRIORITY 5: CATEGORIZATION rules
        if desc:
            for rule in self._active_rules:
                if rule["rule_type"] == "CATEGORIZATION":
                    try:
                        pattern_obj = json.loads(rule["pattern"])
                        keyword = pattern_obj.get("description_matches", "")
                        if keyword and keyword.upper() in desc.upper():
                            action_obj = json.loads(rule["action"])
                            event["metadata"]["macro_categoria"] = action_obj.get("macro_categoria", "OUTROS")
                            event["metadata"]["sub_categoria"]   = action_obj.get("sub_categoria", "INDEFINIDO")
                            event["metadata"]["natureza"]        = action_obj.get("natureza", "INDEFINIDO")
                            event["metadata"]["classificacao_fonte"] = ClassificationSource.RULE.value
                            event["metadata"]["applied_rule_id"] = rule["id"]
                            event["metadata"]["confidence_score"] = rule["confidence_score"]
                            return
                    except Exception as e:
                        logger.warning(f"[Classifier] Erro ao aplicar regra {rule['id']}: {e}")

        # PRIORITY 6: Heurísticas SmartCategorizer
        if self._categorizer and desc:
            try:
                cat_result = self._categorizer.categorize(desc)
                event["metadata"]["macro_categoria"] = cat_result.get("macro_categoria", "OUTROS")
                event["metadata"]["sub_categoria"]   = cat_result.get("sub_categoria", "INDEFINIDO")
                event["metadata"]["natureza"]        = cat_result.get("natureza", "INDEFINIDO")
                event["metadata"]["classificacao_fonte"] = ClassificationSource.HEURISTIC.value
            except Exception as e:
                logger.warning(f"[Classifier] SmartCategorizer error: {e}")
                self._set_pending(event)
        else:
            # PRIORITY 7: Fallback
            self._set_pending(event)

    def _classify_dividend(
        self,
        event: RawFinancialEvent,
        link_type: str | None,
    ) -> None:
        """Classifica um DIVIDEND."""
        from models.core import ClassificationSource
        event["metadata"]["macro_categoria"] = "RENDA_PASSIVA"
        event["metadata"]["sub_categoria"]   = event["metadata"].get("tipo_evento", "DIVIDENDO")
        event["metadata"]["natureza"]        = "RECEITA"
        event["metadata"]["classificacao_fonte"] = ClassificationSource.IMPORT.value

    @staticmethod
    def _set_pending(event: RawFinancialEvent) -> None:
        from models.core import ClassificationSource
        event["metadata"]["macro_categoria"] = "OUTROS"
        event["metadata"]["sub_categoria"]   = "INDEFINIDO"
        event["metadata"]["natureza"]        = "INDEFINIDO"
        event["metadata"]["classificacao_fonte"] = ClassificationSource.IMPORT.value
