# -*- coding: utf-8 -*-
"""Página Receitas e Despesas Aureni - CRUD de gastos_aureni."""

from datetime import date, datetime

import pandas as pd
import streamlit as st

import database as db
from helpers import fmt_moeda, parse_moeda
from io_excel import exportar_gastos_bytes, importar_gastos_df, nome_arquivo

st.subheader("Receitas e Despesas Aureni")

categorias = db.listar_opcoes("categoria")
tipos = db.listar_opcoes("tipo_operacao")

f_de, f_ate, f_cat, f_tipo = st.columns(4)
de = f_de.date_input(
    "De", value=date(datetime.now().year, 1, 1),
    format="DD/MM/YYYY", key="g_de")
ate = f_ate.date_input(
    "Até", value=datetime.now().date(),
    format="DD/MM/YYYY", key="g_ate")
categoria_filtro = f_cat.selectbox(
    "Categoria", ["Todas"] + categorias, key="g_cat")
tipo_filtro = f_tipo.selectbox(
    "Tipo", ["Todos"] + tipos, key="g_tipo")

clausulas = ["data BETWEEN ? AND ?"]
params = [de.isoformat(), ate.isoformat()]
if categoria_filtro != "Todas":
    clausulas.append("categoria = ?")
    params.append(categoria_filtro)
if tipo_filtro != "Todos":
    clausulas.append("tipo_operacao = ?")
    params.append(tipo_filtro)

gastos = db.listar_gastos(" AND ".join(clausulas), tuple(params))

acoes = st.container(horizontal=True)
novo_btn = acoes.button(
    "+ Novo lançamento", type="primary", icon=":material/add:")
editar_btn = acoes.button("Editar", icon=":material/edit:")
excluir_btn = acoes.button("Excluir", icon=":material/delete:")


def _dados_tabela():
    linhas = [
        {
            "ID": g["id"],
            "Data": g["data"][:10],
            "Tipo": g["tipo_operacao"],
            "Descrição": g["descricao"],
            "Categoria": g["categoria"],
            "Valor": float(g["valor"]),
            "Forma de pagamento": g["forma_pagamento"],
            "Observações": g["observacoes"] or "",
        }
        for g in gastos
    ]
    return pd.DataFrame(linhas)


df_tabela = _dados_tabela()
evento = st.dataframe(
    df_tabela,
    hide_index=True,
    selection_mode="single-row",
    on_select="rerun",
    key="tbl_gastos",
    column_config={
        "Valor": st.column_config.NumberColumn(format="R$ %.2f"),
    },
)

receitas = sum(g["valor"] for g in gastos if g["tipo_operacao"] == "Recebimento")
despesas = sum(g["valor"] for g in gastos if g["tipo_operacao"] != "Recebimento")
st.caption(
    f"{len(gastos)} registro(s) | Receitas: {fmt_moeda(receitas)} | "
    f"Despesas: {fmt_moeda(despesas)}"
)

selecionadas = evento.selection.rows
gasto_id = None
if selecionadas:
    gasto_id = int(df_tabela.iloc[selecionadas[0]]["ID"])


