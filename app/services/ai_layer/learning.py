from sqlalchemy.orm import Session
from app.models.core_finance import Transaction
from typing import List, Dict, Any

class LearningService:
    def __init__(self, db: Session):
        self.db = db

    def capture_manual_classifications(self) -> List[Dict[str, Any]]:
        """
        Captura classificações aprovadas ou realizadas manualmente pelo usuário.
        Ideal para criar um dataset gold-standard.
        """
        # Supondo que classificações do usuário tenham classificacao_fonte = 'USER' ou 'MANUAL'
        manual_txs = self.db.query(Transaction).filter(
            Transaction.classificacao_fonte.in_(['USER', 'MANUAL'])
        ).all()
        
        dataset = []
        for t in manual_txs:
            dataset.append({
                "id_economico": t.id_economico,
                "descricao": t.descricao_original,
                "macro_categoria": t.macro_categoria,
                "sub_categoria": t.sub_categoria,
                "natureza": t.natureza
            })
            
        return dataset

    def export_few_shot_examples(self, limit: int = 5) -> str:
        """
        Exporta exemplos no formato Few-Shot para injetar no Prompt da IA.
        Ex: "Descrição -> Categoria"
        """
        dataset = self.capture_manual_classifications()
        
        examples = []
        for item in dataset[:limit]:
            desc = item['descricao']
            macro = item['macro_categoria'] or 'Outros'
            sub = item['sub_categoria'] or 'Indefinido'
            examples.append(f"Input: {desc} -> Output: {{\"macro_categoria\": \"{macro}\", \"sub_categoria\": \"{sub}\"}}")
            
        return "\n".join(examples)
