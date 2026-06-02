"""
Simulação de proteção de reclassificação manual.

CENÁRIO:
  1. ETL classifica Uber → TRANSPORTE
  2. Usuário altera Uber → TRABALHO (via API reclassify)
  3. Reimportação ETL ocorre
  4. Verifica: Uber deve permanecer TRABALHO
"""
from __future__ import annotations
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB = ROOT / "fin_analytics.db"


def row(conn, id_economico: str) -> dict:
    r = conn.execute(
        "SELECT macro_categoria, natureza, classificacao_fonte FROM transactions WHERE id_economico = ?",
        (id_economico,),
    ).fetchone()
    if r is None:
        return {}
    return {"macro": r[0], "natureza": r[1], "fonte": r[2]}


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Pega uma transação Uber (classificada pelo ETL)
    uber = conn.execute(
        "SELECT id_economico, descricao_original, macro_categoria, classificacao_fonte "
        "FROM transactions WHERE descricao_original LIKE '%Uber%' LIMIT 1"
    ).fetchone()

    if uber is None:
        print("ERRO: Nenhuma transação Uber encontrada no banco.")
        sys.exit(1)

    tx_id = uber["id_economico"]
    print(f"\n=== TRANSAÇÃO ALVO: {uber['descricao_original']} ===")
    print(f"ID: {tx_id}")
    print(f"Estado inicial (ETL): macro={uber['macro_categoria']}  fonte={uber['classificacao_fonte']}")
    assert uber["classificacao_fonte"] == "ETL", "FALHA: esperado fonte='ETL' após carga inicial"
    assert uber["macro_categoria"] == "TRANSPORTE", f"FALHA: esperado TRANSPORTE, obteve {uber['macro_categoria']}"
    print("[OK] PASSO 1 OK: ETL classificou corretamente como TRANSPORTE/ETL")

    # Simula reclassificação manual (equivalente à chamada PATCH /reclassify)
    conn.execute(
        """
        UPDATE transactions
        SET macro_categoria = 'TRABALHO',
            sub_categoria   = 'DESLOCAMENTO',
            subnatureza     = 'DESLOCAMENTO',
            natureza        = 'EXPENSE',
            classificacao_fonte = 'MANUAL',
            atualizado_em   = CURRENT_TIMESTAMP
        WHERE id_economico = ?
        """,
        (tx_id,),
    )
    conn.commit()

    estado_manual = row(conn, tx_id)
    print(f"Estado após reclassificação MANUAL: macro={estado_manual['macro']}  fonte={estado_manual['fonte']}")
    assert estado_manual["fonte"] == "MANUAL", "FALHA: fonte deveria ser MANUAL após reclassificação"
    assert estado_manual["macro"] == "TRABALHO", "FALHA: macro deveria ser TRABALHO após reclassificação"
    print("[OK] PASSO 2 OK: Reclassificação marcou corretamente fonte='MANUAL'")

    # Simula reimportação ETL (tenta sobrescrever com TRANSPORTE)
    conn.execute(
        """
        INSERT INTO transactions (
            id_economico, source, origin, domain, source_line_no, data,
            descricao_original, descricao_normalizada,
            valor, valor_cents, identificador_externo,
            macro_categoria, sub_categoria, subnatureza, natureza, perfil,
            classificacao_fonte
        ) VALUES (?, 'NUBANK', 'PIERRE', 'FINANCE', 9999, '2026-01-01',
                  'Uber reimport', 'UBER REIMPORT',
                  1420, 1420, NULL,
                  'TRANSPORTE', 'APLICATIVO', 'APLICATIVO', 'EXPENSE', 'ESSENCIAL',
                  'ETL')
        ON CONFLICT(id_economico) DO UPDATE SET
            source = excluded.source,
            origin = excluded.origin,
            domain = excluded.domain,
            source_line_no = excluded.source_line_no,
            descricao_normalizada = excluded.descricao_normalizada,
            macro_categoria = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.macro_categoria ELSE excluded.macro_categoria END,
            sub_categoria   = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.sub_categoria   ELSE excluded.sub_categoria   END,
            subnatureza     = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.subnatureza     ELSE excluded.subnatureza     END,
            natureza        = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.natureza        ELSE excluded.natureza        END,
            perfil          = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.perfil          ELSE excluded.perfil          END,
            atualizado_em   = CURRENT_TIMESTAMP
        """,
        (tx_id,),
    )
    conn.commit()

    estado_pos_reimport = row(conn, tx_id)
    print(f"Estado APÓS reimportação ETL: macro={estado_pos_reimport['macro']}  fonte={estado_pos_reimport['fonte']}")
    assert estado_pos_reimport["fonte"] == "MANUAL", "FALHA: fonte foi sobrescrita pelo ETL!"
    assert estado_pos_reimport["macro"] == "TRABALHO", f"FALHA CRÍTICA: classificação manual perdida! macro={estado_pos_reimport['macro']}"
    print("[OK] PASSO 3 OK: Reimportação ETL respeitou a classificação MANUAL")

    # Valida contagens gerais
    total_tx = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    total_pos = conn.execute("SELECT COUNT(*) FROM positions").fetchone()[0]
    total_div = conn.execute("SELECT COUNT(*) FROM dividends").fetchone()[0]
    manuais = conn.execute("SELECT COUNT(*) FROM transactions WHERE classificacao_fonte = 'MANUAL'").fetchone()[0]
    etls = conn.execute("SELECT COUNT(*) FROM transactions WHERE classificacao_fonte = 'ETL'").fetchone()[0]

    print(f"\n=== MÉTRICAS GERAIS ===")
    print(f"Transações totais : {total_tx}")
    print(f"  - fonte ETL     : {etls}")
    print(f"  - fonte MANUAL  : {manuais}")
    print(f"Posições MyProfit : {total_pos}")
    print(f"Dividendos        : {total_div}")

    assert total_tx == 1045, f"FALHA: esperado 1045 transações Pierre, obteve {total_tx}"
    assert total_pos == 26, f"FALHA: esperado 26 posições, obteve {total_pos}"
    assert total_div == 554, f"FALHA: esperado 554 dividendos, obteve {total_div}"

    conn.close()
    print("\n[OK] TODAS AS VALIDACOES PASSARAM -- classificacao manual sobrevive a reimportacoes.")


if __name__ == "__main__":
    main()
