# -*- coding: utf-8 -*-
"""
database.py - Camada de acesso ao banco de dados SQLite do sistema
Help! Limpeza Especializada.

Banco: help_sistema.db
Tabelas:
  1) gastos_aureni
  2) recebimentos_pagamentos_funcionarios
"""

import os
import sqlite3
import sys
from datetime import datetime


def _base_dir():
    """Diretório base do app (junto ao executável quando congelado)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DB_NAME = os.path.join(_base_dir(), "help_sistema.db")

# ---------------------------------------------------------------------------
# Script SQL de criação das tabelas
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS gastos_aureni (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    data             TEXT NOT NULL,
    tipo_operacao    TEXT NOT NULL DEFAULT 'Pagamento',
    descricao        TEXT NOT NULL,
    categoria        TEXT NOT NULL DEFAULT 'Geral',
    valor            REAL NOT NULL DEFAULT 0,
    forma_pagamento  TEXT DEFAULT 'Dinheiro',
    observacoes      TEXT
);

CREATE TABLE IF NOT EXISTS recebimentos_pagamentos_funcionarios (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    data             TEXT NOT NULL,
    nome_funcionario TEXT NOT NULL,
    tipo_operacao    TEXT NOT NULL DEFAULT 'Pagamento',
    valor_bruto      REAL NOT NULL DEFAULT 0,
    descontos        REAL NOT NULL DEFAULT 0,
    valor_liquido    REAL NOT NULL DEFAULT 0,
    status_pagamento TEXT NOT NULL DEFAULT 'Pendente',
    observacao       TEXT
);

CREATE TABLE IF NOT EXISTS funcionarios (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nome             TEXT NOT NULL UNIQUE,
    cargo            TEXT DEFAULT '',
    telefone         TEXT DEFAULT '',
    data_admissao    TEXT DEFAULT '',
    observacoes      TEXT DEFAULT '',
    ativo            INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS opcoes_cadastro (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    grupo  TEXT NOT NULL,
    valor  TEXT NOT NULL,
    ordem  INTEGER NOT NULL DEFAULT 0,
    UNIQUE (grupo, valor)
);

CREATE INDEX IF NOT EXISTS idx_gastos_data          ON gastos_aureni(data);
CREATE INDEX IF NOT EXISTS idx_gastos_categoria     ON gastos_aureni(categoria);
CREATE INDEX IF NOT EXISTS idx_func_data            ON recebimentos_pagamentos_funcionarios(data);
CREATE INDEX IF NOT EXISTS idx_func_nome            ON recebimentos_pagamentos_funcionarios(nome_funcionario);
"""


