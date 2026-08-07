from django import template

register = template.Library()


@register.filter
def moeda(valor, casas=2):
    """Formata um número no padrão pt-BR (ponto de milhar, vírgula decimal)."""
    try:
        valor = float(valor)
        casas = int(casas)
    except (TypeError, ValueError):
        return valor

    texto = f"{valor:,.{casas}f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return texto
