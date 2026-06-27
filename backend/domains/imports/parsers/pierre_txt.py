import re
import unicodedata
import logging
from typing import List, Tuple, Optional
from pydantic import BaseModel
from decimal import Decimal, InvalidOperation
from datetime import datetime
from backend.domains.imports.dto import RawDocument

logger = logging.getLogger(__name__)

# Regex para detectar a linha de data+valor que encerra cada bloco
_DATE_VALUE_RE = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(.+)$')

# Regex para extrair valor monetário (aceita qualquer separador de milhar e decimal BR)
_AMOUNT_RE = re.compile(r'[\d]+(?:[.,]\d+)*')


def _is_emoji_only_line(text: str) -> bool:
    """
    Retorna True se a linha for composta exclusivamente por
    caracteres emoji / símbolos Unicode (sem letras, dígitos ou pontuação latina).
    Robusto a qualquer emoji presente ou futuro.
    """
    stripped = text.strip()
    if not stripped:
        return False
    for ch in stripped:
        cat = unicodedata.category(ch)
        # Letras (L*), Dígitos (N*), Pontuação (P*), Símbolos ASCII (Sm, Sc) → não é emoji puro
        if cat.startswith(('L', 'N', 'P')):
            return False
        # Sm = Math symbol, Sc = Currency symbol (like $) → não é emoji puro
        if cat in ('Sm', 'Sc'):
            return False
    return True


def _parse_amount(val_raw: str) -> Tuple[Optional[Decimal], bool]:
    """
    Converte string de valor monetário para Decimal.
    Retorna (valor, is_income).
    Valor é positivo para receitas, negativo para despesas.
    """
    is_income = '+' in val_raw

    # Remover tudo exceto dígitos, vírgula e ponto
    nums = re.sub(r'[^0-9,.]', '', val_raw)
    if not nums:
        return None, is_income

    # Padrão BR: ponto como milhar, vírgula como decimal  → "1.600,00" → "1600.00"
    # Após remoção de não-numéricos temos "1.600,00"
    # Estratégia: se contém vírgula → tratar . como milhar e , como decimal
    if ',' in nums:
        nums = nums.replace('.', '').replace(',', '.')
    # Caso sem vírgula mas com ponto (já é decimal US) → deixar como está

    try:
        val = Decimal(nums)
    except InvalidOperation:
        return None, is_income

    if not is_income:
        val = -val

    return val, is_income


class PierreTxtRowDTO(BaseModel):
    """Representação intermediária fortemente tipada da linha do Pierre."""
    data: datetime
    valor: Decimal
    descricao: str
    categoria: str
    conta: str


class PierreTxtParser:
    """
    Parser estrutural para o TXT do Pierre.

    Estratégia (REF-010):
    ─────────────────────
    O TXT do Pierre é um fluxo contínuo de blocos, cada um TERMINANDO com:
        CONTA
        DD/MM/YYYY  [+|-]R$ X,XX

    O parser acumula linhas em `current_block` até encontrar a linha
    data+valor (âncora). Quando a encontra, classifica o bloco de trás
    para frente:

        current_block[-1] = data+valor  (descartada após extração)
        current_block[-2] = conta
        Linhas antes da conta, ignorando linhas de emoji puro e vazias:
            → Primeira linha não-emoji = descrição
            → Demais linhas não-emoji  = categorias (podem ser múltiplas)

    Essa lógica NÃO depende de qual emoji está presente, apenas da
    estrutura do bloco.
    """

    def parse(self, doc: RawDocument) -> List[PierreTxtRowDTO]:
        parsed_rows: List[PierreTxtRowDTO] = []
        current_block: List[str] = []

        for i, raw_line in enumerate(doc.content):
            line_str = raw_line.strip()

            # Ignorar cabeçalho de 3 linhas
            if i < 3 and any(kw in line_str for kw in ('DESCRIÇÃO', 'DATA', 'VALOR')):
                continue

            # Ignorar linhas completamente vazias entre blocos
            if not line_str and not current_block:
                continue

            current_block.append(line_str)

            # Detectar âncora: linha de data + valor
            m = _DATE_VALUE_RE.match(line_str)
            if not m:
                continue

            date_str = m.group(1)
            val_raw = m.group(2)

            # ── Parse da data ──────────────────────────────────────────────
            try:
                dt = datetime.strptime(date_str, '%d/%m/%Y')
            except ValueError as e:
                logger.warning(
                    'Linha %d ignorada — data inválida: %r. Detalhe: %s',
                    i + 1, date_str, e
                )
                current_block = []
                continue

            # ── Parse do valor ─────────────────────────────────────────────
            val, _ = _parse_amount(val_raw)
            if val is None:
                logger.warning(
                    'Linha %d ignorada — valor inválido: %r',
                    i + 1, val_raw
                )
                current_block = []
                continue

            # ── Parse estrutural de trás para frente ───────────────────────
            # current_block[-1] = âncora data+valor (já processado)
            # current_block[-2] = conta  (linha imediatamente acima)
            if len(current_block) < 2:
                logger.warning(
                    'Linha %d ignorada — bloco muito curto (%d linhas): %r',
                    i + 1, len(current_block), current_block
                )
                current_block = []
                continue

            conta = current_block[-2]

            # Linhas internas do bloco (sem âncora e sem conta)
            interior = current_block[:-2]

            # Filtrar: remover linhas vazias e linhas de emoji puro
            text_lines = [
                l for l in interior
                if l and not _is_emoji_only_line(l)
            ]

            descricao = text_lines[0] if text_lines else 'Sem descrição'
            categorias = text_lines[1:]
            categoria = ' | '.join(categorias) if categorias else 'Sem categoria'

            parsed_rows.append(PierreTxtRowDTO(
                data=dt,
                valor=val,
                descricao=descricao,
                categoria=categoria,
                conta=conta,
            ))

            current_block = []

        return parsed_rows
