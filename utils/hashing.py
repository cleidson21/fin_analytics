"""Deterministic hashing helpers for transaction identity generation."""

from __future__ import annotations

import hashlib


def generate_canonical_transaction_hash(
	data_iso: str,
	valor_abs: str,
	descricao_normalizada: str,
	account_id: str = "",
	external_reference: str = "",
	fallback_seed: str = "",
) -> str:
	"""Generate a reproducible canonical hash for a financial transaction.

	The canonical identity prioritizes stable economic fields. When an external
	reference is missing, a deterministic fallback seed can be appended.
	"""

	payload_parts = [
		f"data_iso={data_iso}",
		f"valor_abs={valor_abs}",
		f"descricao_normalizada={descricao_normalizada}",
		f"account_id={account_id}",
	]
	if external_reference:
		payload_parts.append(f"external_reference={external_reference}")
	elif fallback_seed:
		payload_parts.append(f"fallback_seed={fallback_seed}")

	payload = "|".join(payload_parts)
	return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_deterministic_hash(
	data_iso: str,
	valor_abs: str,
	descricao_normalizada: str,
	fonte: str,
	nome_arquivo: str,
	row_number: str,
) -> str:
	"""Backward-compatible wrapper around canonical transaction hashing."""

	return generate_canonical_transaction_hash(
		data_iso=data_iso,
		valor_abs=valor_abs,
		descricao_normalizada=descricao_normalizada,
		account_id="",
		external_reference="",
		fallback_seed=f"{fonte}|{nome_arquivo}|{row_number}",
	)
