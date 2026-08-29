"""
Testes da Fase 1 — MYPROFIT_ATIVOS (versão corrigida)
Usa account_id como string simples (sem FK para accounts).
"""

import sys
import os
import asyncio
import uuid
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.integrations.myprofit.parser import MyProfitParser

# --------------------------------------------------------------------------
# Dados de teste
# --------------------------------------------------------------------------

ATIVOS_CSV = b"""Ativo,Qtd,"Preco medio",Setor
PETR3,100,"R$ 41,33",Petroleo
VALE3,50,"R$ 72,12","Materiais Basicos"
MXRF11,552,"R$ 10,21",Papeis
BTC,"0,0014","R$ 468.146,30",Criptomoeda
"""

ATIVOS_CSV_UPDATED = b"""Ativo,Qtd,"Preco medio",Setor
PETR3,120,"R$ 41,33",Petroleo
VALE3,50,"R$ 72,12","Materiais Basicos"
"""

ATIVOS_CSV_WITH_TOTAL = b"""Ativo,Qtd,"Preco medio","Preco de aquisicao","Total investido","Preco atual","Total atual",Ganho,"% Ganho",Setor
PETR3,100,"R$ 41,33","R$ 41,33","R$ 4.133,00","R$ 62,59","R$ 6.259,00","R$ 2.126,00","51,43 %",Petroleo
VALE3,50,"R$ 72,12","R$ 72,12","R$ 3.606,00","R$ 81,79","R$ 4.089,50","R$ 483,50","13,41 %","Materiais Basicos"
"2 ativos",,Total:,,"R$ 7.739,00",,"R$ 10.348,50","R$ 2.609,50","33,72 %",,
"""

ATIVOS_CSV_INCOMPATIBLE = b"""Data,"% Mensal","% Acumulada",Patrimonio
Set-2022,"0,00 %","0,00 %","R$ 0,00"
"""

ATIVOS_CSV_ONLY_REQUIRED = b"""Ativo,Qtd
ITSA4,200
BBAS3,80
"""

ATIVOS_CSV_DIFFERENT_ORDER = b"""Setor,Qtd,Ativo,"Preco medio"
Petroleo,100,PETR3,"R$ 41,33"
Papeis,552,MXRF11,"R$ 10,21"
"""

ATIVOS_CSV_PTBR = b"""Ativo,Qtd,"Preco medio",Setor
BTC,"0,0014","R$ 468.146,30",Criptomoeda
TESOURO-SELIC-2031,"0,24","R$ 16.381,78","Tesouro Direto"
MXRF11,552,"R$ 10,21",Papeis
IVV,"0,88","R$ 3.757,29",Outros
VXUS,"0,45","R$ 438,49",Outros
"""

# Account ID de teste (string opaca, sem FK)
TEST_ACCOUNT_ID = "test-myprofit-account-001"
TEST_ACCOUNT_ID_2 = "test-myprofit-account-002"

PASSED = []
FAILED = []

def test(name, condition, detail=""):
    if condition:
        print(f"  [OK] {name}")
        PASSED.append(name)
    else:
        print(f"  [FAIL] {name}" + (f": {detail}" if detail else ""))
        FAILED.append((name, detail))


# --------------------------------------------------------------------------
# TESTES DE PARSER (A-K)
# --------------------------------------------------------------------------

