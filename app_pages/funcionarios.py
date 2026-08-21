# -*- coding: utf-8 -*-
"""Página Funcionários - Recebimentos e Pagamentos de Funcionários."""

from datetime import date, datetime

import pandas as pd
import streamlit as st

import database as db
from helpers import fmt_moeda, parse_moeda
from io_excel import exportar_funcionarios_bytes, nome_arquivo

st.subheader("Recebimentos e Pagamentos de Funcionários")

funcionarios = db.listar_funcionarios()

f_de, f_ate, f_nome = st.columns(3)
de = f_de.date_input(
    "De", value=date(datetime.now().year, 1, 1),
    format="DD/MM/YYYY", key="fn_de")
ate = f_ate.date_input(
    "Até", value=datetime.now().date(),
    format="DD/MM/YYYY", key="fn_ate")
filtro_func = f_nome.selectbox(
    "Funcionário", ["Todos"] + funcionarios, key="fn_nome")

clausulas = ["data BETWEEN ? AND ?"]
params = [de.isoformat(), ate.isoformat()]
if filtro_func != "Todos":
    clausulas.append("nome_funcionario = ?")
    params.append(filtro_func)

lancamentos = db.listar_lancamentos_func(
    " AND ".join(clausulas), tuple(params))

acoes = st.container(horizontal=True)
novo_btn = acoes.button(
    "+ Novo lançamento", type="primary", icon=":material/add:")
editar_btn = acoes.button("Editar", icon=":material/edit:")
excluir_btn = acoes.button("Excluir", icon=":material/delete:")
gerenciar_btn = acoes.button("Cadastrar funcionário",
                             icon=":material/person_add:")


def _dados_tabela():
    return pd.DataFrame([
        {
            "ID": l["id"],
            "Data": l["data"][:10],
            "Funcionário": l["nome_funcionario"],
            "Tipo": l["tipo_operacao"],
            "Valor bruto": float(l["valor_bruto"]),
            "Descontos": float(l["descontos"]),
            "Valor líquido": float(l["valor_liquido"]),
            "Status": l["status_pagamento"],
        }
        for l in lancamentos
    ])


df_tabela = _dados_tabela()
evento = st.dataframe(
    df_tabela,
    hide_index=True,
    selection_mode="single-row",
    on_select="rerun",
    key="tbl_func",
    column_config={
        "Valor bruto": st.column_config.NumberColumn(format="R$ %.2f"),
        "Descontos": st.column_config.NumberColumn(format="R$ %.2f"),
        "Valor líquido": st.column_config.NumberColumn(format="R$ %.2f"),
    },
)

total = sum(l["valor_liquido"] for l in lancamentos)
st.caption(f"{len(lancamentos)} lançamento(s) | Total: {fmt_moeda(total)}")

selecionadas = evento.selection.rows
lancamento_id = None
if selecionadas:
    lancamento_id = int(df_tabela.iloc[selecionadas[0]]["ID"])


def _calcular_liquido(valor_bruto, descontos):
    try:
        bruto = float(valor_bruto or 0)
    except (TypeError, ValueError):
        bruto = 0
    try:
        desc = float(descontos or 0)
    except (TypeError, ValueError):
        desc = 0
    return bruto - desc


