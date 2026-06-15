from sqlalchemy.orm import Session
from typing import Dict, Any
from app.services.ai_layer.rule_engine import RuleEngineService

class AIProviderInterface:
    def classify(self, description: str) -> Dict[str, Any]:
        raise NotImplementedError()

class MockProvider(AIProviderInterface):
    def classify(self, description: str) -> Dict[str, Any]:
        # Simulando uma resposta da IA
        if "uber" in description.lower() or "99" in description.lower():
            return {
                "matched": True,
                "macro_categoria": "Transporte",
                "sub_categoria": "Aplicativo",
                "confidence": 0.85
            }
        return {
            "matched": False,
            "confidence": 0.0
        }

class ClassificationEngineService:
    def __init__(self, db: Session, ai_provider: AIProviderInterface = MockProvider()):
        self.db = db
        self.rule_engine = RuleEngineService(db)
        self.ai_provider = ai_provider

    def classify_transaction(self, description: str, is_reconciled: bool = False) -> Dict[str, Any]:
        """
        Fluxo obrigatório:
        1. Reconciliation (ignorado se já reconciliado, mas no fluxo macro ele entra antes)
        2. Rules
        3. AI
        4. Fallback
        """
        if is_reconciled:
            return {"source": "RECONCILIATION", "macro_categoria": None, "sub_categoria": None}

        # PASSO 1: Tentar RuleEngine
        rule_result = self.rule_engine.evaluate_description(description)
        if rule_result["matched"]:
            return {
                "source": "RULES",
                "macro_categoria": rule_result.get("macro_categoria"),
                "sub_categoria": rule_result.get("sub_categoria"),
                "confidence": rule_result.get("confidence")
            }

        # PASSO 2: Simular chamada AI
        ai_result = self.ai_provider.classify(description)
        if ai_result.get("matched"):
            return {
                "source": "AI",
                "macro_categoria": ai_result.get("macro_categoria"),
                "sub_categoria": ai_result.get("sub_categoria"),
                "confidence": ai_result.get("confidence")
            }

        # PASSO 3: Fallback
        return {
            "source": "FALLBACK",
            "macro_categoria": "Outros",
            "sub_categoria": "Indefinido",
            "confidence": 0.0
        }
