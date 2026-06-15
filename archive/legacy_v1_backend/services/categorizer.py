import csv
import re
from pathlib import Path

from models.core import CanonicalTransaction
from taxonomy.categories import Natureza, Perfil
from utils.semantic import normalize_description


PIERRE_CATEGORY_MAP = {
    "Transferências": {"macro": "TRANSFERENCIA_INTERNA", "sub": "INTERNAL_TRANSFER", "natureza": Natureza.TRANSFER, "perfil": Perfil.PATRIMONIAL},
    "Transferências para terceiros": {"macro": "PAGAMENTO_DIRETO", "sub": "THIRD_PARTY_TRANSFER", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Investimentos": {"macro": "INVESTIMENTOS", "sub": "GERAL", "natureza": Natureza.INVESTMENT, "perfil": Perfil.PATRIMONIAL},
    "Compras online": {"macro": "ALIMENTACAO", "sub": "E_COMMERCE", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Serviços": {"macro": "SERVICOS", "sub": "GERAL", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Compras": {"macro": "COMPRAS", "sub": "GERAL", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Restaurantes, bares e lanchonetes": {"macro": "ALIMENTACAO", "sub": "RESTAURANTES", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Postos de gasolina": {"macro": "TRANSPORTE", "sub": "COMBUSTIVEL", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Supermercado": {"macro": "ALIMENTACAO", "sub": "SUPERMERCADO", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Farmácia": {"macro": "SAUDE", "sub": "FARMACIA", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Telecomunicação": {"macro": "MORADIA", "sub": "TELECOM", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Entre contas": {"macro": "TRANSFERENCIA_INTERNA", "sub": "ENTRE_CONTAS", "natureza": Natureza.TRANSFER, "perfil": Perfil.PATRIMONIAL},
    "Saúde": {"macro": "SAUDE", "sub": "GERAL", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Seguros": {"macro": "MORADIA", "sub": "SEGUROS", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Alimentos e bebidas": {"macro": "ALIMENTACAO", "sub": "GERAL", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Serviços automotivos": {"macro": "TRANSPORTE", "sub": "AUTOMOTIVO", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Hospitais, clínicas e laboratórios": {"macro": "SAUDE", "sub": "ATENDIMENTO", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Ética": {"macro": "SAUDE", "sub": "ETICA", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Serviços digitais": {"macro": "SERVICOS", "sub": "DIGITAIS", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Utensílios para casa": {"macro": "MORADIA", "sub": "CASA", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Ótica": {"macro": "SAUDE", "sub": "GERAL", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Vestiário": {"macro": "VESTUARIO", "sub": "GERAL", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Apostas": {"macro": "OUTROS", "sub": "APOSTAS", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Lazer": {"macro": "LAZER", "sub": "GERAL", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Manutenção de veículos": {"macro": "TRANSPORTE", "sub": "MANUTENCAO", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Livraria": {"macro": "EDUCACAO", "sub": "LIVRARIA", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Táxi e transporte privado urbano": {"macro": "TRANSPORTE", "sub": "APLICATIVO", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Eletrônicos": {"macro": "MORADIA", "sub": "ELETRONICOS", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Celular": {"macro": "MORADIA", "sub": "CELULAR", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Aluguel de veículos": {"macro": "TRANSPORTE", "sub": "ALUGUEL_VEICULOS", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Streaming de música": {"macro": "ASSINATURAS", "sub": "STREAMING", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Restaurantes, bares lanchonetes": {"macro": "ALIMENTACAO", "sub": "RESTAURANTES", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Moradia": {"macro": "MORADIA", "sub": "GERAL", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Renda fixa": {"macro": "INVESTIMENTOS", "sub": "RENDA_FIXA", "natureza": Natureza.INVESTMENT, "perfil": Perfil.PATRIMONIAL},
    "Outros": {"macro": "OUTROS", "sub": "INDEFINIDO", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Eletricidade": {"macro": "MORADIA", "sub": "ENERGIA", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Transferência - PIX": {"macro": "TRANSFERENCIA_INTERNA", "sub": "PIX", "natureza": Natureza.TRANSFER, "perfil": Perfil.PATRIMONIAL},
    "Aluguel de bicicletas": {"macro": "TRANSPORTE", "sub": "BICICLETAS", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Estacionamentos": {"macro": "TRANSPORTE", "sub": "ESTACIONAMENTO", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Transporte": {"macro": "TRANSPORTE", "sub": "GERAL", "natureza": Natureza.EXPENSE, "perfil": Perfil.ESSENCIAL},
    "Hospedagem": {"macro": "VIAGEM", "sub": "HOSPEDAGEM", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Papelaria": {"macro": "EDUCACAO", "sub": "PAPELARIA", "natureza": Natureza.EXPENSE, "perfil": Perfil.DISCRICIONARIO},
    "Transferência - Mesma instituição": {"macro": "TRANSFERENCIA_INTERNA", "sub": "MESMA_INSTITUICAO", "natureza": Natureza.TRANSFER, "perfil": Perfil.PATRIMONIAL},
    "Pagamento de cartão de crédito": {"macro": "PASSIVOS", "sub": "CARTAO_CREDITO", "natureza": Natureza.TRANSFER, "perfil": Perfil.IGNORADO},
}

PIERRE_CATEGORY_LOOKUP = {normalize_description(key): value for key, value in PIERRE_CATEGORY_MAP.items()}


OWNERS = ["CLEIDSON RAMOS", "C RAMOS", "CLEIDSON R", "CLEIDSON RAMOS DE CARVALHO"]
SEMANTIC_MACRO_CATEGORIES = [
    "RECEBIMENTO_DIRETO",
    "TRANSFERENCIA_INTERNA",
    "SALARIO",
    "DIVIDENDOS",
    "PAGAMENTO_DIRETO",
    "OUTROS",
]


def _classification_payload(
    macro: str,
    sub: str,
    natureza: Natureza,
    perfil: Perfil,
) -> dict[str, object]:
    return {
        "macro": macro,
        "sub": sub,
        "macro_categoria": macro,
        "subnatureza": sub,
        "natureza": natureza,
        "perfil": perfil,
    }


def aplicar_regras_semanticas(descricao: str, valor: float) -> dict[str, object] | None:
    desc_upper = normalize_description(descricao).upper()

    if any(keyword in desc_upper for keyword in ["MERCADOLIVRE", "SHOPEE", "AMAZON", "MERCADOPAGO", "ALIEXPRESS"]):
        return _classification_payload(
            "ALIMENTACAO",
            "E_COMMERCE",
            Natureza.EXPENSE,
            Perfil.DISCRICIONARIO,
        )

    is_owner = any(owner in desc_upper for owner in OWNERS)
    if is_owner and any(keyword in desc_upper for keyword in ["TRANSFER", "PIX", "TED"]):
        return _classification_payload(
            "TRANSFERENCIA_INTERNA",
            "INTERNAL_TRANSFER",
            Natureza.NEUTRAL,
            Perfil.PATRIMONIAL,
        )

    if desc_upper.startswith("TRANSFERENCIA RECEBIDA"):
        return _classification_payload(
            "TRANSFERENCIA_INTERNA",
            "RECEBIMENTO_TRANSFERENCIA",
            Natureza.INCOME,
            Perfil.PATRIMONIAL,
        )

    if desc_upper == "VALOR RECEBIDO DE INVESTIMENTOS":
        return _classification_payload(
            "INVESTIMENTOS",
            "RENDIMENTO",
            Natureza.INCOME,
            Perfil.PATRIMONIAL,
        )

    if desc_upper.startswith("CREDITO DE ") or desc_upper.startswith("CREDITO EM CONTA"):
        return _classification_payload(
            "RECEBIMENTO_DIRETO",
            "CREDITO_CONTA",
            Natureza.INCOME,
            Perfil.DISCRICIONARIO,
        )

    if desc_upper == "PAGAMENTO RECEBIDO":
        return _classification_payload(
            "OUTROS",
            "RECEBIMENTO",
            Natureza.INCOME,
            Perfil.DISCRICIONARIO,
        )

    if any(keyword in desc_upper for keyword in [
        "APLICACAO", "RESGATE", "COMPRA DE FII", "COMPRA DE ACAO", "COMPRA DE ACOES",
        "COMPRA DE ETF", "COMPRA DE BDR", "TESOURO DIRETO", "CORRETORA", "NUINVEST", 
        "INTER INVEST", "XP INVESTIMENTOS", "VALOR TRANSFERIDO PARA INVESTIMENTOS",
        "RENDA VARIAVEL"
    ]):
        return _classification_payload(
            "INVESTIMENTOS",
            "MOVIMENTACAO",
            Natureza.INVESTMENT,
            Perfil.PATRIMONIAL,
        )

    if valor > 0:
        if any(keyword in desc_upper for keyword in ["SALARIO", "ORDEM BANCARIA", "FOLHA DE PAGAMENTO"]):
            return _classification_payload(
                "SALARIO",
                "SALARY",
                Natureza.INCOME,
                Perfil.ESSENCIAL,
            )

        if any(keyword in desc_upper for keyword in ["DIVIDENDO", "RENDIMENTO", "JUROS"]):
            return _classification_payload(
                "DIVIDENDOS",
                "DIVIDEND",
                Natureza.DIVIDEND,
                Perfil.PATRIMONIAL,
            )

        if any(keyword in desc_upper for keyword in ["TRANSFERENCIA ENVIADA", "TRANSFER ENVIADO", "PIX", "TED"]):
            return _classification_payload(
                "PAGAMENTO_DIRETO",
                "THIRD_PARTY_TRANSFER",
                Natureza.EXPENSE,
                Perfil.DISCRICIONARIO,
            )

    if valor < 0 and any(keyword in desc_upper for keyword in ["PIX", "TED", "TRANSFER"]):
        return _classification_payload(
            "PAGAMENTO_DIRETO",
            "PIX_TED_OUT",
            Natureza.EXPENSE,
            Perfil.DISCRICIONARIO,
        )

    return None


class SmartCategorizer:
    def __init__(self, rules_path: Path):
        self.rules = self._load_rules(rules_path)

    def available_categories(self) -> list[str]:
        categories = {rule["macro"] for rule in self.rules if rule.get("macro")}
        categories.update(SEMANTIC_MACRO_CATEGORIES)
        return sorted(categories)

    def _load_rules(self, path: Path) -> list[dict[str, str]]:
        rules: list[dict[str, str]] = []
        if path.exists():
            with open(path, mode="r", encoding="utf-8") as file_handle:
                reader = csv.DictReader(file_handle)
                for row in reader:
                    if row.get("keyword"):
                        rules.append(row)
        return rules

    def classify(self, transaction: CanonicalTransaction) -> dict[str, object]:
        descricao = transaction.get("descricao_normalizada") or transaction.get("descricao_original") or ""
        descricao = normalize_description(descricao)
        valor = transaction.get("valor", 0)

        semantica = aplicar_regras_semanticas(descricao, valor)
        if semantica:
            return semantica

        categoria_origem = normalize_description(str(transaction.get("categoria_origem") or ""))
        if categoria_origem and categoria_origem in PIERRE_CATEGORY_LOOKUP:
            mapped = PIERRE_CATEGORY_LOOKUP[categoria_origem]
            return _classification_payload(
                mapped["macro"],
                mapped["sub"],
                mapped["natureza"],
                mapped["perfil"],
            )

        for rule in self.rules:
            if re.search(rule["keyword"], descricao, re.IGNORECASE):
                return _classification_payload(
                    rule["macro"],
                    rule["sub"],
                    Natureza(rule["natureza"]),
                    Perfil(rule["perfil"]),
                )

        return _classification_payload(
            "OUTROS",
            "INDEFINIDO",
            Natureza.EXPENSE,
            Perfil.DISCRICIONARIO,
        )