from datetime import date
from pathlib import Path

from database.repository import DatabaseManager
from parsers.myprofit import parse_dividends, parse_positions
from parsers.nubank import parse_nubank_file
from services.categorizer import SmartCategorizer


def etl_cashflow(db: DatabaseManager, categorizer: SmartCategorizer, data_dir: Path) -> tuple[int, int]:
    total_inserted, total_updated = 0, 0
    nubank_files = list((data_dir / "raw" / "nubank").glob("*.csv"))

    for file_path in nubank_files:
        transacoes = parse_nubank_file(file_path)
        if not transacoes:
            continue

        run_id = db.register_etl_run("NUBANK", file_path.name, len(transacoes))
        inserted, updated = db.upsert_transactions(transacoes, categorizer)
        db.update_etl_run_metrics(run_id, inserted, updated)

        total_inserted += inserted
        total_updated += updated
        print(f"[CAIXA] {file_path.name}: {inserted} novas | {updated} atualizadas")

    return total_inserted, total_updated


def etl_positions(db: DatabaseManager, data_dir: Path) -> tuple[int, int]:
    myprofit_dir = data_dir / "raw" / "myprofit"
    path_pos = myprofit_dir / "tableExport.csv"

    if not path_pos.exists():
        return 0, 0

    positions = parse_positions(path_pos, date.today())
    if not positions:
        return 0, 0

    run_id = db.register_etl_run("MYPROFIT", path_pos.name, len(positions))
    inserted, updated = db.upsert_positions(positions)
    db.update_etl_run_metrics(run_id, inserted, updated)
    print(f"[PATRIMONIO] {path_pos.name}: {inserted} novas | {updated} atualizadas")
    return inserted, updated


def etl_dividends(db: DatabaseManager, data_dir: Path) -> tuple[int, int]:
    myprofit_dir = data_dir / "raw" / "myprofit"
    path_prov = myprofit_dir / "proventos.csv"

    if not path_prov.exists():
        return 0, 0

    dividends = parse_dividends(path_prov)
    if not dividends:
        return 0, 0

    run_id = db.register_etl_run("MYPROFIT", path_prov.name, len(dividends))
    inserted, updated = db.upsert_dividends(dividends)
    db.update_etl_run_metrics(run_id, inserted, updated)
    print(f"[DIVIDENDOS] {path_prov.name}: {inserted} novas | {updated} atualizadas")
    return inserted, updated


def executar_etl_completo():
    data_dir = Path("data")
    db = DatabaseManager()
    categorizer = SmartCategorizer(Path("taxonomy/rules.csv"))

    print("\n" + "=" * 60)
    print("EXECUTANDO ETL COMPLETO (CAIXA + PATRIMONIO)")
    print("=" * 60)

    caixa_inserted, caixa_updated = etl_cashflow(db, categorizer, data_dir)
    patrimonio_inserted, patrimonio_updated = etl_positions(db, data_dir)
    dividendos_inserted, dividendos_updated = etl_dividends(db, data_dir)

    total_inserted = caixa_inserted + patrimonio_inserted + dividendos_inserted
    total_updated = caixa_updated + patrimonio_updated + dividendos_updated

    print(f"\nETL Concluido. Insercoes totais: {total_inserted} | Atualizacoes totais: {total_updated}")


if __name__ == "__main__":
    executar_etl_completo()