def get_connection():
    """Abre uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Cria o banco de dados e as tabelas caso ainda não existam."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        _migrar(conn)
    finally:
        conn.close()
    return DB_NAME


def _migrar(conn):
    """Aplica migrações em bancos já existentes (versões anteriores)."""
    cols_gastos = [r[1] for r in conn.execute("PRAGMA table_info(gastos_aureni)")]
    if "tipo_operacao" not in cols_gastos:
        conn.execute(
            "ALTER TABLE gastos_aureni "
            "ADD COLUMN tipo_operacao TEXT NOT NULL DEFAULT 'Pagamento'")
        conn.commit()

    cols_func = [r[1] for r in conn.execute("PRAGMA table_info(funcionarios)")]
    if "cargo" not in cols_func:
        conn.execute(
            "ALTER TABLE funcionarios "
            "ADD COLUMN cargo TEXT DEFAULT ''")
        conn.execute(
            "ALTER TABLE funcionarios "
            "ADD COLUMN telefone TEXT DEFAULT ''")
        conn.execute(
            "ALTER TABLE funcionarios "
            "ADD COLUMN data_admissao TEXT DEFAULT ''")
        conn.execute(
            "ALTER TABLE funcionarios "
            "ADD COLUMN observacoes TEXT DEFAULT ''")
        conn.execute(
            "ALTER TABLE funcionarios "
            "ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1")
        conn.commit()

    conn.execute(
        """INSERT OR IGNORE INTO funcionarios (nome)
           SELECT DISTINCT nome_funcionario
           FROM recebimentos_pagamentos_funcionarios""")
    conn.commit()

    _semear_opcoes(conn)


# Padrões iniciais e fontes das listas de opções cadastráveis
OPCOES_DEFAULTS = {
    "tipo_operacao": ["Pagamento", "Recebimento", "Adiantamento"],
    "status": ["Pago", "Pendente"],
    "categoria": ["Geral", "Produtos de Limpeza", "Equipamentos",
                  "Transporte", "Alimentação", "Salários", "Marketing",
                  "Manutenção", "Outros"],
    "forma_pagamento": ["Dinheiro", "Pix", "Crédito", "Débito", "Boleto",
                        "Cheque"],
}

OPCOES_EXISTENTES = {
    "tipo_operacao": (
        "SELECT DISTINCT tipo_operacao FROM gastos_aureni "
        "UNION SELECT DISTINCT tipo_operacao "
        "FROM recebimentos_pagamentos_funcionarios"),
    "status": "SELECT DISTINCT status_pagamento "
              "FROM recebimentos_pagamentos_funcionarios",
    "categoria": "SELECT DISTINCT categoria FROM gastos_aureni",
    "forma_pagamento": "SELECT DISTINCT forma_pagamento FROM gastos_aureni",
}


def _semear_opcoes(conn):
    """Cria as listas padrão e inclui valores já usados nos dados."""
    for grupo, padrões in OPCOES_DEFAULTS.items():
        existentes = conn.execute(
            "SELECT COUNT(*) FROM opcoes_cadastro WHERE grupo=?",
            (grupo,)).fetchone()[0]
        if existentes == 0:
            for i, valor in enumerate(padrões):
                conn.execute(
                    "INSERT OR IGNORE INTO opcoes_cadastro "
                    "(grupo, valor, ordem) VALUES (?,?,?)",
                    (grupo, valor, i))
        for (valor,) in conn.execute(OPCOES_EXISTENTES[grupo]).fetchall():
            if valor:
                conn.execute(
                    """INSERT OR IGNORE INTO opcoes_cadastro
                       (grupo, valor, ordem)
                       VALUES (?, ?, (SELECT COALESCE(MAX(ordem),0)+1
                                      FROM opcoes_cadastro WHERE grupo=?))""",
                    (grupo, str(valor), grupo))
    conn.commit()


def _normalize_date(value):
    """Aceita datetime, date ou string ISO e devolve 'AAAA-MM-DD'."""
    if value is None or value == "":
        return datetime.now().date().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return datetime.now().date().isoformat()
    except Exception:
        return text


# ===========================================================================
# CRUD - gastos_aureni
# ===========================================================================
def criar_gasto(data, descricao, categoria, valor, forma_pagamento,
                observacoes="", tipo_operacao="Pagamento"):
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO gastos_aureni
               (data, tipo_operacao, descricao, categoria, valor,
                forma_pagamento, observacoes)
               VALUES (?,?,?,?,?,?,?)""",
            (_normalize_date(data), tipo_operacao, descricao, categoria,
             float(valor or 0), forma_pagamento, observacoes or ""),
        )
        _garantir_opcao(conn, "tipo_operacao", tipo_operacao)
        _garantir_opcao(conn, "categoria", categoria)
        _garantir_opcao(conn, "forma_pagamento", forma_pagamento)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _garantir_opcao(conn, grupo, valor):
    """Registra o valor na lista de opções, caso ainda não exista."""
    if valor is None:
        return
    conn.execute(
        """INSERT OR IGNORE INTO opcoes_cadastro (grupo, valor, ordem)
           VALUES (?, ?,
                   (SELECT COALESCE(MAX(ordem),0)+1
                    FROM opcoes_cadastro WHERE grupo=?))""",
        (grupo, str(valor), grupo))


def listar_gastos(filtro_where="", params=()):
    conn = get_connection()
    try:
        sql = "SELECT * FROM gastos_aureni"
        if filtro_where:
            sql += " WHERE " + filtro_where
        sql += " ORDER BY data DESC, id DESC"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def buscar_gasto(gasto_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM gastos_aureni WHERE id = ?", (gasto_id,)
        ).fetchone()
    finally:
        conn.close()


