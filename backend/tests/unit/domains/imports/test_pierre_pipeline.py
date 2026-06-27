"""
test_pierre_pipeline.py — Testes unitários completos para o pipeline Pierre TXT.
Cobertura: Validator, Parser (REF-010/REF-011), Normalizer.
"""
import io
import pytest
from datetime import datetime
from decimal import Decimal
from backend.domains.imports.dto import RawDocument, CanonicalFinancialEvent
from backend.domains.imports.validators.pierre_txt import PierreTxtValidator
from backend.domains.imports.parsers.pierre_txt import PierreTxtParser, PierreTxtRowDTO, _is_emoji_only_line
from backend.domains.imports.normalizers.pierre_txt import PierreTxtNormalizer


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_doc(content: list, source: str = "PIERRE_TXT") -> RawDocument:
    return RawDocument(
        source=source,
        filename="test.txt",
        mime_type="text/plain",
        encoding="utf-8",
        parser_version="1.0.0",
        metadata={"total_lines": len(content)},
        content=content,
        document_hash="test-hash",
        created_at=datetime.now(),
    )


def single_block(
    descricao: str = "Compra X",
    categoria: str = "Compras",
    conta: str = "Nubank",
    date_str: str = "01/06/2026",
    amount_str: str = "R$ 50,00",
    emoji: str = "💰",
    extra_cat_lines: list = None,
) -> list:
    """Gera um bloco canônico Pierre TXT."""
    lines = [
        emoji,
        descricao,
        emoji,
        categoria,
    ]
    if extra_cat_lines:
        lines.extend(extra_cat_lines)
    lines += ["", conta, f"{date_str}\t{amount_str}\t"]
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# VALIDADOR
# ─────────────────────────────────────────────────────────────────────────────

class TestPierreTxtValidator:

    def test_validator_success(self):
        v = PierreTxtValidator()
        v.validate(make_doc(single_block()))

    def test_validator_invalid_source(self):
        v = PierreTxtValidator()
        doc = make_doc(single_block(), source="OUTRO")
        with pytest.raises(ValueError, match="Validator incompatível"):
            v.validate(doc)

    def test_validator_empty_content(self):
        v = PierreTxtValidator()
        doc = make_doc([])
        with pytest.raises(ValueError, match="vazio"):
            v.validate(doc)

    def test_validator_no_transactions(self):
        v = PierreTxtValidator()
        doc = make_doc(["DESCRIÇÃO", "DATA", "VALOR", "texto sem data"])
        with pytest.raises(ValueError, match="Nenhuma transação válida"):
            v.validate(doc)

    def test_validator_header_only(self):
        v = PierreTxtValidator()
        doc = make_doc(["DESCRIÇÃO\tCATEGORIA\tCONTA\t", "DATA", "VALOR\t"])
        with pytest.raises(ValueError, match="Nenhuma transação válida"):
            v.validate(doc)

    def test_validator_footer_only(self):
        v = PierreTxtValidator()
        doc = make_doc(["Rodapé do extrato", "Gerado em 01/06/2026"])
        with pytest.raises(ValueError, match="Nenhuma transação válida"):
            v.validate(doc)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER _is_emoji_only_line
# ─────────────────────────────────────────────────────────────────────────────

class TestIsEmojiOnlyLine:

    def test_single_emoji_money(self):
        assert _is_emoji_only_line("💰") is True

    def test_single_emoji_box(self):
        assert _is_emoji_only_line("📦") is True

    def test_emoji_with_variation(self):
        assert _is_emoji_only_line("🍽️") is True

    def test_emoji_bank(self):
        assert _is_emoji_only_line("🏦") is True

    def test_emoji_chart_up(self):
        assert _is_emoji_only_line("📈") is True

    def test_emoji_chart_down(self):
        assert _is_emoji_only_line("📉") is True

    def test_emoji_star(self):
        assert _is_emoji_only_line("⭐") is True

    def test_text_line(self):
        assert _is_emoji_only_line("Compra X") is False

    def test_emoji_plus_text(self):
        assert _is_emoji_only_line("💰 Aplicação") is False

    def test_empty_line(self):
        assert _is_emoji_only_line("") is False

    def test_spaces_only(self):
        assert _is_emoji_only_line("   ") is False


# ─────────────────────────────────────────────────────────────────────────────
# PARSER — Caminho feliz
# ─────────────────────────────────────────────────────────────────────────────

