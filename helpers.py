# -*- coding: utf-8 -*-
"""helpers.py - Utilidades compartilhadas pelas páginas web."""


def fmt_moeda(valor):
    """Formata um float como moeda brasileira: R$ 1.234,56."""
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def parse_moeda(texto):
    """Converte texto de moeda ('1.234,56') em float.

    Retorna None quando o texto não é numérico."""
    txt = str(texto or "").strip().replace("R$", "").replace(" ", "")
    if txt in ("", "-"):
        return 0.0
    negativo = txt.startswith("-")
    txt = txt.lstrip("-( )").replace(".", "").replace(",", ".")
    try:
        resultado = float(txt)
    except ValueError:
        return None
    return -resultado if negativo else resultado
