"""
Testes unitarios para o parser MyProfit Proventos.

Cobre:
1. Arquivo com coluna 'tipo' presente - valor preservado
2. Arquivo sem coluna 'tipo' - usa 'DESCONHECIDO'
3. Arquivo com coluna 'tipo' presente mas vazia - usa 'DESCONHECIDO'
4. Arquivo sem colunas obrigatorias reais - rejeitado com erro
"""
import pytest
from backend.integrations.myprofit.parser import MyProfitParser


# ---------------------------------------------------------------------------
# Helpers - gera CSV minimo valido de Proventos
# ---------------------------------------------------------------------------

def make_proventos_csv(with_tipo: bool = True, tipo_value: str = "DIVIDENDO") -> bytes:
    """
    Gera um CSV de Proventos minimo com dados validos.
    Se with_tipo=False, omite a coluna 'Tipo'.
    Se with_tipo=True e tipo_value='', gera coluna vazia.
    """
    if with_tipo:
        header = "Ativo,Recebido,Tipo,Data pgto.,Data COM,Valor por cota,Cotas"
        row = f'TAEE11,"R$ 50,25",{tipo_value},15/08/2024,13/08/2024,"R$ 0,08",619'
    else:
        header = "Ativo,Recebido,Data pgto.,Data COM,Valor por cota,Cotas"
        row = 'TAEE11,"R$ 50,25",15/08/2024,13/08/2024,"R$ 0,08",619'
    return f"{header}\n{row}\n".encode("utf-8")


# ---------------------------------------------------------------------------
# Teste 1: arquivo com 'tipo' presente - valor preservado
# ---------------------------------------------------------------------------

def test_parse_proventos_with_tipo():
    """Parser preserva o valor original de 'tipo' quando a coluna existe."""
    content = make_proventos_csv(with_tipo=True, tipo_value="DIVIDENDO")
    parser = MyProfitParser(content)
    rows, report = parser.parse_proventos()

    assert len(report["errors"]) == 0, f"Erros inesperados: {report['errors']}"
    assert len(rows) == 1
    assert rows[0]["tipo"] == "DIVIDENDO"
    assert rows[0]["ativo"] == "TAEE11"


def test_parse_proventos_with_tipo_jcp():
    """Parser preserva outros tipos como JCP."""
    content = make_proventos_csv(with_tipo=True, tipo_value="JCP")
    parser = MyProfitParser(content)
    rows, report = parser.parse_proventos()

    assert len(report["errors"]) == 0
    assert len(rows) == 1
    assert rows[0]["tipo"] == "JCP"


# ---------------------------------------------------------------------------
# Teste 2: arquivo sem coluna 'tipo' - usa 'DESCONHECIDO'
# ---------------------------------------------------------------------------

def test_parse_proventos_without_tipo_column():
    """Quando a coluna 'tipo' esta ausente, o parser aceita a linha e usa 'DESCONHECIDO'."""
    content = make_proventos_csv(with_tipo=False)
    parser = MyProfitParser(content)
    rows, report = parser.parse_proventos()

    assert len(report["errors"]) == 0, f"Erros inesperados: {report['errors']}"
    assert len(rows) == 1
    assert rows[0]["tipo"] == "DESCONHECIDO"
    assert rows[0]["ativo"] == "TAEE11"


# ---------------------------------------------------------------------------
# Teste 3: coluna 'tipo' presente mas vazia - usa 'DESCONHECIDO'
# ---------------------------------------------------------------------------

def test_parse_proventos_with_empty_tipo():
    """Quando 'tipo' existe mas esta vazio, o parser usa 'DESCONHECIDO'."""
    content = make_proventos_csv(with_tipo=True, tipo_value="")
    parser = MyProfitParser(content)
    rows, report = parser.parse_proventos()

    assert len(report["errors"]) == 0
    assert len(rows) == 1
    assert rows[0]["tipo"] == "DESCONHECIDO"


# ---------------------------------------------------------------------------
# Teste 4: rejeicao de colunas obrigatorias ausentes
# ---------------------------------------------------------------------------

def test_parse_proventos_missing_required_ativo():
    """Arquivo sem coluna 'ativo' e rejeitado com erro de validacao."""
    csv_content = (
        "Recebido,Tipo,Data pgto.,Data COM,Valor por cota,Cotas\n"
        '"R$ 50,25",DIVIDENDO,15/08/2024,13/08/2024,"R$ 0,08",619\n'
    ).encode("utf-8")
    parser = MyProfitParser(csv_content)
    rows, report = parser.parse_proventos()

    assert len(report["errors"]) > 0
    assert len(rows) == 0
    assert "ativo" in report["errors"][0]


def test_parse_proventos_missing_required_recebido():
    """Arquivo sem coluna 'recebido' e rejeitado com erro de validacao."""
    csv_content = (
        "Ativo,Tipo,Data pgto.,Data COM,Valor por cota,Cotas\n"
        'TAEE11,DIVIDENDO,15/08/2024,13/08/2024,"R$ 0,08",619\n'
    ).encode("utf-8")
    parser = MyProfitParser(csv_content)
    rows, report = parser.parse_proventos()

    assert len(report["errors"]) > 0
    assert len(rows) == 0


def test_parse_proventos_missing_required_data_pgto():
    """Arquivo sem coluna 'Data pgto.' e rejeitado com erro de validacao."""
    csv_content = (
        "Ativo,Recebido,Tipo,Data COM,Valor por cota,Cotas\n"
        'TAEE11,"R$ 50,25",DIVIDENDO,13/08/2024,"R$ 0,08",619\n'
    ).encode("utf-8")
    parser = MyProfitParser(csv_content)
    rows, report = parser.parse_proventos()

    assert len(report["errors"]) > 0
    assert len(rows) == 0