class TestPierreTxtParserHappyPath:

    def _parse(self, block: list) -> list:
        return PierreTxtParser().parse(make_doc(block))

    def test_basic_expense(self):
        rows = self._parse(single_block(amount_str="R$ 100,00"))
        assert len(rows) == 1
        assert rows[0].valor == Decimal("-100.00")
        assert rows[0].descricao == "Compra X"
        assert rows[0].categoria == "Compras"
        assert rows[0].conta == "Nubank"

    def test_positive_income(self):
        rows = self._parse(single_block(amount_str="+R$ 200,00"))
        assert len(rows) == 1
        assert rows[0].valor == Decimal("200.00")

    def test_explicit_negative(self):
        rows = self._parse(single_block(amount_str="-R$ 50,00"))
        assert len(rows) == 1
        assert rows[0].valor == Decimal("-50.00")

    def test_value_zero(self):
        rows = self._parse(single_block(amount_str="R$ 0,00"))
        assert len(rows) == 1
        assert rows[0].valor == Decimal("-0.00")

    def test_large_value_with_thousands(self):
        rows = self._parse(single_block(amount_str="R$ 6.239,68"))
        assert rows[0].valor == Decimal("-6239.68")

    def test_income_with_thousands(self):
        rows = self._parse(single_block(amount_str="+R$ 6.239,68"))
        assert rows[0].valor == Decimal("6239.68")

    def test_date_extracted(self):
        rows = self._parse(single_block(date_str="29/05/2026"))
        assert rows[0].data.strftime("%Y-%m-%d") == "2026-05-29"

    def test_multiple_blocks(self):
        block = (
            single_block(descricao="Desc A", amount_str="R$ 10,00") +
            single_block(descricao="Desc B", amount_str="+R$ 20,00")
        )
        rows = self._parse(block)
        assert len(rows) == 2
        assert rows[0].descricao == "Desc A"
        assert rows[1].descricao == "Desc B"

    # ── Categoria composta ─────────────────────────────────────────────────

    def test_compound_category_two_lines(self):
        block = single_block(
            descricao="Transferência enviada|CLEIDSON",
            categoria="Transferência mesma titularidade",
            extra_cat_lines=["Entre contas"],
        )
        rows = self._parse(block)
        assert len(rows) == 1
        assert rows[0].categoria == "Transferência mesma titularidade | Entre contas"

    def test_compound_category_three_lines(self):
        block = single_block(
            descricao="Pagamento",
            categoria="Cat A",
            extra_cat_lines=["Cat B", "Cat C"],
        )
        rows = self._parse(block)
        assert rows[0].categoria == "Cat A | Cat B | Cat C"

    # ── Variação de emoji ──────────────────────────────────────────────────

    def test_emoji_box(self):
        block = single_block(emoji="📦")
        rows = self._parse(block)
        assert len(rows) == 1
        assert rows[0].descricao == "Compra X"

    def test_emoji_restaurant(self):
        block = single_block(emoji="🍽️")
        rows = self._parse(block)
        assert len(rows) == 1

    def test_emoji_unknown(self):
        block = single_block(emoji="🦄")
        rows = self._parse(block)
        assert len(rows) == 1
        assert rows[0].descricao == "Compra X"

    def test_emoji_bank(self):
        block = single_block(emoji="🏦")
        rows = self._parse(block)
        assert len(rows) == 1

    def test_no_leading_emoji_block(self):
        """Bloco sem emoji no início (padrão Mercadolivre no arquivo real)."""
        block = [
            "",
            "Mercadolivre*Mercadol 6/10",
            "🛍️",
            "Compras online",
            "",
            "Nubank",
            "26/05/2026\tR$ 199,90\t",
        ]
        rows = self._parse(block)
        assert len(rows) == 1
        assert rows[0].descricao == "Mercadolivre*Mercadol 6/10"
        assert rows[0].categoria == "Compras online"

    def test_long_description(self):
        long_desc = "A" * 500
        block = single_block(descricao=long_desc)
        rows = self._parse(block)
        assert len(rows) == 1
        assert rows[0].descricao == long_desc

    def test_no_category(self):
        """Bloco onde apenas descrição existe (sem linha de categoria)."""
        block = [
            "💰",
            "Desc Only",
            "",
            "Nubank",
            "01/06/2026\tR$ 25,00\t",
        ]
        rows = self._parse(block)
        assert len(rows) == 1
        assert rows[0].descricao == "Desc Only"
        assert rows[0].categoria == "Sem categoria"


# ─────────────────────────────────────────────────────────────────────────────
# PARSER — Caminhos inválidos
# ─────────────────────────────────────────────────────────────────────────────

