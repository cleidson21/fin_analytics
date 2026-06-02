from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "ParcelamentosPierre.csv"
DB_PATH = ROOT / "fin_analytics.db"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


HEADER_PREFIXES = ("Estabelecimento;Status;Parcelas",)


@dataclass(frozen=True)
class ParcelRow:
    establishment: str
    status: str
    parcelas: str
    amount: str
    total_or_remaining: str
    card: str

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (
            self.establishment.strip().lower(),
            self.status.strip().lower(),
            self.parcelas.strip().lower(),
            _normalize_money(self.amount),
        )



def _normalize_money(value: str) -> str:
    return value.replace("R$", "").replace(".", "").replace(" ", "").replace(",", ".").strip()



def parse_csv(path: Path) -> list[ParcelRow]:
    rows: list[ParcelRow] = []
    with path.open("r", encoding="cp1252", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        for raw in reader:
            if not raw:
                continue
            first_column = raw[0].strip().lower()
            second_column = raw[1].strip().lower() if len(raw) > 1 else ""
            third_column = raw[2].strip().lower() if len(raw) > 2 else ""
            if first_column == "estabelecimento" and second_column == "status" and third_column == "parcelas":
                continue
            if first_column == "status":
                continue
            if len(raw) < 6:
                continue
            rows.append(
                ParcelRow(
                    establishment=raw[0].strip(),
                    status=raw[1].strip(),
                    parcelas=raw[2].strip(),
                    amount=raw[3].strip(),
                    total_or_remaining=raw[4].strip(),
                    card=raw[5].strip(),
                )
            )
    return rows



def normalize_api_item(item: dict[str, object]) -> tuple[str, str, str, str]:
    return (
        str(item.get("base_name", "")).strip().lower(),
        "ativo" if int(item.get("current_installment", 0)) < int(item.get("total_installments", 0)) else "finalizado",
        f"{int(item.get('current_installment', 0))}/{int(item.get('total_installments', 0))}x",
        f"{Decimal(str(item.get('installment_amount', 0))).quantize(Decimal('0.01')):.2f}",
    )



def main() -> None:
    csv_rows = parse_csv(CSV_PATH)
    print(f"CSV_ROWS: {len(csv_rows)}")
    print(f"CSV_ACTIVE: {sum(1 for row in csv_rows if row.status.lower() == 'ativo')}")
    print(f"CSV_FINISHED: {sum(1 for row in csv_rows if row.status.lower() == 'finalizado')}")

    client = TestClient(app)
    response = client.get("/api/v1/dashboard/installments")
    print(f"API_STATUS: {response.status_code}")
    payload = response.json()
    api_items = payload.get("items", [])
    print(f"API_ACTIVE: {payload.get('active_installments')}")
    print(f"API_FINISHED: {payload.get('finished_installments')}")
    print(f"API_LAST_DATE: {payload.get('last_installment_date')}")

    csv_counter = Counter(row.key for row in csv_rows)
    api_counter = Counter(normalize_api_item(item) for item in api_items)

    csv_keys = set(csv_counter)
    api_keys = set(api_counter)

    missing = sorted(csv_keys - api_keys)
    extra = sorted(api_keys - csv_keys)
    shared = sorted(csv_keys & api_keys)

    print("\nMISSING_GROUPS:")
    for key in missing:
        print("-", key, "x", csv_counter[key])

    print("\nEXTRA_GROUPS:")
    for key in extra:
        print("-", key, "x", api_counter[key])

    print("\nMISMATCHED_COUNTS:")
    for key in shared:
        if csv_counter[key] != api_counter[key]:
            print(f"- {key} csv={csv_counter[key]} api={api_counter[key]}")

    print("\nCSV_SAMPLE:")
    for row in csv_rows[:12]:
        print(f"- {row.establishment} | {row.status} | {row.parcelas} | {row.amount} | {row.total_or_remaining} | {row.card}")

    print("\nAPI_SAMPLE:")
    for item in api_items[:12]:
        print(json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    main()