@st.dialog("Gasto Aureni", width="large")
def formulario_gasto(gasto):
    gid = "novo" if gasto is None else str(gasto["id"])
    er_data = st.date_input(
        "Data",
        value=(datetime.now().date() if gasto is None
               else date.fromisoformat(str(gasto["data"])[:10])),
        format="DD/MM/YYYY", key=f"gasto_data_{gid}")
    cmb_tipo = st.selectbox(
        "Tipo de operação",
        tipos or ["Pagamento"],
        index=((tipos or ["Pagamento"]).index(gasto["tipo_operacao"])
               if gasto is not None else 0),
        key=f"gasto_tipo_{gid}")
    ed_descricao = st.text_input(
        "Descrição",
        value=(gasto["descricao"] if gasto is not None else ""),
        placeholder="Ex.: Compra de produtos de limpeza",
        key=f"gasto_desc_{gid}")

    nova_categoria = ""
    if gasto is not None and gasto["categoria"] not in categorias:
        categorias_combo = categorias + [gasto["categoria"]]
        indice = categorias_combo.index(gasto["categoria"])
    else:
        categorias_combo = categorias or ["Geral"]
        indice = ((categorias_combo.index(gasto["categoria"])
                   if gasto is not None else 0))
    cmb_categoria = st.selectbox(
        "Categoria", categorias_combo, index=indice,
        key=f"gasto_cat_{gid}")
    nova_categoria = st.text_input(
        "Nova categoria (opcional - usa no lugar da selecionada)",
        key=f"gasto_novacat_{gid}")

    ed_valor = st.text_input(
        "Valor (R$)",
        value=(f"{gasto['valor']:.2f}".replace(".", ",")
               if gasto is not None else ""),
        placeholder="0,00", key=f"gasto_valor_{gid}")
    cmb_forma = st.selectbox(
        "Forma de pagamento",
        db.listar_opcoes("forma_pagamento") or ["Dinheiro"],
        index=((db.listar_opcoes("forma_pagamento") or ["Dinheiro"]).index(
            gasto["forma_pagamento"]) if gasto is not None else 0),
        key=f"gasto_forma_{gid}")
    ed_obs = st.text_area(
        "Observações",
        value=(gasto["observacoes"] or "" if gasto is not None else ""),
        key=f"gasto_obs_{gid}")

    if st.button("Salvar", type="primary", icon=":material/save:",
                 width="stretch"):
        valor = parse_moeda(ed_valor)
        if valor is None:
            st.error("Informe um valor numérico válido.")
            st.stop()
        if not ed_descricao.strip():
            st.error("Informe a descrição do gasto.")
            st.stop()
        categoria_final = (nova_categoria.strip()
                           if nova_categoria.strip() else cmb_categoria)
        dados = (
            er_data.isoformat(),
            ed_descricao.strip(),
            categoria_final or "Geral",
            valor,
            cmb_forma,
            ed_obs.strip(),
            cmb_tipo,
        )
        if gasto is None:
            db.criar_gasto(*dados)
            st.toast("Lançamento criado com sucesso.")
        else:
            db.atualizar_gasto(gasto["id"], *dados)
            st.toast("Lançamento atualizado com sucesso.")
        st.rerun()


@st.dialog("Confirmar exclusão")
def confirmar_exclusao(gasto):
    st.write(
        f'Excluir o gasto "{gasto["descricao"]}" de '
        f'{str(gasto["data"])[:10]} ({fmt_moeda(gasto["valor"])})?')
    linha = st.container(horizontal=True, horizontal_alignment="right")
    if linha.button("Cancelar"):
        st.rerun()
    if linha.button("Excluir", type="primary", icon=":material/delete:"):
        db.deletar_gasto(gasto["id"])
        st.toast("Registro excluído.")
        st.rerun()


if novo_btn:
    formulario_gasto(None)

if editar_btn:
    if gasto_id is None:
        st.info("Selecione um registro na tabela para editar.")
    else:
        formulario_gasto(db.buscar_gasto(gasto_id))

if excluir_btn:
    if gasto_id is None:
        st.info("Selecione um registro na tabela para excluir.")
    else:
        confirmar_exclusao(db.buscar_gasto(gasto_id))

with st.expander("Importar / Exportar Excel"):
    arquivo = st.file_uploader(
        "Importar planilha de gastos (.xlsx)",
        type=["xlsx", "xls"], key="g_import")
    if arquivo is not None:
        resultado = importar_gastos_df(pd.read_excel(arquivo))
        if resultado is None:
            st.error("Não foi possível identificar as colunas "
                     "'data' e 'valor'. Confira os cabeçalhos da planilha.")
        else:
            importados, erros = resultado
            if erros:
                st.warning(f"{importados} importado(s), {erros} ignorado(s).")
                if importados:
                    st.rerun()
            elif importados:
                st.success(f"{importados} registro(s) importado(s).")
                st.rerun()
            else:
                st.info("Nenhum registro importado.")

    bytes_excel = exportar_gastos_bytes()
    st.download_button(
        "Exportar Excel",
        data=bytes_excel or b"",
        file_name=nome_arquivo("gastos_aureni"),
        mime="application/vnd.openxmlformats-officedocument"
             ".spreadsheetml.sheet",
        icon=":material/download:",
        disabled=bytes_excel is None,
    )