@st.dialog("Lançamento de Funcionário", width="large")
def formulario_lancamento(lancamento):
    lid = "novo" if lancamento is None else str(lancamento["id"])
    er_data = st.date_input(
        "Data",
        value=(datetime.now().date() if lancamento is None
               else date.fromisoformat(str(lancamento["data"])[:10])),
        format="DD/MM/YYYY", key=f"lf_data_{lid}")

    cadastrados = db.listar_funcionarios()
    nome_atual = ("" if lancamento is None
                  else lancamento["nome_funcionario"])
    opcoes = list(cadastrados)
    indice_padrao = 0
    if nome_atual and nome_atual not in opcoes:
        opcoes = [nome_atual] + opcoes
        indice_padrao = 0
    elif nome_atual:
        indice_padrao = opcoes.index(nome_atual)
    cmb_nome = st.selectbox(
        "Funcionário cadastrado", opcoes or ["(nenhum)"],
        index=indice_padrao, key=f"lf_nome_{lid}")
    outro_nome = st.text_input(
        "Outro nome (opcional - usa no lugar do selecionado)",
        key=f"lf_outro_{lid}")

    cmb_tipo = st.selectbox(
        "Tipo de operação",
        db.listar_opcoes("tipo_operacao") or ["Pagamento"],
        index=((db.listar_opcoes("tipo_operacao") or ["Pagamento"]).index(
            lancamento["tipo_operacao"]) if lancamento is not None else 0),
        key=f"lf_tipo_{lid}")
    ed_bruto = st.text_input(
        "Valor bruto (R$)",
        value=(f"{lancamento['valor_bruto']:.2f}".replace(".", ",")
               if lancamento is not None else ""),
        placeholder="0,00", key=f"lf_bruto_{lid}")
    ed_descontos = st.text_input(
        "Descontos (R$)",
        value=(f"{lancamento['descontos']:.2f}".replace(".", ",")
               if lancamento is not None else ""),
        placeholder="0,00", key=f"lf_desc_{lid}")

    bruto_num = parse_moeda(ed_bruto)
    desc_num = parse_moeda(ed_descontos)
    liquido = _calcular_liquido(bruto_num, desc_num)
    st.markdown(f"**Valor líquido:** {fmt_moeda(liquido)}")

    cmb_status = st.selectbox(
        "Status",
        db.listar_opcoes("status") or ["Pago"],
        index=((db.listar_opcoes("status") or ["Pago"]).index(
            lancamento["status_pagamento"]) if lancamento is not None else 0),
        key=f"lf_status_{lid}")
    ed_obs = st.text_area(
        "Observação",
        value=(lancamento["observacao"] or "" if lancamento is not None
               else ""),
        key=f"lf_obs_{lid}")

    if st.button("Salvar", type="primary", icon=":material/save:",
                 width="stretch"):
        nome_final = (outro_nome.strip() if outro_nome.strip()
                      else (cmb_nome if cmb_nome != "(nenhum)" else ""))
        if bruto_num is None or desc_num is None:
            st.error("Informe valores numéricos válidos.")
            st.stop()
        if not nome_final:
            st.error("Informe o nome do funcionário.")
            st.stop()
        dados = (
            er_data.isoformat(),
            nome_final,
            cmb_tipo,
            bruto_num,
            desc_num,
            _calcular_liquido(bruto_num, desc_num),
            cmb_status,
            ed_obs.strip(),
        )
        if lancamento is None:
            db.criar_lancamento_func(*dados)
            st.toast("Lançamento criado com sucesso.")
        else:
            db.atualizar_lancamento_func(lancamento["id"], *dados)
            st.toast("Lançamento atualizado com sucesso.")
        st.rerun()


@st.dialog("Confirmar exclusão")
def confirmar_exclusao(lancamento):
    st.write(
        f'Excluir lançamento de {lancamento["nome_funcionario"]} em '
        f'{str(lancamento["data"])[:10]} '
        f'({fmt_moeda(lancamento["valor_liquido"])})?')
    linha = st.container(horizontal=True, horizontal_alignment="right")
    if linha.button("Cancelar"):
        st.rerun()
    if linha.button("Excluir", type="primary", icon=":material/delete:"):
        db.deletar_lancamento_func(lancamento["id"])
        st.toast("Registro excluído.")
        st.rerun()


