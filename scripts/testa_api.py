from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.main import app


DB_PATH = ROOT / "fin_analytics.db"


def _get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_quarantine_transaction_id() -> str | None:
    with _get_db_connection() as conn:
        row = conn.execute(
            """
            SELECT id_economico
            FROM transactions
            WHERE origin = 'PIERRE'
              AND (COALESCE(macro_categoria, '') = 'OUTROS' OR COALESCE(sub_categoria, '') = 'INDEFINIDO')
            ORDER BY source_line_no ASC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        return str(row["id_economico"])


def main() -> None:
    client = TestClient(app)
    results: list[str] = []
    dashboard_month = "2026-05"

    import_status_response = client.get("/api/v1/governance/import-status")
    results.append(f"GET /governance/import-status -> {import_status_response.status_code}")
    if import_status_response.status_code == 200:
        import_status_payload = import_status_response.json()
        results.append(f"GET /governance/import-status next_line -> {import_status_payload.get('next_line')}")

    import_payload = {
        "raw_text": (
            "Data;Descriçao;Categoria;Conta;Valor\n"
            "29/05/2026;Transferência Recebida|TESTE OPERACIONAL;Transferências;Nubank;R$ 1,00\n"
            "29/05/2026;Valor recebido de Investimentos;Transferências para terceiros;Nubank;R$ 2,00\n"
        )
    }
    import_response = client.post("/api/v1/governance/import-pierre", json=import_payload)
    results.append(f"POST /governance/import-pierre -> {import_response.status_code}")
    if import_response.status_code == 200:
        import_response_payload = import_response.json()
        results.append(f"POST /governance/import-pierre run_id present -> {bool(import_response_payload.get('run_id'))}")

    tx_response = client.get("/api/v1/transactions?limit=5&offset=0")
    results.append(f"GET /transactions -> {tx_response.status_code}")
    tx_payload = tx_response.json()
    first_item_has_id = bool(tx_payload.get("items")) and "id" in tx_payload["items"][0]
    results.append(f"GET /transactions payload id present -> {first_item_has_id}")
    pagination_ok = tx_payload.get("limit") == 5 and tx_payload.get("offset") == 0 and tx_payload.get("total", 0) >= len(tx_payload.get("items", []))
    results.append(f"GET /transactions pagination -> {pagination_ok}")

    quarantine_id = _get_quarantine_transaction_id()
    if quarantine_id:
        patch_response = client.patch(
            f"/api/v1/transactions/{quarantine_id}/reclassify",
            json={"macro_categoria": "SAUDE", "natureza": "EXPENSE", "subnatureza": "GERAL"},
        )
        results.append(f"PATCH /transactions/{{id}}/reclassify -> {patch_response.status_code}")
    else:
        results.append("PATCH /transactions/{id}/reclassify -> skipped (sem quarentena)")

    dashboard_response = client.get("/api/v1/dashboard/summary")
    results.append(f"GET /dashboard/summary -> {dashboard_response.status_code}")

    subscriptions_response = client.get(f"/api/v1/dashboard/subscriptions?month={dashboard_month}")
    results.append(f"GET /dashboard/subscriptions?month={dashboard_month} -> {subscriptions_response.status_code}")
    if subscriptions_response.status_code == 200:
        subscriptions_payload = subscriptions_response.json()
        results.append("GET /dashboard/subscriptions payload ->")
        results.append(json.dumps(subscriptions_payload, ensure_ascii=False, indent=2))

    installments_response = client.get("/api/v1/dashboard/installments")
    results.append("GET /dashboard/installments -> {}".format(installments_response.status_code))
    if installments_response.status_code == 200:
        installments_payload = installments_response.json()
        items = installments_payload.get("items", [])
        active_count = sum(
            1
            for item in items
            if item.get("current_installment", 0) < item.get("total_installments", 0)
        )
        finished_count = sum(
            1
            for item in items
            if item.get("current_installment", 0) >= item.get("total_installments", 0)
        )
        results.append(f"GET /dashboard/installments active_count -> {active_count}")
        results.append(f"GET /dashboard/installments finished_count -> {finished_count}")
        results.append("GET /dashboard/installments payload ->")
        results.append(json.dumps(installments_payload, ensure_ascii=False, indent=2))

    governance_response = client.get("/api/v1/governance/quarantine")
    results.append(f"GET /governance/quarantine -> {governance_response.status_code}")
    governance_count = len(governance_response.json()) if governance_response.status_code == 200 else -1
    results.append(f"GET /governance/quarantine count -> {governance_count}")

    investments_response = client.get("/api/v1/investments/dividends/history")
    results.append(f"GET /investments/dividends/history -> {investments_response.status_code}")

    print("=== API TESTS ===")
    for line in results:
        print(line)

    if quarantine_id:
        with _get_db_connection() as conn:
            updated = conn.execute(
                "SELECT macro_categoria, sub_categoria, natureza FROM transactions WHERE id_economico = ?",
                (quarantine_id,),
            ).fetchone()
            print("PATCH result ->", dict(updated) if updated else None)


if __name__ == "__main__":
    main()