def test_parser():
    print("\n== PARSER - Testes A a K ==\n")

    # A — Parse basico
    parser = MyProfitParser(ATIVOS_CSV)
    rows, report = parser.parse_ativos()
    test("A1 - headers validos, sem erros", len(report["errors"]) == 0, str(report.get("errors")))
    test("A2 - 4 linhas validas", len(rows) == 4, f"got {len(rows)}: {[r['ticker'] for r in rows]}")
    test("A3 - PETR3 qty=100", any(r["ticker"] == "PETR3" and r["quantity"] == 100.0 for r in rows))
    test("A4 - BTC qty=0.0014", any(r["ticker"] == "BTC" and abs(r["quantity"] - 0.0014) < 1e-6 for r in rows))
    test("A5 - Setor preenchido em PETR3", any(r["ticker"] == "PETR3" and r["sector"] == "Petroleo" for r in rows))

    # B — Reimportacao identica
    rows2, _ = parser.parse_ativos()
    test("B1 - Reimportacao identica produz mesmo resultado", rows == rows2)

    # C — Alteracao de quantidade
    parser2 = MyProfitParser(ATIVOS_CSV_UPDATED)
    rows3, _ = parser2.parse_ativos()
    petr3 = next((r for r in rows3 if r["ticker"] == "PETR3"), None)
    test("C1 - PETR3 qty alterado para 120", petr3 and petr3["quantity"] == 120.0, str(petr3))

    # E — Ativo ausente no CSV atualizado
    test("E1 - BTC ausente do CSV atualizado", not any(r["ticker"] == "BTC" for r in rows3))
    test("E2 - MXRF11 ausente do CSV atualizado", not any(r["ticker"] == "MXRF11" for r in rows3))

    # G — Nome de arquivo nao afeta resultado
    test("G1 - Parser nao recebe filename (independe do nome)", True)

    # H — Apenas colunas obrigatorias
    parser3 = MyProfitParser(ATIVOS_CSV_ONLY_REQUIRED)
    rows4, report4 = parser3.parse_ativos()
    test("H1 - CSV com so Ativo+Qtd aceito", len(report4["errors"]) == 0, str(report4.get("errors")))
    test("H2 - avg_price None quando ausente", all(r["avg_price"] is None for r in rows4))
    test("H3 - sector None quando ausente", all(r["sector"] is None for r in rows4))
    test("H4 - 2 linhas validas", len(rows4) == 2, f"got {len(rows4)}")

    # I — CSV completo com linha de totais
    parser4 = MyProfitParser(ATIVOS_CSV_WITH_TOTAL)
    rows5, report5 = parser4.parse_ativos()
    test("I1 - Linha de totais ignorada", not any("ativos" in (r.get("ticker") or "").lower() for r in rows5))
    test("I2 - 2 ativos validos (sem linha de total)", len(rows5) == 2, f"got {len(rows5)}: {[r['ticker'] for r in rows5]}")
    test("I3 - Warning sobre linha de totais gerado", any("ignorada" in w.lower() for w in report5.get("warnings", [])))

    # J — Valores PT-BR
    parser5 = MyProfitParser(ATIVOS_CSV_PTBR)
    rows6, _ = parser5.parse_ativos()
    btc = next((r for r in rows6 if r["ticker"] == "BTC"), None)
    tesouro = next((r for r in rows6 if "TESOURO" in r["ticker"]), None)
    ivv = next((r for r in rows6 if r["ticker"] == "IVV"), None)
    vxus = next((r for r in rows6 if r["ticker"] == "VXUS"), None)
    test("J1 - BTC qty=0.0014", btc and abs(btc["quantity"] - 0.0014) < 1e-6, str(btc))
    test("J2 - Tesouro qty=0.24", tesouro and abs(tesouro["quantity"] - 0.24) < 1e-6, str(tesouro))
    test("J3 - IVV qty=0.88", ivv and abs(ivv["quantity"] - 0.88) < 1e-6, str(ivv))
    test("J4 - BTC avg_price=468146.30", btc and abs(btc["avg_price"] - 468146.30) < 0.01, str(btc))
    test("J5 - VXUS avg_price=438.49", vxus and abs(vxus["avg_price"] - 438.49) < 0.01, str(vxus))

    # K — Colunas em ordem diferente
    parser6 = MyProfitParser(ATIVOS_CSV_DIFFERENT_ORDER)
    rows7, report7 = parser6.parse_ativos()
    test("K1 - Colunas em ordem diferente aceito", len(report7["errors"]) == 0, str(report7.get("errors")))
    test("K2 - PETR3 qty=100 com colunas embaralhadas", any(r["ticker"] == "PETR3" and r["quantity"] == 100.0 for r in rows7))
    test("K3 - Setor preservado em ordem diferente", any(r["ticker"] == "PETR3" and r["sector"] == "Petroleo" for r in rows7))

    # CSV incompativel rejeitado
    parser7 = MyProfitParser(ATIVOS_CSV_INCOMPATIBLE)
    _, report7b = parser7.parse_ativos()
    test("K4 - CSV de evolucao rejeitado como MYPROFIT_ATIVOS", len(report7b["errors"]) > 0)

    # validate_headers report
    parser8 = MyProfitParser(ATIVOS_CSV)
    report8 = parser8.validate_headers("MYPROFIT_ATIVOS")
    test("K5 - required_columns reportados corretamente", "ativo" in report8["required_columns"])
    test("K6 - sem missing_columns no CSV valido", len(report8["missing_columns"]) == 0)


