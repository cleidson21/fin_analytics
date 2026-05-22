"""Tests for shared utility functions."""

from __future__ import annotations

from utils.hashing import generate_deterministic_hash
from utils.normalization import normalize_text


def test_normalize_text_removes_accents_and_collapses_spaces() -> None:
	assert normalize_text(" Mêrcado  ") == "MERCADO"


def test_normalize_text_removes_special_characters() -> None:
	assert normalize_text("  Pix! cartão-credito / hoje  ") == "PIX CARTAO CREDITO HOJE"


def test_generate_deterministic_hash_is_stable() -> None:
	first = generate_deterministic_hash(
		data_iso="2026-05-22",
		valor_abs="123.45",
		descricao_normalizada="MERCADO",
		fonte="NUBANK",
		nome_arquivo="extrato.csv",
		row_number="7",
	)
	second = generate_deterministic_hash(
		data_iso="2026-05-22",
		valor_abs="123.45",
		descricao_normalizada="MERCADO",
		fonte="NUBANK",
		nome_arquivo="extrato.csv",
		row_number="7",
	)

	assert first == second
	assert len(first) == 64
	assert all(character in "0123456789abcdef" for character in first)


def test_generate_deterministic_hash_produces_distinct_values() -> None:
	hashes = {
		generate_deterministic_hash(
			data_iso="2026-05-22",
			valor_abs="123.45",
			descricao_normalizada="MERCADO",
			fonte="NUBANK",
			nome_arquivo="extrato.csv",
			row_number="7",
		),
		generate_deterministic_hash(
			data_iso="2026-05-22",
			valor_abs="123.45",
			descricao_normalizada="MERCADO",
			fonte="NUBANK",
			nome_arquivo="extrato.csv",
			row_number="8",
		),
		generate_deterministic_hash(
			data_iso="2026-05-23",
			valor_abs="123.45",
			descricao_normalizada="MERCADO",
			fonte="NUBANK",
			nome_arquivo="extrato.csv",
			row_number="7",
		),
		generate_deterministic_hash(
			data_iso="2026-05-22",
			valor_abs="999.99",
			descricao_normalizada="OUTRO",
			fonte="NUBANK",
			nome_arquivo="outro.csv",
			row_number="7",
		),
	}

	assert len(hashes) == 4
