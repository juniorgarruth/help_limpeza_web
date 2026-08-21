# -*- coding: utf-8 -*-
"""Página Relatórios - geração de PDFs e Excel (equivalente ao desktop)."""

import os
import tempfile
from datetime import date, datetime

import pandas as pd
import streamlit as st

import database as db
from io_excel import (
    exportar_completo_bytes, importar_funcionarios_df,
    importar_gastos_df, nome_arquivo,
)
from reports.pdf_generator import (
    gerar_pdf_funcionarios, gerar_pdf_gastos, gerar_pdf_resumo,
)

MIME_PDF = "application/pdf"
MIME_XLSX = ("application/vnd.openxmlformats-officedocument"
             ".spreadsheetml.sheet")

st.subheader("Relatórios e Impressão")


def _pdf_bytes(funcao, *args, **kwargs):
    fd, caminho = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        qtd = funcao(caminho, *args, **kwargs)
        with open(caminho, "rb") as f:
            return qtd, f.read()
    finally:
        try:
            os.remove(caminho)
        except OSError:
            pass


with st.container(border=True):
    st.markdown("##### Relatório de Receitas e Despesas (Aureni)")
    g1, g2 = st.columns(2)
    g_de = g1.date_input(
        "De", value=date(datetime.now().year, 1, 1),
        format="DD/MM/YYYY", key="rg_de")
    g_ate = g2.date_input(
        "Até", value=datetime.now().date(), format="DD/MM/YYYY", key="rg_ate")
    modo = st.radio(
        "Categorias",
        ["Todas as categorias", "Somente selecionadas"],
        horizontal=True, key="rg_modo")
    categorias_sel = []
    if modo == "Somente selecionadas":
        categorias_sel = st.multiselect(
            "Categorias", db.listar_opcoes("categoria"), key="rg_cats")
    if st.button("Gerar PDF", type="primary", icon=":material/picture_as_pdf:"):
        if modo == "Somente selecionadas" and not categorias_sel:
            st.warning("Selecione pelo menos uma categoria.")
        else:
            with st.spinner("Gerando PDF..."):
                qtd, dados = _pdf_bytes(
                    gerar_pdf_gastos, de=g_de.isoformat(),
                    ate=g_ate.isoformat(),
                    categorias=categorias_sel or None)
            st.success(f"{qtd} registro(s) exportado(s).")
            st.download_button(
                "Baixar PDF",
                data=dados,
                file_name=f"relatorio_gastos_{datetime.now():%Y%m%d_%H%M}.pdf",
                mime=MIME_PDF,
                type="primary",
                icon=":material/download:")

with st.container(border=True):
    st.markdown("##### Relatório de Pagamentos por Funcionário")
    f1, f2 = st.columns(2)
    f_de = f1.date_input(
        "De ", value=date(datetime.now().year, 1, 1),
        format="DD/MM/YYYY", key="rf_de")
    f_ate = f2.date_input(
        "Até ", value=datetime.now().date(), format="DD/MM/YYYY", key="rf_ate")
    funcionario = st.selectbox(
        "Funcionário", ["(Todos)"] + db.listar_funcionarios(), key="rf_nome")
    if st.button("Gerar PDF (extrato geral ou individual)",
                 type="primary", icon=":material/picture_as_pdf:"):
        nome = None if funcionario == "(Todos)" else funcionario
        with st.spinner("Gerando PDF..."):
            qtd, dados = _pdf_bytes(
                gerar_pdf_funcionarios, de=f_de.isoformat(),
                ate=f_ate.isoformat(), funcionario=nome)
        st.success(f"{qtd} lançamento(s) exportado(s).")
        st.download_button(
            "Baixar PDF",
            data=dados,
            file_name=(f"relatorio_funcionarios_"
                       f"{datetime.now():%Y%m%d_%H%M}.pdf"),
            mime=MIME_PDF,
            type="primary",
            icon=":material/download:")

with st.container(border=True):
    st.markdown("##### Resumo Financeiro Mensal")
    MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro",
             "Dezembro"]
    r1, r2 = st.columns(2)
    r_mes_nome = r1.selectbox("Mês ", MESES,
                              index=datetime.now().month - 1, key="rr_mes")
    r_ano = r2.selectbox(
        "Ano ",
        list(range(datetime.now().year - 5, datetime.now().year + 2)),
        index=5, key="rr_ano")
    ano_mes = (f"{r_ano}-{MESES.index(r_mes_nome) + 1:02d}")
    if st.button("Gerar PDF", type="primary",
                 icon=":material/picture_as_pdf:", key="btn_resumo"):
        with st.spinner("Gerando PDF..."):
            _, dados = _pdf_bytes(gerar_pdf_resumo, ano_mes)
        st.success(f"Resumo de {ano_mes} pronto.")
        st.download_button(
            "Baixar PDF",
            data=dados,
            file_name=(f"relatorio_resumo_{ano_mes}.pdf"),
            mime=MIME_PDF,
            type="primary",
            icon=":material/download:",
            key="dl_resumo")

with st.container(border=True):
    st.markdown("##### Exportação para Excel")
    bytes_excel = exportar_completo_bytes()
    st.download_button(
        "Exportar Gastos + Funcionários (2 abas)",
        data=bytes_excel or b"",
        file_name=nome_arquivo("gastos_e_funcionarios"),
        mime=MIME_XLSX,
        icon=":material/download:",
        disabled=bytes_excel is None,
    )
    st.caption("Gera um único arquivo .xlsx com as abas "
               "GastosAureni e Funcionarios.")

with st.container(border=True):
    st.markdown("##### Importação de planilhas legadas (.xlsx)")
    arq_gastos = st.file_uploader(
        "Importar Gastos", type=["xlsx", "xls"], key="imp_gastos")
    if arq_gastos is not None:
        resultado = importar_gastos_df(pd.read_excel(arq_gastos))
        if resultado is None:
            st.error("Planilha incompatível: colunas 'data' e 'valor' "
                     "não identificadas.")
        else:
            importados, erros = resultado
            if erros:
                st.warning(f"{importados} importado(s), {erros} ignorado(s).")
            else:
                st.success(f"{importados} registro(s) importado(s).")

    arq_func = st.file_uploader(
        "Importar Funcionários", type=["xlsx", "xls"], key="imp_func")
    if arq_func is not None:
        resultado = importar_funcionarios_df(pd.read_excel(arq_func))
        if resultado is None:
            st.error("Planilha incompatível: colunas 'data' e "
                     "'funcionário' não identificadas.")
        else:
            importados, erros = resultado
            if erros:
                st.warning(f"{importados} importado(s), {erros} ignorado(s).")
            else:
                st.success(f"{importados} registro(s) importado(s).")
