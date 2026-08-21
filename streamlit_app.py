# -*- coding: utf-8 -*-
"""
streamlit_app.py - Versão web do sistema Help! Limpeza Especializada.

Mesma identidade visual e funcionalidades do app desktop (PyQt5),
executando no navegador via Streamlit.

Para executar:  streamlit run streamlit_app.py
"""

import base64
import os

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo_help.png")

st.set_page_config(
    page_title="Help! Limpeza Especializada",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else ":material/cleaning_services:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _logo_base64():
    try:
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""


_logo = _logo_base64()
_logo_img = (
    f'<img src="data:image/png;base64,{_logo}" '
    'style="height:50px;display:block;" alt="Logo Help"/>'
    if _logo else ""
)

st.html(
    """
    <div style="background:#6B52B3;border-bottom:4px solid #DDAA33;
                border-radius:0 0 12px 12px;padding:10px 22px;
                display:flex;align-items:center;gap:16px;">
      <div style="background:#FFFFFF;border-radius:8px;padding:4px 10px;
                  box-shadow:0 1px 3px rgba(0,0,0,.25);">{logo}</div>
      <div>
        <div style="color:#FFFFFF;font-size:22px;font-weight:700;line-height:1.25;">
          Help! Limpeza Especializada</div>
        <div style="color:#DDAA33;font-size:12px;font-style:italic;">
          Limpeza Especializada e Confiável</div>
      </div>
      <div style="margin-left:auto;color:#FFFFFF;font-size:11px;opacity:.85;
                  align-self:flex-start;">web v1.0</div>
    </div>
    """.replace("{logo}", _logo_img)
)


def _senha_obrigatoria():
    """Senha definida nos secrets (usada na versão publicada na nuvem).

    Sem o secret configurado (uso local), o acesso é livre."""
    try:
        return st.secrets.get("APP_SENHA")
    except Exception:
        return None


_senha = _senha_obrigatoria()
if _senha and not st.session_state.get("autenticado"):
    with st.container(border=True):
        st.markdown("##### Acesso restrito")
        entrada = st.text_input(
            "Senha", type="password", key="senha_acesso")
        if st.button("Entrar", type="primary", icon=":material/lock_open:"):
            if entrada == _senha:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

page = st.navigation(
    [
        st.Page(
            "app_pages/dashboard.py",
            title="Dashboard",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page(
            "app_pages/gastos.py",
            title="Receitas e Despesas Aureni",
            icon=":material/account_balance_wallet:",
        ),
        st.Page(
            "app_pages/funcionarios.py",
            title="Funcionários",
            icon=":material/groups:",
        ),
        st.Page(
            "app_pages/relatorios.py",
            title="Relatórios",
            icon=":material/description:",
        ),
        st.Page(
            "app_pages/cadastros.py",
            title="Cadastros",
            icon=":material/checklist:",
        ),
    ],
    position="top",
)

page.run()
