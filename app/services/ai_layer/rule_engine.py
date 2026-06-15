import re
import json
from sqlalchemy.orm import Session
from app.models.ai_layer import Rule
from typing import Dict, Any, Optional

class RuleEngineService:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_description(self, description: str) -> Dict[str, Any]:
        """
        Carrega regras ativas e aplica regex na descrição.
        Retorna classificação determinística.
        Impede múltiplos matches conflitantes escolhendo o de maior confidence_score (prioridade).
        """
        # Fetch active rules ordered by confidence_score descending (priority)
        active_rules = self.db.query(Rule).filter(Rule.active == 1).order_by(Rule.confidence_score.desc()).all()
        
        matches = []
        for rule in active_rules:
            try:
                # We assume pattern is a valid regex
                if re.search(rule.pattern, description, re.IGNORECASE):
                    matches.append(rule)
            except re.error:
                continue # ignore invalid regexes
                
        if not matches:
            return {
                "matched": False,
                "rule_id": None,
                "macro_categoria": None,
                "sub_categoria": None,
                "confidence": 0.0
            }
            
        # Top match by confidence_score
        best_rule = matches[0]
        
        # We assume rule.action stores a JSON payload with the categories, or just the category name.
        # Format expected: {"macro_categoria": "...", "sub_categoria": "..."}
        try:
            action_data = json.loads(best_rule.action)
            macro = action_data.get("macro_categoria")
            sub = action_data.get("sub_categoria")
        except json.JSONDecodeError:
            # Fallback if action is just a string representing the macro category
            macro = best_rule.action
            sub = None

        return {
            "matched": True,
            "rule_id": best_rule.id,
            "macro_categoria": macro,
            "sub_categoria": sub,
            "confidence": best_rule.confidence_score
        }
