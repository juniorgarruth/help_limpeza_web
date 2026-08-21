# -*- coding: utf-8 -*-
"""Página Cadastros - gestão das listas de opções dos formulários."""

import streamlit as st

import database as db

st.subheader("Cadastros - Listas de opções")

GRUPOS = [
    ("tipo_operacao", "Tipo de operação"),
    ("status", "Status"),
    ("categoria", "Categoria"),
    ("forma_pagamento", "Forma de pagamento"),
]

abas = st.tabs([rotulo for _, rotulo in GRUPOS])

for (grupo, rotulo), aba in zip(GRUPOS, abas):
    with aba:
        opcoes = db.listar_opcoes_todos(grupo)

        with st.form(f"form_add_{grupo}", border=False):
            novo_valor = st.text_input("Novo item", placeholder="Digite o valor")
            if st.form_submit_button("Adicionar", type="primary",
                                     icon=":material/add:"):
                if not novo_valor.strip():
                    st.warning("Digite um valor.")
                else:
                    resultado = db.criar_opcao(grupo, novo_valor)
                    if resultado is None:
                        st.warning("Esse valor já existe na lista.")
                    else:
                        st.toast("Item adicionado.")
                        st.rerun()

        if not opcoes:
            st.caption("Nenhum item cadastrado nesta lista.")
            continue

        mapa = {f"{o['valor']}": o["id"] for o in opcoes}
        escolha = st.selectbox(
            "Item", list(mapa.keys()), key=f"sel_{grupo}")

        col_editar, col_excluir = st.columns(2)
        with col_editar:
            with st.form(f"form_edit_{grupo}", border=False):
                renome = st.text_input(
                    "Renomear para", value=escolha, key=f"renome_{grupo}")
                if st.form_submit_button("Renomear", icon=":material/edit:"):
                    if not renome.strip():
                        st.warning("Digite o novo nome.")
                    elif renome.strip() == escolha:
                        st.info("O nome não mudou.")
                    else:
                        ok = db.atualizar_opcao(mapa[escolha], renome)
                        if ok:
                            st.toast("Item renomeado.")
                            st.rerun()
                        else:
                            st.warning(
                                "Já existe um item com esse nome na lista.")
        with col_excluir:
            if st.button("Excluir", icon=":material/delete:",
                         key=f"excluir_{grupo}",
                         type="primary"):
                db.deletar_opcao(mapa[escolha])
                st.toast(f'Item "{escolha}" excluído.')
                st.rerun()
