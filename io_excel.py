# -*- coding: utf-8 -*-
"""
io_excel.py - Importação e exportação de dados em Excel (.xlsx)
sem dependência de interface (versão web de ui/import_export.py).
"""

import io
from datetime import datetime

import pandas as pd

import database as db


def _moeda_para_float(valor):
    """Converte texto de moeda brasileira ('1.234,56') para float."""
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    if texto in ("", "-"):
        return 0.0
    negativo = texto.startswith("-")
    texto = texto.lstrip("-( )")
    numero = texto.replace(".", "").replace(",", ".")
    try:
        resultado = float(numero)
    except ValueError:
        return 0.0
    return -resultado if negativo else resultado


MAPEAMENTO_GASTOS = {
    "data": ["data", "dat", "dia", "date"],
    "descricao": ["descricao", "descri", "item", "serviço", "servico",
                  "produto", "detalhe"],
    "categoria": ["categoria", "cat", "grupo"],
    "tipo_operacao": ["tipo de operação", "tipo de operacao", "tipo",
                      "operacao", "operação", "natureza", "entrada",
                      "saída", "saida"],
    "valor": ["valor", "valor r$", "valor(r$)", "r$", "total",
              "valor total", "custo", "preço", "preco", "montante"],
    "forma_pagamento": ["forma", "forma de pagamento", "pagamento",
                        "forma pagamento", "meio"],
    "observacoes": ["observacoes", "observações", "obs", "nota",
                    "complemento", "extra"],
}

MAPEAMENTO_FUNC = {
    "data": ["data", "dat", "dia", "date", "competência", "competencia",
             "referente", "ref"],
    "nome": ["nome", "funcionario", "funcionário", "empregado",
             "colaborador", "nome do funcionário"],
    "tipo": ["tipo", "tipo de operação", "operacao", "operação",
             "natureza", "categoria"],
    "bruto": ["valor bruto", "bruto", "valor", "vencimento", "salário",
              "salario", "proventos", "total"],
    "descontos": ["desconto", "descontos", "deducoes", "deduções"],
    "liquido": ["valor liquido", "valor líquido", "liquido", "líquido",
                "total líquido", "total liquido"],
    "status": ["status", "situação", "situacao", "estado", "situacao do p"],
    "obs": ["observacoes", "observações", "obs", "nota", "comentário",
            "comentario"],
}


def _mapear(df, mapeamento):
    mapa = {}
    for nome_padrao, alternativas in mapeamento.items():
        encontrada = None
        for col in df.columns:
            for alt in alternativas:
                if col == alt or alt in col:
                    encontrada = col
                    break
            if encontrada:
                break
        mapa[nome_padrao] = encontrada
    return mapa


def _normalizar_colunas(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def importar_gastos_df(df):
    """Importa um DataFrame como gastos. Retorna (importados, erros) ou None
    quando a planilha não tem 'data' e 'valor' identificáveis."""
    df = _normalizar_colunas(df)
    mapa = _mapear(df, MAPEAMENTO_GASTOS)
    if not mapa["data"] or not mapa["valor"]:
        return None

    def detectar_tipo(linha):
        raw = str(linha.get(mapa["tipo_operacao"]) or "").lower()
        if not raw or raw in ("nan", "none"):
            return "Pagamento"
        if "receb" in raw or "entrada" in raw or "receita" in raw:
            return "Recebimento"
        if "adiant" in raw:
            return "Adiantamento"
        return "Pagamento"

    importados = 0
    erros = 0
    for _, linha in df.iterrows():
        try:
            data = linha.get(mapa["data"])
            descricao = str(linha.get(mapa["descricao"]) or "").strip()
            if not descricao or descricao.lower() == "nan":
                descricao = "Sem descrição"
            categoria = str(linha.get(mapa["categoria"]) or "Geral").strip()
            if categoria.lower() == "nan":
                categoria = "Geral"
            valor = _moeda_para_float(linha.get(mapa["valor"]))
            forma = str(linha.get(mapa["forma_pagamento"]) or "Dinheiro").strip()
            if forma.lower() == "nan":
                forma = "Dinheiro"
            obs = str(linha.get(mapa["observacoes"]) or "").strip()
            if obs.lower() == "nan":
                obs = ""
            db.criar_gasto(data, descricao[:200], categoria[:200], valor,
                           forma[:50], obs, detectar_tipo(linha))
            importados += 1
        except Exception:
            erros += 1
    return importados, erros


def importar_funcionarios_df(df):
    """Importa um DataFrame como lançamentos de funcionários.
    Retorna (importados, erros) ou None se faltar data/nome."""
    df = _normalizar_colunas(df)
    mapa = _mapear(df, MAPEAMENTO_FUNC)
    if not mapa["data"] or not mapa["nome"]:
        return None

    def tipo(linha):
        raw = str(linha.get(mapa["tipo"]) or "").lower()
        if "adiant" in raw:
            return "Adiantamento"
        if "receb" in raw or raw.strip() == "rec":
            return "Recebimento"
        return "Pagamento"

    def status(linha):
        raw = str(linha.get(mapa["status"]) or "").lower()
        if "pago" in raw or "ok" in raw or raw in ("sim", "s"):
            return "Pago"
        if "pend" in raw:
            return "Pendente"
        return "Pago"

    importados = 0
    erros = 0
    for _, linha in df.iterrows():
        try:
            data = linha.get(mapa["data"])
            nome = str(linha.get(mapa["nome"]) or "").strip()
            if not nome or nome.lower() == "nan":
                erros += 1
                continue
            bruto = _moeda_para_float(linha.get(mapa["bruto"]))
            descontos = _moeda_para_float(linha.get(mapa["descontos"]))
            liquido = _moeda_para_float(linha.get(mapa["liquido"]))
            if liquido == 0:
                liquido = bruto - descontos
            obs = str(linha.get(mapa["obs"]) or "").strip()
            if obs.lower() == "nan":
                obs = ""
            db.criar_lancamento_func(
                data, nome[:200], tipo(linha), bruto, descontos,
                liquido, status(linha), obs)
            importados += 1
        except Exception:
            erros += 1
    return importados, erros


def _bytes_de(frames):
    """Gera os bytes de um .xlsx com as abas informadas {nome: DataFrame}."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for nome, frame in frames.items():
            (frame if frame is not None else pd.DataFrame()).to_excel(
                writer, index=False, sheet_name=nome)
    return buffer.getvalue()


def exportar_gastos_bytes():
    dados = [dict(g) for g in db.listar_gastos()]
    if not dados:
        return None
    return _bytes_de({"GastosAureni": pd.DataFrame(dados)})


def exportar_funcionarios_bytes():
    dados = [dict(l) for l in db.listar_lancamentos_func()]
    if not dados:
        return None
    return _bytes_de({"Funcionarios": pd.DataFrame(dados)})


def exportar_completo_bytes():
    gastos = [dict(g) for g in db.listar_gastos()]
    lancamentos = [dict(l) for l in db.listar_lancamentos_func()]
    if not gastos and not lancamentos:
        return None
    return _bytes_de({
        "GastosAureni": pd.DataFrame(gastos),
        "Funcionarios": pd.DataFrame(lancamentos),
    })


def nome_arquivo(prefixo):
    return f"{prefixo}_{datetime.now():%Y%m%d}.xlsx"
