"""DuckDB repository for the wealth-centric domain."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, date, datetime
from decimal import Decimal
import hashlib
from pathlib import Path
from typing import Any
from uuid import uuid4

import duckdb

from config.constants import ClasseAtivo, StatusMeta
from config.settings import get_settings
from models.wealth_dto import AssetDTO, BudgetDTO, GoalDTO, PositionDTO as LegacyPositionDTO
from models.wealth_schemas import CategoriaDimDTO, FinancialGoalDTO, PositionDTO as WealthPositionDTO


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
			CREATE TABLE IF NOT EXISTS DIM_CATEGORIAS (
				id VARCHAR PRIMARY KEY,
				macro_categoria VARCHAR NOT NULL,
				subcategoria VARCHAR NOT NULL,
				tipo_financeiro VARCHAR NOT NULL,
				esencialidade VARCHAR NOT NULL,
				cor_dashboard VARCHAR NOT NULL,
				icone VARCHAR NOT NULL,
				budget_default DECIMAL(18, 2) NOT NULL,
				created_at TIMESTAMP WITH TIME ZONE NOT NULL,
				updated_at TIMESTAMP WITH TIME ZONE NOT NULL
			)
			""",
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
				goal_id VARCHAR PRIMARY KEY,
				id_meta VARCHAR,
				nome VARCHAR NOT NULL,
				tipo VARCHAR NOT NULL,
				valor_meta DECIMAL(18, 2) NOT NULL,
				valor_alvo DECIMAL(18, 2) NOT NULL,
				valor_atual DECIMAL(18, 2) NOT NULL,
				data_limite DATE,
				prazo_meses INTEGER NOT NULL,
				prioridade INTEGER NOT NULL,
				categoria_relacionada VARCHAR,
				aporte_mensal_planejado DECIMAL(18, 2) NOT NULL,
				aporte_mensal_sugerido DECIMAL(18, 2) NOT NULL,
				percentual_conclusao DECIMAL(18, 2) NOT NULL,
				status VARCHAR NOT NULL,
				updated_at TIMESTAMP WITH TIME ZONE NOT NULL
			)
			""",
			"""
			CREATE TABLE IF NOT EXISTS DIM_POSITIONS (
				ticker VARCHAR PRIMARY KEY,
				quantidade DECIMAL(18, 6) NOT NULL,
				preco_medio DECIMAL(18, 6) NOT NULL,
				classe_ativo VARCHAR NOT NULL,
				corretora VARCHAR NOT NULL,
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

		self._ensure_column("DIM_CATEGORIAS", "budget_default", "DECIMAL(18, 2)")
		self._ensure_column("DIM_CATEGORIAS", "created_at", "TIMESTAMP WITH TIME ZONE")
		self._ensure_column("DIM_CATEGORIAS", "updated_at", "TIMESTAMP WITH TIME ZONE")

		self._ensure_column("DIM_POSITIONS", "classe_ativo", "VARCHAR")
		self._ensure_column("DIM_POSITIONS", "corretora", "VARCHAR")
		self._ensure_column("DIM_POSITIONS", "updated_at", "TIMESTAMP WITH TIME ZONE")

		self._ensure_column("FINANCIAL_GOALS", "id_meta", "VARCHAR")
		self._ensure_column("FINANCIAL_GOALS", "goal_id", "VARCHAR")
		self._ensure_column("FINANCIAL_GOALS", "tipo", "VARCHAR")
		self._ensure_column("FINANCIAL_GOALS", "valor_meta", "DECIMAL(18, 2)")
		self._ensure_column("FINANCIAL_GOALS", "data_limite", "DATE")
		self._ensure_column("FINANCIAL_GOALS", "categoria_relacionada", "VARCHAR")
		self._ensure_column("FINANCIAL_GOALS", "aporte_mensal_planejado", "DECIMAL(18, 2)")
		self._ensure_column("FINANCIAL_GOALS", "aporte_mensal_sugerido", "DECIMAL(18, 2)")
		self._ensure_column("FINANCIAL_GOALS", "percentual_conclusao", "DECIMAL(18, 2)")

		self.seed_default_categories()

	def seed_default_categories(self) -> None:
		"""Seed a mature category taxonomy when ``DIM_CATEGORIAS`` is empty."""

		if self._read_only:
			return

		row = self._connection.execute("SELECT COUNT(*) FROM DIM_CATEGORIAS").fetchone()
		if row and int(row[0] or 0) > 0:
			return

		defaults = (
			{
				"macro_categoria": "MORADIA",
				"subcategoria": "ALUGUEL",
				"tipo_financeiro": "FIXO",
				"essencialidade": "ESSENCIAL",
				"cor_dashboard": "#7C4DFF",
				"icone": "house",
				"budget_default": Decimal("0"),
			},
			{
				"macro_categoria": "MORADIA",
				"subcategoria": "CONDOMINIO",
				"tipo_financeiro": "FIXO",
				"essencialidade": "ESSENCIAL",
				"cor_dashboard": "#7C4DFF",
				"icone": "building",
				"budget_default": Decimal("0"),
			},
			{
				"macro_categoria": "TRANSPORTE",
				"subcategoria": "UBER",
				"tipo_financeiro": "VARIAVEL",
				"essencialidade": "DISCRICIONARIO",
				"cor_dashboard": "#00B8D9",
				"icone": "car",
				"budget_default": Decimal("0"),
			},
			{
				"macro_categoria": "TRANSPORTE",
				"subcategoria": "GASOLINA",
				"tipo_financeiro": "VARIAVEL",
				"essencialidade": "ESSENCIAL",
				"cor_dashboard": "#00B8D9",
				"icone": "fuel",
				"budget_default": Decimal("0"),
			},
			{
				"macro_categoria": "ALIMENTACAO",
				"subcategoria": "SUPERMERCADO",
				"tipo_financeiro": "VARIAVEL",
				"essencialidade": "ESSENCIAL",
				"cor_dashboard": "#FFB020",
				"icone": "basket",
				"budget_default": Decimal("0"),
			},
			{
				"macro_categoria": "ALIMENTACAO",
				"subcategoria": "IFOOD",
				"tipo_financeiro": "VARIAVEL",
				"essencialidade": "DISCRICIONARIO",
				"cor_dashboard": "#FFB020",
				"icone": "utensils",
				"budget_default": Decimal("0"),
			},
			{
				"macro_categoria": "SAUDE",
				"subcategoria": "FARMACIA",
				"tipo_financeiro": "VARIAVEL",
				"essencialidade": "ESSENCIAL",
				"cor_dashboard": "#2EC4B6",
				"icone": "medical",
				"budget_default": Decimal("0"),
			},
			{
				"macro_categoria": "LAZER",
				"subcategoria": "STREAMING",
				"tipo_financeiro": "RECORRENTE",
				"essencialidade": "DISCRICIONARIO",
				"cor_dashboard": "#FF6B6B",
				"icone": "tv",
				"budget_default": Decimal("0"),
			},
			{
				"macro_categoria": "ASSINATURAS",
				"subcategoria": "SOFTWARE",
				"tipo_financeiro": "RECORRENTE",
				"essencialidade": "DISCRICIONARIO",
				"cor_dashboard": "#9B5DE5",
				"icone": "subscription",
				"budget_default": Decimal("0"),
			},
			{
				"macro_categoria": "INVESTIMENTOS",
				"subcategoria": "APORTE",
				"tipo_financeiro": "FIXO",
				"essencialidade": "ESSENCIAL",
				"cor_dashboard": "#06D6A0",
				"icone": "chart-line",
				"budget_default": Decimal("0"),
			},
		)

		for category in defaults:
			self.upsert_category(category)

	def upsert_category(self, category: CategoriaDimDTO | Mapping[str, Any] | Any) -> None:
		"""Insert or replace a category row in ``DIM_CATEGORIAS``."""

		if self._read_only:
			return

		dto = self._coerce_category(category)
		now = datetime.now(UTC)
		self._atomic_replace(
			"DIM_CATEGORIAS",
			"id",
			dto.id,
			"""
			INSERT INTO DIM_CATEGORIAS (
				id,
				macro_categoria,
				subcategoria,
				tipo_financeiro,
				esencialidade,
				cor_dashboard,
				icone,
				budget_default,
				created_at,
				updated_at
			)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""",
			[
				dto.id,
				dto.macro_categoria,
				dto.subcategoria,
				dto.tipo_financeiro,
				dto.essencialidade,
				dto.cor_dashboard,
				dto.icone,
				dto.budget_default,
				now,
				now,
			],
		)

	def fetch_categories(self) -> list[CategoriaDimDTO]:
		"""Return the category dimension as typed DTOs."""

		self.init_wealth_tables()
		rows = self._connection.execute(
			"""
			SELECT id, macro_categoria, subcategoria, tipo_financeiro, essencialidade, cor_dashboard, icone, budget_default
			FROM DIM_CATEGORIAS
			ORDER BY macro_categoria, subcategoria
			""",
		).fetchall()
		return [
			CategoriaDimDTO(
				id=row[0],
				macro_categoria=row[1],
				subcategoria=row[2],
				tipo_financeiro=row[3],
				esencialidade=row[4],
				cor_dashboard=row[5],
				icone=row[6],
				budget_default=row[7],
			)
			for row in rows
		]

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

	def update_position(self, position: LegacyPositionDTO | Mapping[str, Any] | Any) -> None:
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

	def upsert_position_dimension(self, position: WealthPositionDTO | Mapping[str, Any] | Any) -> None:
		"""Insert or replace the portfolio dimension row in ``DIM_POSITIONS``."""

		dto = self._coerce_position_dimension(position)
		now = datetime.now(UTC)
		self._atomic_replace(
			"DIM_POSITIONS",
			"ticker",
			dto.ticker,
			"""
			INSERT INTO DIM_POSITIONS (
				ticker,
				quantidade,
				preco_medio,
				classe_ativo,
				corretora,
				updated_at
			)
			VALUES (?, ?, ?, ?, ?, ?)
			""",
			[
				dto.ticker,
				dto.quantidade,
				dto.preco_medio,
				dto.classe_ativo,
				dto.corretora,
				now,
			],
		)

	def upsert_goal(self, goal: FinancialGoalDTO | GoalDTO | Mapping[str, Any] | Any) -> None:
		"""Insert or replace a financial goal in ``FINANCIAL_GOALS``."""

		payload = self._normalize_goal_payload(goal)
		now = datetime.now(UTC)
		try:
			self._connection.execute("BEGIN TRANSACTION")
			self._connection.execute(
				"""
				DELETE FROM FINANCIAL_GOALS
				WHERE goal_id = ? OR id_meta = ? OR nome = ?
				""",
				[payload["goal_id"], payload["id_meta"], payload["nome"]],
			)
			self._connection.execute(
				"""
				INSERT INTO FINANCIAL_GOALS (
					goal_id,
					id_meta,
					nome,
					tipo,
					valor_meta,
					valor_alvo,
					valor_atual,
					data_limite,
					prazo_meses,
					prioridade,
					categoria_relacionada,
					aporte_mensal_planejado,
					aporte_mensal_sugerido,
					percentual_conclusao,
					status,
					updated_at
				)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				[
					payload["goal_id"],
					payload["id_meta"],
					payload["nome"],
					payload["tipo"],
					payload["valor_meta"],
					payload["valor_alvo"],
					payload["valor_atual"],
					payload["data_limite"],
					payload["prazo_meses"],
					payload["prioridade"],
					payload["categoria_relacionada"],
					payload["aporte_mensal_planejado"],
					payload["aporte_mensal_sugerido"],
					payload["percentual_conclusao"],
					payload["status"],
					now,
				],
			)
			self._connection.execute("COMMIT")
		except Exception as exc:
			try:
				self._connection.execute("ROLLBACK")
			except Exception:
				pass
			raise RuntimeError("Failed to persist data into FINANCIAL_GOALS.") from exc

	def update_goal_progress(self, goal_id: str, valor_atual: Decimal) -> None:
		"""Update the current progress of a goal and refresh its status."""

		if self._read_only:
			return

		goal_row = self._connection.execute(
			"""
			SELECT goal_id, id_meta, nome, tipo, valor_meta, valor_alvo, data_limite, prioridade, categoria_relacionada
			FROM FINANCIAL_GOALS
			WHERE goal_id = ? OR id_meta = ? OR nome = ?
			LIMIT 1
			""",
			[goal_id, goal_id, goal_id],
		).fetchone()
		if goal_row is None:
			raise KeyError(f"Goal not found: {goal_id}")

		current_value = self._to_decimal(valor_atual)
		baseline = self._to_decimal(goal_row[4] if goal_row[4] is not None else goal_row[5])
		percentual = min((current_value / baseline) * Decimal("100"), Decimal("100")) if baseline > 0 else Decimal("0")
		status = StatusMeta.CONCLUIDA.value if percentual >= Decimal("100") else StatusMeta.ATIVA.value
		now = datetime.now(UTC)

		try:
			self._connection.execute("BEGIN TRANSACTION")
			self._connection.execute(
				"""
				UPDATE FINANCIAL_GOALS
				SET valor_atual = ?,
					percentual_conclusao = ?,
					status = ?,
					updated_at = ?
				WHERE goal_id = ? OR id_meta = ? OR nome = ?
				""",
				[current_value, percentual, status, now, goal_id, goal_id, goal_id],
			)
			self._connection.execute("COMMIT")
		except Exception as exc:
			try:
				self._connection.execute("ROLLBACK")
			except Exception:
				pass
			raise RuntimeError("Failed to update goal progress.") from exc

	def fetch_all_positions(self) -> list[LegacyPositionDTO]:
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
			LegacyPositionDTO(
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
		records = self._fetch_goal_records(active_only=True)
		return [
			GoalDTO.model_validate(
				{
					"id_meta": record["id_meta"],
					"nome": record["nome"],
					"valor_alvo": record["valor_alvo"],
					"valor_atual": record["valor_atual"],
					"prazo_meses": record["prazo_meses"],
					"aporte_mensal_sugerido": record["aporte_mensal_sugerido"],
					"percentual_conclusao": record["percentual_conclusao"],
					"prioridade": record["prioridade"],
					"status": record["status"],
				},
			)
			for record in records
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
		return self._fetch_goal_records(active_only=False)

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

	def _coerce_position(self, position: LegacyPositionDTO | Mapping[str, Any] | Any) -> LegacyPositionDTO:
		"""Normalize a position payload into ``PositionDTO``."""

		data = self._payload_to_dict(position)
		data.setdefault("cotacao_atual", data.get("preco_medio", 0))
		data.setdefault("pnl_absoluto", Decimal("0"))
		data.setdefault("pnl_percentual", Decimal("0"))
		data.setdefault("dividend_yield", Decimal("0"))
		return position if isinstance(position, LegacyPositionDTO) else LegacyPositionDTO.model_validate(data)

	def _coerce_position_dimension(self, position: WealthPositionDTO | Mapping[str, Any] | Any) -> WealthPositionDTO:
		"""Normalize a payload into the wealth position dimension DTO."""

		data = self._payload_to_dict(position)
		data.setdefault("corretora", "NAO_INFORMADA")
		data.setdefault("classe_ativo", data.get("classe", "CAIXA"))
		return position if isinstance(position, WealthPositionDTO) else WealthPositionDTO.model_validate(data)

	def _coerce_category(self, category: CategoriaDimDTO | Mapping[str, Any] | Any) -> CategoriaDimDTO:
		"""Normalize a payload into ``CategoriaDimDTO``."""

		data = self._payload_to_dict(category)
		data.setdefault("budget_default", Decimal("0"))
		data.setdefault("cor_dashboard", "#6C7A89")
		data.setdefault("icone", "circle")
		return category if isinstance(category, CategoriaDimDTO) else CategoriaDimDTO.model_validate(data)

	def _normalize_goal_payload(self, goal: FinancialGoalDTO | GoalDTO | Mapping[str, Any] | Any) -> dict[str, Any]:
		"""Normalize financial goal payloads into the new repository shape."""

		data = self._payload_to_dict(goal)
		nome = str(data.get("nome", "")).strip()
		goal_id = str(data.get("goal_id") or data.get("id_meta") or self._build_goal_id(nome or uuid4().hex))
		valor_meta = self._to_decimal(data.get("valor_meta", data.get("valor_alvo", 0)))
		valor_atual = self._to_decimal(data.get("valor_atual", 0))
		prioridade = int(data.get("prioridade") or 1)
		tipo = str(data.get("tipo") or "OUTRA").strip().upper().replace(" ", "_")
		categoria_relacionada = data.get("categoria_relacionada")
		if categoria_relacionada is not None:
			categoria_relacionada = str(categoria_relacionada).strip().upper().replace(" ", "_")

		data_limite = data.get("data_limite")
		prazo_meses = int(data.get("prazo_meses") or 0)
		if data_limite is None and prazo_meses > 0:
			data_limite = self._estimate_goal_deadline(prazo_meses)
		elif data_limite is not None and not isinstance(data_limite, date):
			data_limite = self._coerce_date(data_limite)

		if not prazo_meses and data_limite is not None:
			prazo_meses = self._estimate_months_until(data_limite)

		aporte_planejado = self._to_decimal(data.get("aporte_mensal_planejado", data.get("aporte_mensal_sugerido", 0)))
		percentual_conclusao = data.get("percentual_conclusao")
		if percentual_conclusao is None:
			percentual_conclusao = (
				(min((valor_atual / valor_meta) * Decimal("100"), Decimal("100")) if valor_meta > 0 else Decimal("0"))
			)
		else:
			percentual_conclusao = self._to_decimal(percentual_conclusao)

		status = str(data.get("status") or self._derive_goal_status(self._to_decimal(percentual_conclusao))).strip().upper().replace(" ", "_")

		return {
			"goal_id": goal_id,
			"id_meta": str(data.get("id_meta") or goal_id),
			"nome": nome,
			"tipo": tipo,
			"valor_meta": valor_meta,
			"valor_alvo": valor_meta,
			"valor_atual": valor_atual,
			"data_limite": data_limite,
			"prazo_meses": prazo_meses,
			"prioridade": prioridade,
			"categoria_relacionada": categoria_relacionada,
			"aporte_mensal_planejado": aporte_planejado,
			"aporte_mensal_sugerido": aporte_planejado,
			"percentual_conclusao": self._to_decimal(percentual_conclusao),
			"status": status,
		}

	def _fetch_goal_records(self, active_only: bool = False) -> list[dict[str, Any]]:
		"""Read the goal table using the normalized repository shape."""

		where_clause = "WHERE COALESCE(status, 'ATIVA') <> 'CONCLUIDA'" if active_only else ""
		rows = self._connection.execute(
			f"""
			SELECT
				goal_id,
				id_meta,
				nome,
				tipo,
				valor_meta,
				valor_alvo,
				valor_atual,
				data_limite,
				prazo_meses,
				prioridade,
				categoria_relacionada,
				aporte_mensal_planejado,
				aporte_mensal_sugerido,
				percentual_conclusao,
				status,
				updated_at
			FROM FINANCIAL_GOALS
			{where_clause}
			ORDER BY prioridade ASC, COALESCE(data_limite, DATE '2999-12-31') ASC, nome
			""",
		).fetchall()
		return [self._goal_row_to_record(row) for row in rows]

	def _goal_row_to_record(self, row: tuple[Any, ...]) -> dict[str, Any]:
		"""Convert a DuckDB goal row into the normalized dict shape."""

		goal_id = str(row[0] or row[1] or self._build_goal_id(str(row[2] or "")))
		valor_meta = self._to_decimal(row[4] if row[4] is not None else row[5])
		valor_atual = self._to_decimal(row[6])
		data_limite = row[7]
		prazo_meses = int(row[8] or 0)
		if prazo_meses <= 0 and data_limite is not None:
			prazo_meses = self._estimate_months_until(data_limite)
		aporte_mensal_planejado = self._to_decimal(row[11] if row[11] is not None else row[12])
		percentual_conclusao = self._to_decimal(row[13])
		if percentual_conclusao <= 0 and valor_meta > 0:
			percentual_conclusao = min((valor_atual / valor_meta) * Decimal("100"), Decimal("100"))
		status = self._coerce_status(row[14])

		return {
			"goal_id": goal_id,
			"id_meta": goal_id,
			"nome": row[2],
			"tipo": row[3] or "OUTRA",
			"valor_meta": valor_meta,
			"valor_alvo": valor_meta,
			"valor_atual": valor_atual,
			"data_limite": data_limite,
			"prazo_meses": prazo_meses,
			"prioridade": int(row[9] or 1),
			"categoria_relacionada": row[10],
			"aporte_mensal_planejado": aporte_mensal_planejado,
			"aporte_mensal_sugerido": aporte_mensal_planejado,
			"percentual_conclusao": percentual_conclusao,
			"status": status,
			"updated_at": row[15],
		}

	def _estimate_goal_deadline(self, prazo_meses: int) -> date:
		"""Approximate a deadline date from a month count."""

		anchor = datetime.now(UTC).date()
		year = anchor.year + ((anchor.month - 1 + prazo_meses) // 12)
		month = ((anchor.month - 1 + prazo_meses) % 12) + 1
		day = min(anchor.day, 28)
		return anchor.replace(year=year, month=month, day=day)

	def _estimate_months_until(self, target_date: Any) -> int:
		"""Approximate the number of months until a target date."""

		coerced_date = self._coerce_date(target_date)
		anchor = datetime.now(UTC).date()
		years_delta = coerced_date.year - anchor.year
		months_delta = coerced_date.month - anchor.month
		return max((years_delta * 12) + months_delta, 0)

	def _coerce_date(self, value: Any) -> date:
		"""Normalize database values into ``date`` objects."""

		if isinstance(value, date):
			return value
		if isinstance(value, datetime):
			return value.date()
		if isinstance(value, str):
			return date.fromisoformat(value)
		raise TypeError(f"Cannot coerce {type(value)!r} into a date.")

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