def atualizar_gasto(gasto_id, data, descricao, categoria, valor,
                    forma_pagamento, observacoes="", tipo_operacao="Pagamento"):
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE gastos_aureni SET
               data=?, tipo_operacao=?, descricao=?, categoria=?, valor=?,
               forma_pagamento=?, observacoes=?
               WHERE id=?""",
            (_normalize_date(data), tipo_operacao, descricao, categoria,
             float(valor or 0), forma_pagamento, observacoes or "", gasto_id),
        )
        _garantir_opcao(conn, "tipo_operacao", tipo_operacao)
        _garantir_opcao(conn, "categoria", categoria)
        _garantir_opcao(conn, "forma_pagamento", forma_pagamento)
        conn.commit()
    finally:
        conn.close()


def deletar_gasto(gasto_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM gastos_aureni WHERE id=?", (gasto_id,))
        conn.commit()
    finally:
        conn.close()


# ===========================================================================
# CRUD - recebimentos_pagamentos_funcionarios
# ===========================================================================
def criar_lancamento_func(data, nome_funcionario, tipo_operacao, valor_bruto,
                          descontos, valor_liquido, status_pagamento,
                          observacao=""):
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO recebimentos_pagamentos_funcionarios
               (data, nome_funcionario, tipo_operacao, valor_bruto, descontos,
                valor_liquido, status_pagamento, observacao)
               VALUES (?,?,?,?,?,?,?,?)""",
            (_normalize_date(data), nome_funcionario, tipo_operacao,
             float(valor_bruto or 0), float(descontos or 0),
             float(valor_liquido if valor_liquido is not None else 0),
             status_pagamento, observacao or ""),
        )
        _garantir_opcao(conn, "tipo_operacao", tipo_operacao)
        _garantir_opcao(conn, "status", status_pagamento)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def listar_lancamentos_func(filtro_where="", params=()):
    conn = get_connection()
    try:
        sql = "SELECT * FROM recebimentos_pagamentos_funcionarios"
        if filtro_where:
            sql += " WHERE " + filtro_where
        sql += " ORDER BY data DESC, id DESC"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def buscar_lancamento_func(lancamento_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM recebimentos_pagamentos_funcionarios WHERE id=?",
            (lancamento_id,),
        ).fetchone()
    finally:
        conn.close()


def atualizar_lancamento_func(lancamento_id, data, nome_funcionario,
                              tipo_operacao, valor_bruto, descontos,
                              valor_liquido, status_pagamento, observacao=""):
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE recebimentos_pagamentos_funcionarios SET
               data=?, nome_funcionario=?, tipo_operacao=?, valor_bruto=?,
               descontos=?, valor_liquido=?, status_pagamento=?, observacao=?
               WHERE id=?""",
            (_normalize_date(data), nome_funcionario, tipo_operacao,
             float(valor_bruto or 0), float(descontos or 0),
             float(valor_liquido if valor_liquido is not None else 0),
             status_pagamento, observacao or "", lancamento_id),
        )
        _garantir_opcao(conn, "tipo_operacao", tipo_operacao)
        _garantir_opcao(conn, "status", status_pagamento)
        conn.commit()
    finally:
        conn.close()


def deletar_lancamento_func(lancamento_id):
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM recebimentos_pagamentos_funcionarios WHERE id=?",
            (lancamento_id,),
        )
        conn.commit()
    finally:
        conn.close()


# ===========================================================================
# CRUD - funcionarios
# ===========================================================================
def criar_funcionario(nome, cargo="", telefone="", data_admissao="",
                      observacoes="", ativo=1):
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO funcionarios
               (nome, cargo, telefone, data_admissao, observacoes, ativo)
               VALUES (?,?,?,?,?,?)""",
            (nome.strip(), cargo.strip(), telefone.strip(),
             _normalize_date(data_admissao) if data_admissao else
             datetime.now().date().isoformat(),
             observacoes.strip(), 1 if ativo else 0),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def listar_funcionarios(ativos=True):
    """Retorna a lista de nomes de funcionários cadastrados."""
    conn = get_connection()
    try:
        sql = "SELECT nome FROM funcionarios"
        if ativos:
            sql += " WHERE ativo = 1"
        sql += " ORDER BY nome"
        return [r["nome"] for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def listar_funcionarios_todos():
    """Retorna todos os registros de funcionários (para a gestão)."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM funcionarios ORDER BY nome"
        ).fetchall()
    finally:
        conn.close()


def buscar_funcionario(funcionario_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM funcionarios WHERE id = ?", (funcionario_id,)
        ).fetchone()
    finally:
        conn.close()


def atualizar_funcionario(funcionario_id, nome, cargo="", telefone="",
                          data_admissao="", observacoes="", ativo=1):
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE funcionarios SET
               nome=?, cargo=?, telefone=?, data_admissao=?, observacoes=?,
               ativo=? WHERE id=?""",
            (nome.strip(), cargo.strip(), telefone.strip(),
             _normalize_date(data_admissao) if data_admissao else
             datetime.now().date().isoformat(),
             observacoes.strip(), 1 if ativo else 0, funcionario_id),
        )
        conn.commit()
    finally:
        conn.close()