# --------------------------------------------------------------------------
# TESTES DE PERSISTENCIA (A-L)
# --------------------------------------------------------------------------

async def test_persistence():
    print("\n== PERSISTENCIA - Testes A-L ==\n")

    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.future import select
    from backend.infrastructure.persistence.models.wealth.asset import AssetModel
    from backend.infrastructure.persistence.models.wealth.position_snapshot import PositionSnapshotModel
    from backend.infrastructure.persistence.models.sync_log import SyncLogModel, SyncStatus
    from backend.application.use_cases.confirm_myprofit_ativos import ConfirmMyProfitAtivosSyncUseCase
    from backend.domain.enums.provider_type import ProviderType

    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "fin_analytics.db")
    engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Limpar dados de teste anteriores
    async with AsyncSessionLocal() as session:
        for ticker in ["TEST_PETR3", "TEST_VALE3", "TEST_MXRF11", "TEST_BTC"]:
            result = await session.execute(select(AssetModel).where(AssetModel.ticker == ticker))
            asset = result.scalar_one_or_none()
            if asset:
                snaps = await session.execute(
                    select(PositionSnapshotModel).where(PositionSnapshotModel.asset_id == asset.id)
                )
                for snap in snaps.scalars().all():
                    await session.delete(snap)
                await session.delete(asset)
        await session.commit()
    print("  [INFO] Dados de teste anteriores limpos.\n")

    async def create_sync_log(session, rows, source_type="MYPROFIT_ATIVOS"):
        log = SyncLogModel(
            id=str(uuid.uuid4()),
            user_id="test-user-001",
            provider=ProviderType.MYPROFIT_ATIVOS,
            status=SyncStatus.RUNNING,
            transactions_synced=len(rows),
            start_time=datetime.utcnow(),
            provider_metadata={
                "source_type": source_type,
                "filename": "test.csv",
                "staging_rows": rows,
            }
        )
        session.add(log)
        await session.commit()
        return log.id

    rows_ago = [
        {"ticker": "TEST_PETR3", "quantity": 100.0, "avg_price": 41.33, "sector": "Petroleo"},
        {"ticker": "TEST_VALE3", "quantity": 50.0, "avg_price": 72.12, "sector": "Materiais Basicos"},
        {"ticker": "TEST_MXRF11", "quantity": 552.0, "avg_price": 10.21, "sector": "Papeis"},
    ]
    rows_ago_updated = [
        {"ticker": "TEST_PETR3", "quantity": 120.0, "avg_price": 41.33, "sector": "Petroleo"},
        {"ticker": "TEST_VALE3", "quantity": 50.0, "avg_price": 72.12, "sector": "Materiais Basicos"},
    ]
    rows_set = [
        {"ticker": "TEST_PETR3", "quantity": 120.0, "avg_price": 41.33, "sector": "Petroleo"},
        {"ticker": "TEST_VALE3", "quantity": 55.0, "avg_price": 72.12, "sector": "Materiais Basicos"},
    ]

    # --- Teste A: Primeira importacao ---
    async with AsyncSessionLocal() as session:
        run_id = await create_sync_log(session, rows_ago)
        use_case = ConfirmMyProfitAtivosSyncUseCase(session)
        report = await use_case.execute(run_id, TEST_ACCOUNT_ID, "2026-08-31")

    test("A1 - 3 snapshots inseridos (primeira importacao)", report["snapshots_inserted"] == 3, str(report))
    test("A2 - 0 atualizados", report["snapshots_updated"] == 0)
    test("A3 - assets criados + reutilizados = 3", report["assets_created"] + report["assets_reused"] == 3)

    # --- Teste B: Reimportacao identica ---
    async with AsyncSessionLocal() as session:
        run_id2 = await create_sync_log(session, rows_ago)
        use_case = ConfirmMyProfitAtivosSyncUseCase(session)
        report2 = await use_case.execute(run_id2, TEST_ACCOUNT_ID, "2026-08-31")

    test("B1 - 0 inseridos (reimportacao identica)", report2["snapshots_inserted"] == 0, str(report2))
    test("B2 - 3 atualizados (UPSERT)", report2["snapshots_updated"] == 3)
    test("B3 - 0 assets criados (reutilizados)", report2["assets_created"] == 0)

    # --- Teste C: Alteracao de quantidade ---
    async with AsyncSessionLocal() as session:
        run_id3 = await create_sync_log(session, rows_ago_updated)
        use_case = ConfirmMyProfitAtivosSyncUseCase(session)
        report3 = await use_case.execute(run_id3, TEST_ACCOUNT_ID, "2026-08-31")

    async with AsyncSessionLocal() as session:
        petr3_asset = (await session.execute(select(AssetModel).where(AssetModel.ticker == "TEST_PETR3"))).scalar_one_or_none()
        if petr3_asset:
            snap = (await session.execute(
                select(PositionSnapshotModel).where(
                    PositionSnapshotModel.asset_id == petr3_asset.id,
                    PositionSnapshotModel.account_id == TEST_ACCOUNT_ID,
                    PositionSnapshotModel.reference_date == "2026-08-31",
                )
            )).scalar_one_or_none()
            test("C1 - PETR3 qty atualizado para 120", snap and float(snap.quantity) == 120.0, str(snap and snap.quantity))
        else:
            test("C1 - TEST_PETR3 encontrado", False, "asset nao encontrado")

    # --- Teste D: Nova data nao altera agosto ---
    async with AsyncSessionLocal() as session:
        run_id4 = await create_sync_log(session, rows_set)
        use_case = ConfirmMyProfitAtivosSyncUseCase(session)
        report4 = await use_case.execute(run_id4, TEST_ACCOUNT_ID, "2026-09-30")

    async with AsyncSessionLocal() as session:
        petr3_a = (await session.execute(select(AssetModel).where(AssetModel.ticker == "TEST_PETR3"))).scalar_one_or_none()
        if petr3_a:
            snap_ago = (await session.execute(
                select(PositionSnapshotModel).where(
                    PositionSnapshotModel.asset_id == petr3_a.id,
                    PositionSnapshotModel.account_id == TEST_ACCOUNT_ID,
                    PositionSnapshotModel.reference_date == "2026-08-31",
                )
            )).scalar_one_or_none()
            snap_set = (await session.execute(
                select(PositionSnapshotModel).where(
                    PositionSnapshotModel.asset_id == petr3_a.id,
                    PositionSnapshotModel.account_id == TEST_ACCOUNT_ID,
                    PositionSnapshotModel.reference_date == "2026-09-30",
                )
            )).scalar_one_or_none()
            test("D1 - Snapshot agosto intacto (qty=120)", snap_ago and float(snap_ago.quantity) == 120.0, str(snap_ago and snap_ago.quantity))
            test("D2 - Snapshot setembro criado", snap_set is not None)
            test("D3 - Snapshots de agosto e setembro coexistem", snap_ago is not None and snap_set is not None)

    # --- Teste E: Ativo ausente em setembro nao apaga agosto ---
    async with AsyncSessionLocal() as session:
        mxrf_a = (await session.execute(select(AssetModel).where(AssetModel.ticker == "TEST_MXRF11"))).scalar_one_or_none()
        if mxrf_a:
            snap_mxrf_ago = (await session.execute(
                select(PositionSnapshotModel).where(
                    PositionSnapshotModel.asset_id == mxrf_a.id,
                    PositionSnapshotModel.account_id == TEST_ACCOUNT_ID,
                    PositionSnapshotModel.reference_date == "2026-08-31",
                )
            )).scalar_one_or_none()
            snap_mxrf_set = (await session.execute(
                select(PositionSnapshotModel).where(
                    PositionSnapshotModel.asset_id == mxrf_a.id,
                    PositionSnapshotModel.account_id == TEST_ACCOUNT_ID,
                    PositionSnapshotModel.reference_date == "2026-09-30",
                )
            )).scalar_one_or_none()
            test("E1 - MXRF11 snapshot agosto preservado (ausente em set)", snap_mxrf_ago is not None)
            test("E2 - MXRF11 sem snapshot em setembro (correto)", snap_mxrf_set is None)
        else:
            test("E - TEST_MXRF11 encontrado", False)

    # --- Teste F: Duas contas ---
    async with AsyncSessionLocal() as session:
        run_id5 = await create_sync_log(session, [
            {"ticker": "TEST_PETR3", "quantity": 999.0, "avg_price": 41.33, "sector": "Petroleo"}
        ])
        use_case = ConfirmMyProfitAtivosSyncUseCase(session)
        report5 = await use_case.execute(run_id5, TEST_ACCOUNT_ID_2, "2026-08-31")

    async with AsyncSessionLocal() as session:
        petr3_f = (await session.execute(select(AssetModel).where(AssetModel.ticker == "TEST_PETR3"))).scalar_one_or_none()
        if petr3_f:
            snap_acc1 = (await session.execute(
                select(PositionSnapshotModel).where(
                    PositionSnapshotModel.asset_id == petr3_f.id,
                    PositionSnapshotModel.account_id == TEST_ACCOUNT_ID,
                    PositionSnapshotModel.reference_date == "2026-08-31",
                )
            )).scalar_one_or_none()
            snap_acc2 = (await session.execute(
                select(PositionSnapshotModel).where(
                    PositionSnapshotModel.asset_id == petr3_f.id,
                    PositionSnapshotModel.account_id == TEST_ACCOUNT_ID_2,
                    PositionSnapshotModel.reference_date == "2026-08-31",
                )
            )).scalar_one_or_none()
            test("F1 - Conta A preserva posicao (qty=120)", snap_acc1 and float(snap_acc1.quantity) == 120.0, str(snap_acc1 and snap_acc1.quantity))
            test("F2 - Conta B tem posicao propria (qty=999)", snap_acc2 and float(snap_acc2.quantity) == 999.0, str(snap_acc2 and snap_acc2.quantity))
        else:
            test("F - TEST_PETR3 encontrado", False)

    # --- Teste L: Protecao de edicao manual ---
    async with AsyncSessionLocal() as session:
        petr3_l = (await session.execute(select(AssetModel).where(AssetModel.ticker == "TEST_PETR3"))).scalar_one_or_none()
        if petr3_l:
            snap_l = (await session.execute(
                select(PositionSnapshotModel).where(
                    PositionSnapshotModel.asset_id == petr3_l.id,
                    PositionSnapshotModel.account_id == TEST_ACCOUNT_ID,
                    PositionSnapshotModel.reference_date == "2026-08-31",
                )
            )).scalar_one_or_none()
            if snap_l:
                snap_l.is_manual = 1
                snap_l.quantity = Decimal("999")
                await session.commit()
                print("  [INFO] is_manual=1 e qty=999 setados para TEST_PETR3/agosto")

    # Reimportar com qty diferente — deve preservar
    async with AsyncSessionLocal() as session:
        run_id_l = await create_sync_log(session, [
            {"ticker": "TEST_PETR3", "quantity": 50.0, "avg_price": 41.33, "sector": "Petroleo"}
        ])
        use_case = ConfirmMyProfitAtivosSyncUseCase(session)
        report_l = await use_case.execute(run_id_l, TEST_ACCOUNT_ID, "2026-08-31")

    async with AsyncSessionLocal() as session:
        petr3_lf = (await session.execute(select(AssetModel).where(AssetModel.ticker == "TEST_PETR3"))).scalar_one_or_none()
        if petr3_lf:
            snap_final = (await session.execute(
                select(PositionSnapshotModel).where(
                    PositionSnapshotModel.asset_id == petr3_lf.id,
                    PositionSnapshotModel.account_id == TEST_ACCOUNT_ID,
                    PositionSnapshotModel.reference_date == "2026-08-31",
                )
            )).scalar_one_or_none()
            test("L1 - Posicao manual (qty=999) preservada apos reimportacao", snap_final and float(snap_final.quantity) == 999.0, str(snap_final and snap_final.quantity))
            test("L2 - is_manual permanece 1", snap_final and snap_final.is_manual == 1)
            test("L3 - Relatorio informa preservacao (snapshots_preserved_manual=1)", report_l["snapshots_preserved_manual"] == 1, str(report_l))
            test("L4 - Warning gerado com detalhes", len(report_l.get("row_warnings", [])) > 0)
        else:
            test("L - TEST_PETR3 encontrado", False)


# --------------------------------------------------------------------------
# Execucao
# --------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("FASE 1 - MYPROFIT_ATIVOS - Suite de Testes")
    print("=" * 60)

    test_parser()

    print("\n" + "-" * 60)
    asyncio.run(test_persistence())

    print("\n" + "=" * 60)
    print(f"RESULTADO: {len(PASSED)} passaram, {len(FAILED)} falharam")
    if FAILED:
        print("\nFALHAS:")
        for name, detail in FAILED:
            print(f"   - {name}: {detail}")
    else:
        print("\nTodos os testes passaram!")
    print("=" * 60)

    sys.exit(0 if not FAILED else 1)
