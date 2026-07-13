import os
import json
import csv
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from backend.domains.imports.pipelines.myprofit_proventos import MyProfitProventosPipeline

# Helper for JSON serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "isoformat"): # date
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super(DecimalEncoder, self).default(obj)

def run():
    print("\n[V4] Iniciando Teste Funcional Completo: MyProfit Proventos")
    
    sample_file = "samples/Exemplo_Proventos_Myprofit.csv"
    output_dir = "backend/tests/results/V4_MyProfit_Proventos"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    pipeline = MyProfitProventosPipeline()
    success, raw_doc, canonical_events = pipeline.execute(sample_file)
    
    if not success:
        print("FALHA: Pipeline retornou erro.")
        return
        
    # Salvar Eventos Canônicos em JSON
    json_path = os.path.join(output_dir, "canonical_events.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        events_dicts = [e.model_dump() for e in canonical_events]
        json.dump(events_dicts, f, indent=2, ensure_ascii=False, cls=DecimalEncoder)
        
    # Salvar Eventos Canônicos em CSV
    csv_path = os.path.join(output_dir, "canonical_events.csv")
    if canonical_events:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=canonical_events[0].model_dump().keys())
            writer.writeheader()
            for e in canonical_events:
                # Convert Decimals and Dates to strings for CSV
                row = {k: str(v) if v is not None else "" for k, v in e.model_dump().items()}
                writer.writerow(row)
                
    # Salvar Estatísticas
    stats = {
        "source": raw_doc.source if raw_doc else "MYPROFIT",
        "total_lines_read": raw_doc.metadata.get("total_lines", 0) if raw_doc else 0,
        "total_events_extracted": len(canonical_events),
        "execution_date": datetime.now().isoformat()
    }
    stats_path = os.path.join(output_dir, "import_statistics.json")
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
        
    print(f"SUCESSO: {len(canonical_events)} proventos extraídos.")
    print(f"Resultados salvos em: {output_dir}")

if __name__ == "__main__":
    run()
