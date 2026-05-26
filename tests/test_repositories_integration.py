from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import duckdb
import polars as pl

from config.constants import StatusProcessamento
from repositories.transacoes_repository import TransacoesRepository
from repositories.wealth_repository import WealthRepository


def _transaction_schema() -> dict[str, pl.DataType]:
	return {
		"ID_Unico": pl.Utf8,
		"Data": pl.Date,
		"Descricao": pl.Utf8,
		"Valor": pl.Decimal(18, 2),
		"Tipo": pl.Utf8,
		"Categoria": pl.Utf8,
		"ArquivoOrigem": pl.Utf8,
		"Fonte": pl.Utf8,
		"processed_at": pl.Utf8,
	}


def _quarantine_schema() -> dict[str, pl.DataType]:
	schema = _transaction_schema()
	schema["motivo_rejeicao"] = pl.Utf8
	return schema


def test_filter_new_records_uses_sql_antijoin(tmp_path: Path) -> None:
	db_path = tmp_path / "integration_dedup.duckdb"
	repository = TransacoesRepository(database_path=db_path)
	repository.init_tables()

	now = datetime.now(UTC).isoformat()
	base_df = pl.DataFrame(
		[
			{
				"ID_Unico": "tx-001",
				"Data": date(2026, 1, 10),
				"Descricao": "mercado",
				"Valor": Decimal("-120.50"),
				"Tipo": "GASTO",
				"Categoria": "ALIMENTACAO",
				"ArquivoOrigem": "extrato.csv",
				"Fonte": "NUBANK",
				"processed_at": now,
			}
		],
		schema=_transaction_schema(),
		orient="row",
	)

	filtered_first = repository.filter_new_records(base_df)
	assert filtered_first.height == 1

	repository.bulk_insert(
		filtered_first,
		pl.DataFrame(schema=_quarantine_schema()),
		{
			"execution_id": "exec-1",
			"started_at": datetime.now(UTC),
			"finished_at": datetime.now(UTC),
			"source_file": "extrato.csv",
			"rows_read": 1,
			"rows_inserted": 1,
			"rows_duplicated": 0,
			"rows_quarantined": 0,
			"status": StatusProcessamento.SUCESSO.value,
			"execution_time_ms": 1,
		},
	)

	filtered_second = repository.filter_new_records(base_df)
	assert filtered_second.is_empty()


def test_promote_quarantine_transaction_moves_row(tmp_path: Path) -> None:
	db_path = tmp_path / "integration_quarantine.duckdb"
	repository = TransacoesRepository(database_path=db_path)
	repository.init_tables()

	now = datetime.now(UTC).isoformat()
	quarantine_df = pl.DataFrame(
		[
			{
				"ID_Unico": "q-001",
				"Data": date(2026, 2, 11),
				"Descricao": "transacao sem categoria",
				"Valor": Decimal("-10.00"),
				"Tipo": "GASTO",
				"Categoria": "NAO_CLASSIFICADO",
				"ArquivoOrigem": "raw.csv",
				"Fonte": "MANUAL",
				"processed_at": now,
				"motivo_rejeicao": "categoria ausente",
			}
		],
		schema=_quarantine_schema(),
		orient="row",
	)

	repository.bulk_insert(
		pl.DataFrame(schema=_transaction_schema()),
		quarantine_df,
		{
			"execution_id": "exec-2",
			"started_at": datetime.now(UTC),
			"finished_at": datetime.now(UTC),
			"source_file": "raw.csv",
			"rows_read": 1,
			"rows_inserted": 0,
			"rows_duplicated": 0,
			"rows_quarantined": 1,
			"status": StatusProcessamento.SUCESSO.value,
			"execution_time_ms": 1,
		},
	)

	repository.promote_quarantine_transaction(
		transaction_id="q-001",
		tipo="GASTO",
		categoria="ALIMENTACAO",
	)

	quarantine_rows = repository.fetch_quarantine_records(limit=10)
	assert quarantine_rows == []

	base_rows = repository.fetch_latest_transactions(10).fetchall()
	assert len(base_rows) == 1
	assert base_rows[0][0] == "q-001"
	assert base_rows[0][5] == "ALIMENTACAO"


def test_wealth_repository_initializes_canonical_tables(tmp_path: Path) -> None:
	db_path = tmp_path / "integration_wealth.duckdb"
	repository = WealthRepository(database_path=db_path)
	repository.init_wealth_tables()
	repository.close()

	connection = duckdb.connect(database=str(db_path), read_only=True)
	try:
		rows = connection.execute(
			"""
			SELECT UPPER(table_name) AS table_name
			FROM information_schema.tables
			WHERE table_schema = 'main'
			"""
		).fetchall()
	finally:
		connection.close()

	table_names = {row[0] for row in rows}
	assert {
		"DIM_ACCOUNTS",
		"DIM_ASSETS",
		"FACT_TRANSACTIONS",
		"FACT_POSITIONS",
		"FACT_CASHFLOW",
		"FACT_DIVIDENDS",
		"FACT_TRANSFERS",
	}.issubset(table_names)