def deletar_funcionario(funcionario_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM funcionarios WHERE id=?", (funcionario_id,))
        conn.commit()
    finally:
        conn.close()


# ===========================================================================
# CRUD - opcoes_cadastro (listas cadastráveis)
# ===========================================================================
def listar_opcoes(grupo):
    """Retorna os valores de uma lista (tipo, status, categoria, forma...)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT valor FROM opcoes_cadastro WHERE grupo=? "
            "ORDER BY ordem, id", (grupo,))
        return [r["valor"] for r in rows]
    finally:
        conn.close()


def listar_opcoes_todos(grupo):
    """Retorna as linhas completas de uma lista (id, grupo, valor)."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT id, grupo, valor FROM opcoes_cadastro WHERE grupo=? "
            "ORDER BY ordem, id", (grupo,)).fetchall()
    finally:
        conn.close()


def buscar_opcao(opcao_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT id, grupo, valor FROM opcoes_cadastro WHERE id=?",
            (opcao_id,)).fetchone()
    finally:
        conn.close()


def criar_opcao(grupo, valor):
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO opcoes_cadastro (grupo, valor, ordem)
               VALUES (?, ?,
                       (SELECT COALESCE(MAX(ordem),0)+1
                        FROM opcoes_cadastro WHERE grupo=?))""",
            (grupo, valor.strip(), grupo))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        conn.rollback()
        return None
    finally:
        conn.close()


def atualizar_opcao(opcao_id, valor):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE opcoes_cadastro SET valor=? WHERE id=?",
            (valor.strip(), opcao_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        conn.rollback()
        return False
    finally:
        conn.close()


def deletar_opcao(opcao_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM opcoes_cadastro WHERE id=?", (opcao_id,))
        conn.commit()
    finally:
        conn.close()


# ===========================================================================
# Consultas de apoio (dashboard / relatórios)
# ===========================================================================
def listar_categorias():
    """Retorna a lista de categorias cadastradas."""
    return listar_opcoes("categoria")


def resumo_mes(ano_mes):
    """Retorna resumo (receitas, despesas, saldo) de um mês 'AAAA-MM'."""
    conn = get_connection()
    try:
        receitas_func = conn.execute(
            """SELECT COALESCE(SUM(valor_liquido),0) AS total
               FROM recebimentos_pagamentos_funcionarios
               WHERE tipo_operacao = 'Recebimento'
                 AND substr(data,1,7) = ?""",
            (ano_mes,),
        ).fetchone()["total"]

        receitas_gastos = conn.execute(
            """SELECT COALESCE(SUM(valor),0) AS total
               FROM gastos_aureni
               WHERE tipo_operacao = 'Recebimento'
                 AND substr(data,1,7) = ?""",
            (ano_mes,),
        ).fetchone()["total"]

        despesas = conn.execute(
            """SELECT COALESCE(SUM(valor),0) AS total
               FROM gastos_aureni
               WHERE (tipo_operacao IS NULL OR tipo_operacao != 'Recebimento')
                 AND substr(data,1,7) = ?""",
            (ano_mes,),
        ).fetchone()["total"]

        pag_func = conn.execute(
            """SELECT COALESCE(SUM(valor_liquido),0) AS total
               FROM recebimentos_pagamentos_funcionarios
               WHERE tipo_operacao IN ('Pagamento','Adiantamento')
                 AND status_pagamento = 'Pago'
                 AND substr(data,1,7) = ?""",
            (ano_mes,),
        ).fetchone()["total"]

        despesa_total = despesas + pag_func
        return {
            "receitas": float(receitas_func) + float(receitas_gastos),
            "receitas_func": float(receitas_func),
            "receitas_gastos": float(receitas_gastos),
            "despesas_gastos": float(despesas),
            "pagamentos_funcionarios": float(pag_func),
            "despesa_total": float(despesa_total),
            "saldo": (float(receitas_func) + float(receitas_gastos))
                     - float(despesa_total),
        }
    finally:
        conn.close()


def total_geral():
    conn = get_connection()
    try:
        receitas_func = conn.execute(
            """SELECT COALESCE(SUM(valor_liquido),0)
               FROM recebimentos_pagamentos_funcionarios
               WHERE tipo_operacao='Recebimento'"""
        ).fetchone()[0]
        receitas_gastos = conn.execute(
            """SELECT COALESCE(SUM(valor),0)
               FROM gastos_aureni WHERE tipo_operacao='Recebimento'"""
        ).fetchone()[0]
        despesas = conn.execute(
            """SELECT COALESCE(SUM(valor),0)
               FROM gastos_aureni
               WHERE tipo_operacao IS NULL OR tipo_operacao != 'Recebimento'"""
        ).fetchone()[0]
        pag_func = conn.execute(
            """SELECT COALESCE(SUM(valor_liquido),0)
               FROM recebimentos_pagamentos_funcionarios
               WHERE tipo_operacao IN ('Pagamento','Adiantamento')
                 AND status_pagamento='Pago'"""
        ).fetchone()[0]
        return {
            "receitas": float(receitas_func or 0) + float(receitas_gastos or 0),
            "despesas": float(despesas or 0) + float(pag_func or 0),
        }
    finally:
        conn.close()


def serie_mensal(meses=6):
    """Retorna série mensal de receitas/despesas dos últimos N meses."""
    conn = get_connection()
    try:
        hoje = datetime.now()
        meses_lista = []
        for i in range(meses - 1, -1, -1):
            d = datetime(hoje.year, hoje.month, 1)
            ano, mes = (d.year, d.month)
            for _ in range(i):
                mes -= 1
                if mes == 0:
                    mes = 12
                    ano -= 1
            label = f"{ano}-{mes:02d}"
            receitas_func = conn.execute(
                """SELECT COALESCE(SUM(valor_liquido),0)
                   FROM recebimentos_pagamentos_funcionarios
                   WHERE tipo_operacao='Recebimento'
                     AND substr(data,1,7)=?""",
                (label,),
            ).fetchone()[0]
            receitas_gastos = conn.execute(
                """SELECT COALESCE(SUM(valor),0)
                   FROM gastos_aureni
                   WHERE tipo_operacao='Recebimento' AND substr(data,1,7)=?""",
                (label,),
            ).fetchone()[0]
            despesas = conn.execute(
                """SELECT COALESCE(SUM(valor),0)
                   FROM gastos_aureni
                   WHERE (tipo_operacao IS NULL OR tipo_operacao != 'Recebimento')
                     AND substr(data,1,7)=?""",
                (label,),
            ).fetchone()[0]
            pag_func = conn.execute(
                """SELECT COALESCE(SUM(valor_liquido),0)
                   FROM recebimentos_pagamentos_funcionarios
                   WHERE tipo_operacao IN ('Pagamento','Adiantamento')
                     AND status_pagamento='Pago' AND substr(data,1,7)=?""",
                (label,),
            ).fetchone()[0]
            meses_lista.append({
                "label": f"{mes:02d}/{ano}",
                "receitas": float(receitas_func or 0) + float(receitas_gastos or 0),
                "despesas": float(despesas or 0) + float(pag_func or 0),
            })
        return meses_lista
    finally:
        conn.close()
