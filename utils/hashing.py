"""Deterministic hashing helpers for transaction identity generation."""

from __future__ import annotations

import hashlib


def generate_deterministic_hash(
	data_iso: str,
	valor_abs: str,
	descricao_normalizada: str,
	fonte: str,
	nome_arquivo: str,
	row_number: str,
) -> str:
	"""Generate a reproducible SHA-256 hash for a transaction-like record.

	The payload is serialized with explicit field labels and separators so that
	different field combinations cannot collapse into the same input string.

	Args:
		data_iso: Date in ISO-8601 format.
		valor_abs: Absolute monetary value represented as a string.
		descricao_normalizada: Normalized transaction description.
		fonte: Data source identifier.
		nome_arquivo: Source file name.
		row_number: Row position in the source file.

	Returns:
		A lowercase hexadecimal SHA-256 digest.
	"""

	payload = "|".join(
		(
			f"data_iso={data_iso}",
			f"valor_abs={valor_abs}",
			f"descricao_normalizada={descricao_normalizada}",
			f"fonte={fonte}",
			f"nome_arquivo={nome_arquivo}",
			f"row_number={row_number}",
		)
	)
	return hashlib.sha256(payload.encode("utf-8")).hexdigest()