@st.dialog("Gerenciar Funcionários", width="large")
def gerenciar_funcionarios():
    modo = st.session_state.get("func_modo", "lista")
    if modo == "form":
        funcionario = st.session_state.get("func_editando")
        fid = ("novo" if funcionario is None
               else str(funcionario["id"]))
        ed_nome = st.text_input(
            "Nome", value=(funcionario["nome"] if funcionario else ""),
            placeholder="Nome completo", key=f"gf_nome_{fid}")
        ed_cargo = st.text_input(
            "Cargo", value=((funcionario["cargo"] or "") if funcionario
                            else ""),
            placeholder="Ex.: Auxiliar de limpeza", key=f"gf_cargo_{fid}")
        ed_telefone = st.text_input(
            "Telefone",
            value=((funcionario["telefone"] or "") if funcionario else ""),
            placeholder="(00) 00000-0000", key=f"gf_tel_{fid}")
        padrao_admissao = (
            date.fromisoformat(str(funcionario["data_admissao"])[:10])
            if (funcionario is not None
                and str(funcionario["data_admissao"] or "")[:10])
            else datetime.now().date())
        er_admissao = st.date_input(
            "Data de admissão", value=padrao_admissao,
            format="DD/MM/YYYY", key=f"gf_adm_{fid}")
        ed_obs = st.text_area(
            "Observações",
            value=((funcionario["observacoes"] or "") if funcionario
                   else ""), key=f"gf_obs_{fid}")
        chk_ativo = st.checkbox(
            "Funcionário ativo",
            value=bool(funcionario["ativo"]) if funcionario else True,
            key=f"gf_ativo_{fid}")

        col1, col2 = st.columns(2)
        if col1.button("Salvar", type="primary", icon=":material/save:",
                       width="stretch"):
            nome = ed_nome.strip()
            if not nome:
                st.error("Informe o nome do funcionário.")
                st.stop()
            duplicados = [
                f for f in db.listar_funcionarios_todos()
                if f["nome"].strip().lower() == nome.lower()]
            if duplicados and (funcionario is None
                               or duplicados[0]["id"]
                               != funcionario["id"]):
                st.error("Já existe um funcionário com esse nome.")
                st.stop()
            dados = (
                nome,
                ed_cargo.strip(),
                ed_telefone.strip(),
                er_admissao.isoformat(),
                ed_obs.strip(),
                1 if chk_ativo else 0,
            )
            if funcionario is None:
                db.criar_funcionario(*dados)
                st.toast("Funcionário cadastrado com sucesso.")
            else:
                db.atualizar_funcionario(funcionario["id"], *dados)
                st.toast("Funcionário atualizado com sucesso.")
            st.session_state.func_modo = "lista"
            st.rerun()
        if col2.button("Voltar", width="stretch"):
            st.session_state.func_modo = "lista"
            st.rerun()
        return

    todos = db.listar_funcionarios_todos()
    if not todos:
        st.info("Nenhum funcionário cadastrado ainda.")
    nomes = {
        f["id"]: (f"{f['nome']}"
                  + (f" - {f['cargo']}" if (f["cargo"] or "") else "")
                  + f" ({'ativo' if f['ativo'] else 'inativo'})")
        for f in todos
    }
    escolha = st.selectbox(
        "Funcionários",
        ["(selecione)"] + [nomes[f["id"]] for f in todos],
        key="func_sel")
    selecionado = None
    if escolha != "(selecione)":
        selecionado = next(
            (f for f in todos if nomes[f["id"]] == escolha), None)

    linha = st.container(horizontal=True)
    if linha.button("+ Cadastrar", type="primary",
                    icon=":material/person_add:"):
        st.session_state.func_modo = "form"
        st.session_state.func_editando = None
        st.rerun()
    if linha.button("Editar", icon=":material/edit:", disabled=selecionado is None):
        st.session_state.func_modo = "form"
        st.session_state.func_editando = selecionado
        st.rerun()
    if linha.button("Excluir", icon=":material/delete:",
                    disabled=selecionado is None):
        db.deletar_funcionario(selecionado["id"])
        st.toast(f'Funcionário "{selecionado["nome"]}" excluído.')
        st.rerun()


if novo_btn:
    formulario_lancamento(None)

if editar_btn:
    if lancamento_id is None:
        st.info("Selecione um lançamento na tabela para editar.")
    else:
        formulario_lancamento(db.buscar_lancamento_func(lancamento_id))

if excluir_btn:
    if lancamento_id is None:
        st.info("Selecione um lançamento na tabela para excluir.")
    else:
        confirmar_exclusao(db.buscar_lancamento_func(lancamento_id))

if gerenciar_btn:
    st.session_state.setdefault("func_modo", "lista")
    gerenciar_funcionarios()

with st.expander("Exportar Excel"):
    bytes_excel = exportar_funcionarios_bytes()
    st.download_button(
        "Exportar Excel",
        data=bytes_excel or b"",
        file_name=nome_arquivo("lancamentos_funcionarios"),
        mime="application/vnd.openxmlformats-officedocument"
             ".spreadsheetml.sheet",
        icon=":material/download:",
        disabled=bytes_excel is None,
    )
