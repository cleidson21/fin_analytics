from decimal import Decimal, ROUND_HALF_UP


def format_money(value) -> str:
    """Calcula com precisão absoluta e devolve uma string limpa para o JSON."""
    if value is None:
        return "0.00"

    dec_val = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{dec_val:.2f}"
