"""DuckDB repository for the wealth-centric domain."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
from pathlib import Path
from typing import Any
from uuid import uuid4

import duckdb

from config.constants import ClasseAtivo, StatusMeta
from config.settings import get_settings
from models.wealth_dto import AssetDTO, BudgetDTO, GoalDTO, PositionDTO


class WealthRepository:
	"""Persist and query the personal-wealth layer in DuckDB."""

	def __init__(
		self,
		database_path: Path | str | None = None,
		*,
		read_only: bool = False,
	) -> None:
		settings = get_settings()
		resolved_path = Path(database_path) if database_path is not None else settings.DATABASE_PATH

		resolved_path.parent.mkdir(parents=True, exist_ok=True)
		self._read_only = read_only
		self._connection: duckdb.DuckDBPyConnection = duckdb.connect(
			database=str(resolved_path),
			read_only=read_only,
		)
		self.init_wealth_tables()

	def close(self) -> None:
		"""Close the underlying DuckDB connection."""

		self._connection.close()

	def init_wealth_tables(self) -> None:
		"""Create the wealth tables if they do not already exist."""

		if self._read_only:
			return

		ddl_statements = (
			"""
			CREATE TABLE IF NOT EXISTS DIM_ASSETS (
				ticker VARCHAR PRIMARY KEY,
				nome VARCHAR NOT NULL,
				classe_ativo VARCHAR NOT NULL,
				setor VARCHAR NOT NULL,
				created_at TIMESTAMP WITH TIME ZONE NOT NULL,
				updated_at TIMESTAMP WITH TIME ZONE NOT NULL
			)
			""",
			"""
			CREATE TABLE IF NOT EXISTS FACT_POSITIONS (
				ticker VARCHAR PRIMARY KEY,
				quantidade DECIMAL(18, 6) NOT NULL,
				preco_medio DECIMAL(18, 6) NOT NULL,
				cotacao_atual DECIMAL(18, 6) NOT NULL,
				pnl_absoluto DECIMAL(18, 6) NOT NULL,
				pnl_percentual DECIMAL(18, 6) NOT NULL,
				dividend_yield DECIMAL(18, 6) NOT NULL,
				updated_at TIMESTAMP WITH TIME ZONE NOT NULL
			)
			""",
			"""
			CREATE TABLE IF NOT EXISTS FINANCIAL_GOALS (
				id_meta VARCHAR PRIMARY KEY,
				nome VARCHAR NOT NULL,
				valor_alvo DECIMAL(18, 2) NOT NULL,
				valor_atual DECIMAL(18, 2) NOT NULL,
				prazo_meses INTEGER NOT NULL,
				aporte_mensal_sugerido DECIMAL(18, 2) NOT NULL,
				percentual_conclusao DECIMAL(18, 2) NOT NULL,
				prioridade INTEGER NOT NULL,
				status VARCHAR NOT NULL,
				updated_at TIMESTAMP WITH TIME ZONE NOT NULL
			)
			""",
			"""
			CREATE TABLE IF NOT EXISTS BUDGETS (
				categoria VARCHAR PRIMARY KEY,
				teto_mensal DECIMAL(18, 2) NOT NULL,
				valor_utilizado DECIMAL(18, 2) NOT NULL,
				percentual_uso DECIMAL(18, 2) NOT NULL,
				status_alerta VARCHAR NOT NULL,
				updated_at TIMESTAMP WITH TIME ZONE NOT NULL
			)
			""",
		)

		for statement in ddl_statements:
			self._connection.execute(statement)

		# Backward-compatible migration for existing legacy tables.
		self._ensure_column("DIM_ASSETS", "nome", "VARCHAR")
		self._ensure_column("DIM_ASSETS", "classe_ativo", "VARCHAR")
		self._ensure_column("DIM_ASSETS", "setor", "VARCHAR")
		self._ensure_column("DIM_ASSETS", "created_at", "TIMESTAMP WITH TIME ZONE")

		self._ensure_column("FINANCIAL_GOALS", "id_meta", "VARCHAR")
		self._ensure_column("FINANCIAL_GOALS", "aporte_mensal_sugerido", "DECIMAL(18, 2)")
		self._ensure_column("FINANCIAL_GOALS", "percentual_conclusao", "DECIMAL(18, 2)")

	def upsert_asset(self, asset: AssetDTO | Mapping[str, Any] | Any) -> None:
		"""Insert or replace asset metadata in ``DIM_ASSETS``."""

		dto = self._coerce_asset(asset)
		data = self._payload_to_dict(asset)
		now = datetime.now(UTC)
		dim_columns = self._table_columns("DIM_ASSETS")

		if {"nome", "classe_ativo", "setor", "created_at"}.issubset(dim_columns):
			self._atomic_replace(
				"DIM_ASSETS",
				"ticker",
				dto.ticker,
				"""
				INSERT INTO DIM_ASSETS (
					ticker,
					nome,
					classe_ativo,
					setor,
					created_at,
					updated_at
				)
				VALUES (?, ?, ?, ?, ?, ?)
				""",
				[
					dto.ticker,
					dto.nome,
					dto.classe_ativo.value,
					dto.setor,
					now,
					now,
				],
			)
			return

		legacy_classe = data.get("classe") or data.get("classe_ativo") or dto.classe_ativo.value
		legacy_quantidade = self._to_decimal(data.get("quantidade", Decimal("0")))
		legacy_preco_medio = self._to_decimal(data.get("preco_medio", Decimal("0")))
		self._atomic_replace(
			"DIM_ASSETS",
			"ticker",
			dto.ticker,
			"""
			INSERT INTO DIM_ASSETS (
				ticker,
				classe,
				quantidade,
				preco_medio,
				updated_at
			)
			VALUES (?, ?, ?, ?, ?)
			""",
			[
				dto.ticker,
				str(legacy_classe),
				legacy_quantidade,
				legacy_preco_medio,
				now,
			],
		)

	def update_position(self, position: PositionDTO | Mapping[str, Any] | Any) -> None:
		"""Insert or replace the current position snapshot for a ticker."""

		dto = self._coerce_position(position)
		now = datetime.now(UTC)
		self._atomic_replace(
			"FACT_POSITIONS",
			"ticker",
			dto.ticker,
			"""
			INSERT INTO FACT_POSITIONS (
				ticker,
				quantidade,
				preco_medio,
				cotacao_atual,
				pnl_absoluto,
				pnl_percentual,
				dividend_yield,
				updated_at
			)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?)
			""",
			[
				dto.ticker,
				dto.quantidade,
				dto.preco_medio,
				dto.cotacao_atual,
				dto.pnl_absoluto,
				dto.pnl_percentual,
				dto.dividend_yield,
				now,
			],
		)

	def upsert_goal(self, goal: GoalDTO | Mapping[str, Any] | Any) -> None:
		"""Insert or replace a financial goal in ``FINANCIAL_GOALS``."""

		dto = self._coerce_goal(goal)
		now = datetime.now(UTC)
		goal_columns = self._table_columns("FINANCIAL_GOALS")

		if "id_meta" not in goal_columns:
			self._atomic_replace(
				"FINANCIAL_GOALS",
				"nome",
				dto.nome,
				"""
				INSERT INTO FINANCIAL_GOALS (
					nome,
					valor_alvo,
					valor_atual,
					prazo_meses,
					prioridade,
					status,
					updated_at
				)
				VALUES (?, ?, ?, ?, ?, ?, ?)
				""",
				[
					dto.nome,
					dto.valor_alvo,
					dto.valor_atual,
					dto.prazo_meses,
					dto.prioridade,
					dto.status,
					now,
				],
			)
			return

		self._atomic_replace(
			"FINANCIAL_GOALS",
			"id_meta",
			dto.id_meta,
			"""
			INSERT INTO FINANCIAL_GOALS (
				id_meta,
				nome,
				valor_alvo,
				valor_atual,
				prazo_meses,
				aporte_mensal_sugerido,
				percentual_conclusao,
				prioridade,
				status,
				updated_at
			)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""",
			[
				dto.id_meta,
				dto.nome,
				dto.valor_alvo,
				dto.valor_atual,
				dto.prazo_meses,
				dto.aporte_mensal_sugerido,
				dto.percentual_conclusao,
				dto.prioridade,
				dto.status,
				now,
			],
		)

	def fetch_all_positions(self) -> list[PositionDTO]:
		"""Return all stored positions as typed DTOs."""

		self.init_wealth_tables()
		rows = self._connection.execute(
			"""
			SELECT ticker, quantidade, preco_medio, cotacao_atual, pnl_absoluto, pnl_percentual, dividend_yield
			FROM FACT_POSITIONS
			ORDER BY ticker
			""",
		).fetchall()
		return [
			PositionDTO(
				ticker=row[0],
				quantidade=row[1],
				preco_medio=row[2],
				cotacao_atual=row[3],
				pnl_absoluto=row[4],
				pnl_percentual=row[5],
				dividend_yield=row[6],
			)
			for row in rows
		]

	def fetch_active_goals(self) -> list[GoalDTO]:
		"""Return goals that are still in progress."""

		self.init_wealth_tables()
		goal_columns = self._table_columns("FINANCIAL_GOALS")
		if {"id_meta", "aporte_mensal_sugerido", "percentual_conclusao"}.issubset(goal_columns):
			rows = self._connection.execute(
				"""
				SELECT id_meta, nome, valor_alvo, valor_atual, prazo_meses, aporte_mensal_sugerido,
				       percentual_conclusao, prioridade, status
				FROM FINANCIAL_GOALS
				WHERE COALESCE(percentual_conclusao, 0) < 100
				ORDER BY prioridade ASC, prazo_meses ASC, nome
				""",
			).fetchall()
		else:
			rows = self._connection.execute(
				"""
				SELECT nome, valor_alvo, valor_atual, prazo_meses, prioridade, status
				FROM FINANCIAL_GOALS
				WHERE COALESCE(status, 'ATIVA') <> 'CONCLUIDA'
				ORDER BY prioridade ASC, prazo_meses ASC, nome
				""",
			).fetchall()
			return [
				GoalDTO(
					id_meta=self._build_goal_id(str(row[0])),
					nome=row[0],
					valor_alvo=row[1],
					valor_atual=row[2],
					prazo_meses=row[3],
					aporte_mensal_sugerido=Decimal("0"),
					percentual_conclusao=(
						(min((self._to_decimal(row[2]) / self._to_decimal(row[1])) * Decimal("100"), Decimal("100"))
						if self._to_decimal(row[1]) > 0
						else Decimal("0"))
					),
					prioridade=row[4],
					status=row[5],
				)
				for row in rows
			]

		return [
			GoalDTO(
				id_meta=row[0],
				nome=row[1],
				valor_alvo=row[2],
				valor_atual=row[3],
				prazo_meses=row[4],
				aporte_mensal_sugerido=row[5],
				percentual_conclusao=row[6],
				prioridade=row[7],
				status=row[8],
			)
			for row in rows
		]

	def fetch_budgets(self) -> list[BudgetDTO]:
		"""Return all configured budgets as typed DTOs."""

		self.init_wealth_tables()
		rows = self._connection.execute(
			"""
			SELECT categoria, teto_mensal, valor_utilizado, percentual_uso, status_alerta
			FROM BUDGETS
			ORDER BY categoria
			""",
		).fetchall()
		return [
			BudgetDTO(
				categoria=row[0],
				teto_mensal=row[1],
				valor_utilizado=row[2],
				percentual_uso=row[3],
				status_alerta=row[4],
			)
			for row in rows
		]

	def fetch_portfolio(self) -> list[dict[str, Any]]:
		"""Compatibility alias returning the legacy portfolio shape."""

		self.init_wealth_tables()
		dim_columns = self._table_columns("DIM_ASSETS")
		class_column = "a.classe_ativo" if "classe_ativo" in dim_columns else "a.classe"
		rows = self._connection.execute(
			f"""
			SELECT p.ticker, {class_column}, p.quantidade, p.preco_medio
			FROM FACT_POSITIONS p
			LEFT JOIN DIM_ASSETS a ON a.ticker = p.ticker
			ORDER BY p.ticker
			""",
		).fetchall()
		return [
			{
				"ticker": row[0],
				"classe": self._coerce_classe(row[1]),
				"quantidade": row[2],
				"preco_medio": row[3],
			}
			for row in rows
		]

	def fetch_goals(self) -> list[dict[str, Any]]:
		"""Compatibility alias returning the legacy goal shape."""

		self.init_wealth_tables()
		goal_columns = self._table_columns("FINANCIAL_GOALS")
		if {"id_meta", "aporte_mensal_sugerido", "percentual_conclusao"}.issubset(goal_columns):
			rows = self._connection.execute(
				"""
				SELECT id_meta, nome, valor_alvo, valor_atual, prazo_meses, aporte_mensal_sugerido,
				       percentual_conclusao, prioridade, status, updated_at
				FROM FINANCIAL_GOALS
				ORDER BY prioridade ASC, prazo_meses ASC, nome
				""",
			).fetchall()
			return [
				{
					"id_meta": row[0],
					"nome": row[1],
					"valor_alvo": row[2],
					"valor_atual": row[3],
					"prazo_meses": row[4],
					"aporte_mensal_sugerido": row[5],
					"percentual_conclusao": row[6],
					"prioridade": row[7],
					"status": self._coerce_status(row[8]),
					"updated_at": row[9],
				}
				for row in rows
			]

		rows = self._connection.execute(
			"""
			SELECT nome, valor_alvo, valor_atual, prazo_meses, prioridade, status, updated_at
			FROM FINANCIAL_GOALS
			ORDER BY prioridade ASC, prazo_meses ASC, nome
			""",
		).fetchall()
		return [
			{
				"id_meta": self._build_goal_id(str(row[0])),
				"nome": row[0],
				"valor_alvo": row[1],
				"valor_atual": row[2],
				"prazo_meses": row[3],
				"aporte_mensal_sugerido": Decimal("0"),
				"percentual_conclusao": (
					(min((self._to_decimal(row[2]) / self._to_decimal(row[1])) * Decimal("100"), Decimal("100"))
					if self._to_decimal(row[1]) > 0
					else Decimal("0"))
				),
				"prioridade": row[4],
				"status": self._coerce_status(row[5]),
				"updated_at": row[6],
			}
			for row in rows
		]

	def _table_columns(self, table_name: str) -> set[str]:
		"""Return a normalized set of available columns for a table."""

		try:
			rows = self._connection.execute(f"PRAGMA table_info('{table_name}')").fetchall()
		except Exception:
			return set()
		return {str(row[1]).strip().lower() for row in rows}

	def _ensure_column(self, table_name: str, column_name: str, column_type: str) -> None:
		"""Add a missing column to an existing table when possible."""

		columns = self._table_columns(table_name)
		if column_name.lower() in columns:
			return
		try:
			self._connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
		except Exception:
			# Keep backward compatibility even when migration cannot be applied.
			return

	def _build_goal_id(self, name: str) -> str:
		"""Build a deterministic domain identifier for legacy goals."""

		normalized = name.strip().lower()
		if not normalized:
			return uuid4().hex
		return hashlib.md5(normalized.encode("utf-8")).hexdigest()

	def _atomic_replace(
		self,
		table_name: str,
		key_column: str,
		key_value: str,
		insert_sql: str,
		params: list[Any],
	) -> None:
		"""Execute a delete+insert cycle inside a transaction."""

		try:
			self._connection.execute("BEGIN TRANSACTION")
			self._connection.execute(f"DELETE FROM {table_name} WHERE {key_column} = ?", [key_value])
			self._connection.execute(insert_sql, params)
			self._connection.execute("COMMIT")
		except Exception as exc:
			try:
				self._connection.execute("ROLLBACK")
			except Exception:
				pass
			raise RuntimeError(f"Failed to persist data into {table_name}.") from exc

	def _coerce_asset(self, asset: AssetDTO | Mapping[str, Any] | Any) -> AssetDTO:
		"""Normalize an asset payload into ``AssetDTO``."""

		data = self._payload_to_dict(asset)
		data.setdefault("nome", data.get("ticker", "").strip() if isinstance(data.get("ticker"), str) else data.get("ticker", ""))
		data.setdefault("setor", "NAO_INFORMADO")
		if "classe_ativo" not in data and "classe" in data:
			data["classe_ativo"] = data.pop("classe")
		return asset if isinstance(asset, AssetDTO) else AssetDTO.model_validate(data)

	def _coerce_position(self, position: PositionDTO | Mapping[str, Any] | Any) -> PositionDTO:
		"""Normalize a position payload into ``PositionDTO``."""

		data = self._payload_to_dict(position)
		data.setdefault("cotacao_atual", data.get("preco_medio", 0))
		data.setdefault("pnl_absoluto", Decimal("0"))
		data.setdefault("pnl_percentual", Decimal("0"))
		data.setdefault("dividend_yield", Decimal("0"))
		return position if isinstance(position, PositionDTO) else PositionDTO.model_validate(data)

	def _coerce_goal(self, goal: GoalDTO | Mapping[str, Any] | Any) -> GoalDTO:
		"""Normalize a goal payload into ``GoalDTO``."""

		data = self._payload_to_dict(goal)
		nome = str(data.get("nome", "")).strip()
		valor_alvo = self._to_decimal(data.get("valor_alvo"))
		valor_atual = self._to_decimal(data.get("valor_atual", 0))
		prazo_meses = int(data.get("prazo_meses") or 0)
		percentual_conclusao = data.get("percentual_conclusao")
		aporte_mensal_sugerido = data.get("aporte_mensal_sugerido")

		if percentual_conclusao is None:
			percentual_conclusao = (
				(min((valor_atual / valor_alvo) * Decimal("100"), Decimal("100")) if valor_alvo > 0 else Decimal("0"))
			)
		else:
			percentual_conclusao = self._to_decimal(percentual_conclusao)

		if aporte_mensal_sugerido is None:
			valor_restante = max(valor_alvo - valor_atual, Decimal("0"))
			aporte_mensal_sugerido = (
				valor_restante / Decimal(prazo_meses)
				if prazo_meses > 0 and valor_restante > 0
				else Decimal("0")
			)
		else:
			aporte_mensal_sugerido = self._to_decimal(aporte_mensal_sugerido)

		data.setdefault("id_meta", str(data.get("id_meta") or uuid4().hex))
		data["nome"] = nome
		data["valor_alvo"] = valor_alvo
		data["valor_atual"] = valor_atual
		data["prazo_meses"] = prazo_meses
		data["aporte_mensal_sugerido"] = aporte_mensal_sugerido
		data["percentual_conclusao"] = percentual_conclusao
		data.setdefault("prioridade", int(data.get("prioridade") or 1))
		data.setdefault("status", self._derive_goal_status(percentual_conclusao))
		return goal if isinstance(goal, GoalDTO) else GoalDTO.model_validate(data)

	def _coerce_budget(self, budget: BudgetDTO | Mapping[str, Any] | Any) -> BudgetDTO:
		"""Normalize a budget payload into ``BudgetDTO``."""

		data = self._payload_to_dict(budget)
		data.setdefault("valor_utilizado", Decimal("0"))
		data.setdefault("percentual_uso", Decimal("0"))
		data.setdefault("status_alerta", "OK")
		return budget if isinstance(budget, BudgetDTO) else BudgetDTO.model_validate(data)

	def _payload_to_dict(self, payload: Any) -> dict[str, Any]:
		"""Convert mappings and Pydantic-like objects into a mutable dictionary."""

		if isinstance(payload, Mapping):
			return dict(payload)
		if hasattr(payload, "model_dump"):
			return dict(payload.model_dump())

		data: dict[str, Any] = {}
		for field_name in (
			"ticker",
			"nome",
			"classe_ativo",
			"classe",
			"setor",
			"quantidade",
			"preco_medio",
			"cotacao_atual",
			"pnl_absoluto",
			"pnl_percentual",
			"dividend_yield",
			"id_meta",
			"valor_alvo",
			"valor_atual",
			"prazo_meses",
			"aporte_mensal_sugerido",
			"percentual_conclusao",
			"prioridade",
			"status",
			"categoria",
			"teto_mensal",
			"valor_utilizado",
			"percentual_uso",
			"status_alerta",
		):
			if hasattr(payload, field_name):
				data[field_name] = getattr(payload, field_name)
		return data

	def _to_decimal(self, value: object) -> Decimal:
		"""Convert repository values into ``Decimal`` safely."""

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, str):
			return Decimal(value)
		if isinstance(value, float):
			return Decimal(str(value))
		if value is None:
			return Decimal("0")
		return Decimal(str(value))

	def _coerce_classe(self, value: object) -> ClasseAtivo:
		"""Normalize stored class values to ``ClasseAtivo``."""

		if isinstance(value, ClasseAtivo):
			return value
		if value is None:
			return ClasseAtivo.CAIXA
		try:
			return ClasseAtivo(str(value))
		except Exception:
			return ClasseAtivo.CAIXA

	def _coerce_status(self, value: object) -> StatusMeta:
		"""Normalize stored status values to ``StatusMeta`` when possible."""

		if isinstance(value, StatusMeta):
			return value
		if value is None:
			return StatusMeta.ATIVA
		try:
			return StatusMeta(str(value))
		except Exception:
			return StatusMeta.ATIVA

	def _derive_goal_status(self, percentual_conclusao: Decimal) -> str:
		"""Derive a goal lifecycle label from completion percentage."""

		return StatusMeta.CONCLUIDA.value if percentual_conclusao >= Decimal("100") else StatusMeta.ATIVA.value