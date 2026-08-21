# -*- coding: utf-8 -*-
"""Página Dashboard - Painel Financeiro (equivalente à aba do desktop)."""

from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

import database as db
from helpers import fmt_moeda

ROXO = "#6B52B3"
DOURADO = "#DDAA33"

st.subheader("Painel Financeiro")

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

col_mes, col_ano = st.columns(2)
mes_nome = col_mes.selectbox(
    "Mês", MESES, index=datetime.now().month - 1, key="dash_mes")
ano = col_ano.selectbox(
    "Ano",
    list(range(datetime.now().year - 5, datetime.now().year + 2)),
    index=5,
    key="dash_ano",
)
ano_mes = f"{ano}-{MESES.index(mes_nome) + 1:02d}"

resumo = db.resumo_mes(ano_mes)
serie = db.serie_mensal(6)

c_receitas, c_despesas, c_pagfunc, c_saldo = st.columns(4)

with c_receitas:
    with st.container(border=True):
        st.caption("Receitas do mês")
        st.markdown(f"### :green[{fmt_moeda(resumo['receitas'])}]")
        st.caption(
            f"Funcionários: {fmt_moeda(resumo['receitas_func'])} · "
            f"Aureni: {fmt_moeda(resumo['receitas_gastos'])}"
        )

with c_despesas:
    with st.container(border=True):
        st.caption("Despesas do mês")
        st.markdown(f"### :red[{fmt_moeda(resumo['despesa_total'])}]")
        st.caption(
            f"Aureni: {fmt_moeda(resumo['despesas_gastos'])} · "
            f"Funcionários: {fmt_moeda(resumo['pagamentos_funcionarios'])}"
        )

with c_pagfunc:
    with st.container(border=True):
        st.caption("Pagamentos de funcionários")
        st.markdown(f"### {fmt_moeda(resumo['pagamentos_funcionarios'])}")
        st.caption("Somente lançamentos com status Pago")

cor_saldo = "green" if resumo["saldo"] >= 0 else "red"
with c_saldo:
    with st.container(border=True):
        st.caption("Saldo do mês")
        st.markdown(f"### :{cor_saldo}[{fmt_moeda(resumo['saldo'])}]")
        st.caption(
            f"Receitas {fmt_moeda(resumo['receitas'])} − "
            f"Despesas {fmt_moeda(resumo['despesa_total'])}"
        )

df_serie = pd.DataFrame(serie)
df_longo = df_serie.melt(
    id_vars="label",
    value_vars=["receitas", "despesas"],
    var_name="Tipo",
    value_name="Valor",
)
df_longo["Tipo"] = df_longo["Tipo"].map(
    {"receitas": "Receitas", "despesas": "Despesas"}
)

grafico = (
    alt.Chart(df_longo)
    .mark_bar()
    .encode(
        x=alt.X("label:N", title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("Tipo:N"),
        y=alt.Y("Valor:Q", title=None),
        color=alt.Color(
            "Tipo:N",
            scale=alt.Scale(range=[ROXO, DOURADO]),
            legend=alt.Legend(title=None, orient="top"),
        ),
        tooltip=[
            alt.Tooltip("label:N", title="Mês"),
            alt.Tooltip("Tipo:N", title="Tipo"),
            alt.Tooltip("Valor:Q", title="Valor", format=",.2f"),
        ],
    )
    .properties(title="Receitas x Despesas (últimos 6 meses)")
    .configure_title(color=ROXO, fontSize=14, fontWeight="bold", anchor="middle")
    .configure_axis(gridColor="#E0E0E0", labelColor="#4A3F75")
    .configure_view(stroke=None)
)

st.altair_chart(grafico)
