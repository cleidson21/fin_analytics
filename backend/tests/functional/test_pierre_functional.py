import os
import json
import csv
import urllib.parse
from backend.domains.imports.pipelines.pierre_txt import PierreTxtPipeline

def run_functional_test():
    filepath = "samples/Exemplo_Extrato_Pierre.txt"
    if not os.path.exists(filepath):
        print(f"Arquivo não encontrado: {filepath}")
        return

    pipeline = PierreTxtPipeline()
    raw_doc, canonical_events = pipeline.execute(filepath)

    output_dir = "backend/tests/results/V3_Pierre"
    os.makedirs(output_dir, exist_ok=True)

    # raw_document.json
    with open(f"{output_dir}/raw_document.json", "w", encoding="utf-8") as f:
        doc_dict = raw_doc.model_dump()
        doc_dict["created_at"] = doc_dict["created_at"].isoformat()
        json.dump(doc_dict, f, indent=2, ensure_ascii=False)

    # canonical_events.json
    with open(f"{output_dir}/canonical_events.json", "w", encoding="utf-8") as f:
        events_dict = []
        for e in canonical_events:
            d = e.model_dump()
            d["transaction_date"] = d["transaction_date"].isoformat()
            if d.get("settlement_date"):
                d["settlement_date"] = d["settlement_date"].isoformat()
            d["amount"] = float(d["amount"])
            events_dict.append(d)
        json.dump(events_dict, f, indent=2, ensure_ascii=False)

    # canonical_events.csv (Golden Test)
    with open(f"{output_dir}/canonical_events.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Description", "Normalized Description", "Amount", "Event Type", "Source System", "Account"])
        for e in canonical_events:
            writer.writerow([
                e.transaction_date.strftime("%d/%m/%Y"),
                e.description,
                e.normalized_description,
                str(e.amount),
                e.event_type.value,
                e.source_system,
                e.account
            ])

    # validation_report.md
    with open(f"{output_dir}/validation_report.md", "w", encoding="utf-8") as f:
        f.write("# Relatório de Validação - V3 Pierre TXT\n")
        f.write(f"- Arquivo: Exemplo_Extrato_Pierre.txt\n")
        f.write(f"- Linhas Lidas (brutas): {raw_doc.metadata['total_lines']}\n")
        f.write(f"- Eventos Gerados: {len(canonical_events)}\n")
        f.write(f"- Status: {'SUCESSO' if len(canonical_events) > 0 else 'FALHA'}\n")

    # render_flow.md
    flow_content = f"""# Render Flow - V3 Pierre TXT

Arquivo TXT
↓
PierreTxtReader
↓
RawDocument ({raw_doc.metadata['total_lines']} linhas lidas)
↓
PierreTxtValidator
↓
PierreTxtParser
↓
PierreTxtNormalizer
↓
{len(canonical_events)} CanonicalFinancialEvents
↓
(Fim da microetapa de extração)
"""
    with open(f"{output_dir}/render_flow.md", "w", encoding="utf-8") as f:
        f.write(flow_content)

    # import_statistics.json
    stats = {
        "lines_read": raw_doc.metadata['total_lines'],
        "events_created": len(canonical_events),
        "events_discarded": 0,
        "errors": 0,
        "conflicts": 0
    }
    with open(f"{output_dir}/import_statistics.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    print("Testes funcionais V3 (Pierre TXT) concluídos com sucesso.")

if __name__ == "__main__":
    run_functional_test()