class TestPierreTxtParserInvalidPaths:

    def _parse(self, block: list) -> list:
        return PierreTxtParser().parse(make_doc(block))

    def test_invalid_date(self):
        block = single_block()
        block[-1] = "99/99/9999\tR$ 50,00\t"
        rows = self._parse(block)
        assert len(rows) == 0   # Ignorado com log

    def test_invalid_amount(self):
        block = single_block()
        block[-1] = "01/06/2026\tR$ ABC\t"
        rows = self._parse(block)
        assert len(rows) == 0   # Ignorado com log

    def test_empty_file(self):
        rows = self._parse([])
        assert rows == []

    def test_header_only(self):
        rows = self._parse(["DESCRIÇÃO\tCATEGORIA\tCONTA", "DATA", "VALOR"])
        assert rows == []

    def test_partial_block_no_date(self):
        """Bloco sem linha de data+valor → nenhum evento."""
        rows = self._parse(["💰", "Desc", "💰", "Cat", "", "Nubank"])
        assert rows == []

    def test_line_empty_between_blocks(self):
        """Linhas vazias entre blocos não devem causar erro."""
        block = (
            single_block(descricao="A") +
            ["", "", ""] +
            single_block(descricao="B")
        )
        rows = self._parse(block)
        assert len(rows) == 2


# ─────────────────────────────────────────────────────────────────────────────
# PARSER — Encoding
# ─────────────────────────────────────────────────────────────────────────────

class TestPierreTxtParserEncoding:

    def _parse_from_bytes(self, raw: bytes, enc: str) -> list:
        """Simula o Reader lendo bytes com dado encoding, depois faz parse."""
        lines = raw.decode(enc).splitlines()
        doc = make_doc(lines)
        return PierreTxtParser().parse(doc)

    def _build_raw(self, enc: str, bom: bool = False) -> bytes:
        block_text = "\n".join(single_block())
        encoded = block_text.encode(enc)
        if bom and enc == "utf-8":
            encoded = b'\xef\xbb\xbf' + encoded
        return encoded

    def test_utf8(self):
        rows = self._parse_from_bytes(self._build_raw("utf-8"), "utf-8")
        assert len(rows) == 1

    def test_utf8_bom(self):
        raw = self._build_raw("utf-8", bom=True)
        # Strip BOM manually as a Reader would
        text = raw.decode("utf-8-sig")
        lines = text.splitlines()
        doc = make_doc(lines)
        rows = PierreTxtParser().parse(doc)
        assert len(rows) == 1

    def test_crlf(self):
        block = "\r\n".join(single_block())
        lines = [l.rstrip() for l in block.splitlines()]
        doc = make_doc(lines)
        rows = PierreTxtParser().parse(doc)
        assert len(rows) == 1

    def test_lf_only(self):
        block = "\n".join(single_block())
        lines = [l.rstrip() for l in block.splitlines()]
        doc = make_doc(lines)
        rows = PierreTxtParser().parse(doc)
        assert len(rows) == 1


# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZER
# ─────────────────────────────────────────────────────────────────────────────

class TestPierreTxtNormalizer:

    def _normalize(self, rows: list) -> list:
        return PierreTxtNormalizer().normalize(rows, "hash-test")

    def _row(self, **kwargs) -> PierreTxtRowDTO:
        defaults = dict(
            data=datetime(2026, 6, 1),
            valor=Decimal("100.00"),
            descricao="Compra X",
            categoria="Compras",
            conta="Nubank",
        )
        defaults.update(kwargs)
        return PierreTxtRowDTO(**defaults)

    def test_normalizer_basic(self):
        events = self._normalize([self._row()])
        assert len(events) == 1
        e = events[0]
        assert e.source_system == "PIERRE"
        assert e.source_type == "TXT"
        assert e.amount == Decimal("100.00")
        assert e.account == "Nubank"
        assert e.description == "Compra X | Compras"

    def test_normalizer_uuid_unique(self):
        rows = [self._row(descricao=f"Desc {i}") for i in range(5)]
        events = self._normalize(rows)
        uuids = [e.external_uuid for e in events]
        assert len(set(uuids)) == 5

    def test_normalizer_normalized_desc_transfer_sent(self):
        events = self._normalize([self._row(descricao="Transferência enviada|João")])
        assert events[0].normalized_description == "Transferência Enviada"

    def test_normalizer_normalized_desc_transfer_received(self):
        events = self._normalize([self._row(descricao="Transferência Recebida|Maria")])
        assert events[0].normalized_description == "Transferência Recebida"

    def test_normalizer_generic_desc_unchanged(self):
        events = self._normalize([self._row(descricao="Amazon 6/6")])
        assert events[0].normalized_description == "Amazon 6/6"
