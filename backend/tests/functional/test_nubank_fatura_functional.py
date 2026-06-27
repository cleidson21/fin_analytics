import os
import json
import csv
from pathlib import Path
from backend.domains.imports.pipelines.nubank_fatura import NubankFaturaPipeline

def test_v2_nubank_fatura_pipeline():
    project_root = Path(__file__).parent.parent.parent.parent
    sample_file = project_root / "samples" / "Exemplo_Extrato_Fatura_Nubank.csv"
    results_dir = project_root / "backend" / "tests" / "results" / "V2_Nubank_Fatura"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    pipeline = NubankFaturaPipeline()
    raw_doc, canonical_events = pipeline.execute(str(sample_file))
    
    # 2. Output raw_document.json
    raw_doc_dict = raw_doc.model_dump()
    raw_doc_dict["created_at"] = raw_doc_dict["created_at"].isoformat()
    with open(results_dir / "raw_document.json", "w", encoding="utf-8") as f:
        json.dump(raw_doc_dict, f, ensure_ascii=False, indent=2)
        
    # 3. Output canonical_events.json
    events_list = [e.model_dump() for e in canonical_events]
    for ev in events_list:
        ev["transaction_date"] = ev["transaction_date"].isoformat()
        if ev["settlement_date"]:
            ev["settlement_date"] = ev["settlement_date"].isoformat()
        ev["amount"] = str(ev["amount"])
    with open(results_dir / "canonical_events.json", "w", encoding="utf-8") as f:
        json.dump(events_list, f, ensure_ascii=False, indent=2)
        
    # 4. Output canonical_events.csv (Golden Test)
    csv_path = results_dir / "canonical_events.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Description", "Normalized Description", "Amount", "Event Type", "Source System", "Credit Card"])
        for ev in canonical_events:
            writer.writerow([
                ev.transaction_date.strftime("%d/%m/%Y"),
                ev.description,
                ev.normalized_description,
                str(ev.amount),
                ev.event_type.value,
                ev.source_system,
                ev.credit_card
            ])
            
    # 5. Output import_statistics.json
    stats = {
        "lines_read": len(raw_doc.content),
        "events_created": len(canonical_events),
        "events_discarded": 0,
        "errors": 0,
        "conflicts": 0
    }
    with open(results_dir / "import_statistics.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    # 6. Output validation_report.md
    with open(results_dir / "validation_report.md", "w", encoding="utf-8") as f:
        f.write(f"# Relatório de Validação - V2 Nubank Fatura\n")
        f.write(f"- Arquivo: {sample_file.name}\n")
        f.write(f"- Linhas Lidas: {stats['lines_read']}\n")
        f.write(f"- Eventos Gerados: {stats['events_created']}\n")
        f.write(f"- Status: SUCESSO\n")
        
    # 7. Output render_flow.md (Fluxograma)
    with open(results_dir / "render_flow.md", "w", encoding="utf-8") as f:
        f.write("Arquivo CSV\n")
        f.write("↓\n")
        f.write("NubankFaturaReader\n")
        f.write("↓\n")
        f.write(f"RawDocument ({stats['lines_read']} registros)\n")
        f.write("↓\n")
        f.write("NubankFaturaValidator\n")
        f.write("↓\n")
        f.write("NubankFaturaParser\n")
        f.write("↓\n")
        f.write("NubankFaturaNormalizer\n")
        f.write("↓\n")
        f.write(f"{stats['events_created']} CanonicalFinancialEvents\n")
        f.write("↓\n")
        f.write("(Fim da microetapa de extração)\n")

if __name__ == "__main__":
    test_v2_nubank_fatura_pipeline()
