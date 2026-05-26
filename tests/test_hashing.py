from __future__ import annotations

from utils.hashing import generate_canonical_transaction_hash


def test_canonical_hash_prefers_external_reference() -> None:
	first = generate_canonical_transaction_hash(
		data_iso="2026-01-10",
		valor_abs="100.00",
		descricao_normalizada="pix recebido",
		account_id="conta-principal",
		external_reference="txn-123",
		fallback_seed="origem|arquivo|1",
	)
	second = generate_canonical_transaction_hash(
		data_iso="2026-01-10",
		valor_abs="100.00",
		descricao_normalizada="pix recebido",
		account_id="conta-principal",
		external_reference="txn-123",
		fallback_seed="origem|arquivo|999",
	)

	assert first == second


def test_canonical_hash_uses_fallback_when_reference_missing() -> None:
	first = generate_canonical_transaction_hash(
		data_iso="2026-01-10",
		valor_abs="100.00",
		descricao_normalizada="pix recebido",
		account_id="conta-principal",
		external_reference="",
		fallback_seed="origem|arquivo|1",
	)
	second = generate_canonical_transaction_hash(
		data_iso="2026-01-10",
		valor_abs="100.00",
		descricao_normalizada="pix recebido",
		account_id="conta-principal",
		external_reference="",
		fallback_seed="origem|arquivo|2",
	)

	assert first != second
