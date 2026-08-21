# -*- coding: utf-8 -*-
"""
reports/pdf_generator.py - Geração de relatórios PDF com ReportLab.
Todos os relatórios incluem o cabeçalho da marca "Help! Limpeza Especializada"
com as cores oficiais (roxo #6B52B3 e dourado #DDAA33) e o logo da empresa.
"""

import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

import database as db
from styles import montar_pdf_palette

EMPRESA = "Help! Limpeza Especializada"


def _caminho_logo():
    """Localiza o logo da empresa (mesma preferência do app desktop).

    Quando congelado (PyInstaller), procura primeiro no _MEIPASS e depois
    junto ao executável."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidatos = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidatos.append(meipass)
        candidatos.append(os.path.dirname(sys.executable))
    else:
        candidatos.append(base)
    for raiz in candidatos:
        for nome in ("logo_help.png", "logo.png"):
            caminho = os.path.join(raiz, nome)
            if os.path.exists(caminho):
                return caminho
    return None


LOGO_PATH = _caminho_logo()

_logo_cache = None


def _logo_imagem():
    """Retorna (ImageReader, (largura_px, altura_px)) do logo recortado
    exatamente sobre a arte visível (ignorando transpência), para o desenho
    caber perfeitamente no centro da moldura branca. Cacheado."""
    global _logo_cache
    if _logo_cache is not None:
        return _logo_cache
    if not LOGO_PATH:
        return None
    try:
        from reportlab.lib.utils import ImageReader
        from PIL import Image
        with Image.open(LOGO_PATH) as img:
            rgba = img.convert("RGBA")
            alpha = rgba.split()[3]
            # bbox dos pixels com alpha significativo
            bbox = alpha.point(lambda a: 255 if a > 100 else 0).getbbox()
            if bbox:
                img = img.crop(bbox)
            # remove margens internas quase invisíveis na arte
            rgba2 = img.convert("RGBA")
            alpha2 = rgba2.split()[3]
            bbox2 = alpha2.point(lambda a: 255 if a > 60 else 0).getbbox()
            if bbox2:
                img = img.crop(bbox2)
            tamanho = img.size
        _logo_cache = (ImageReader(img), tamanho)
    except Exception:
        _logo_cache = None
    return _logo_cache

P = montar_pdf_palette()


# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
def _estilos():
    styles = {
        "titulo": ParagraphStyle(
            "titulo", fontName="Helvetica-Bold", fontSize=16,
            textColor=P["roxo"], alignment=1, spaceAfter=2),
        "subtitulo": ParagraphStyle(
            "subtitulo", fontName="Helvetica-Bold", fontSize=12,
            textColor=P["roxo"], spaceBefore=6, spaceAfter=6),
        "normal": ParagraphStyle(
            "normal", fontName="Helvetica", fontSize=9,
            textColor=P["texto"], leading=12),
        "resumo": ParagraphStyle(
            "resumo", fontName="Helvetica-Bold", fontSize=10,
            textColor=P["texto"]),
    }
    return styles


def _fmt_data(valor):
    """Converte 'AAAA-MM-DD' em 'DD/MM/AAAA'."""
    texto = str(valor)[:10]
    if len(texto) == 10 and texto[4] == "-":
        return "%s/%s/%s" % (texto[8:10], texto[5:7], texto[0:4])
    return texto


def _base_page(canvas, doc, frame_=None):
    """Desenha o cabeçalho e rodapé com as cores da marca e o logo."""
    canvas = canvas
    centro_y = doc.pagesize[1] - 12 * mm
    barra_topo = doc.pagesize[1] - 24 * mm

    # Faixa roxa do topo ---------------------------------------------------
    canvas.saveState()
    canvas.setFillColor(P["roxo"])
    canvas.rect(0, barra_topo, doc.pagesize[0], 24 * mm, fill=1, stroke=0)
    canvas.setFillColor(P["dourado"])
    canvas.rect(0, barra_topo - 0.8 * mm, doc.pagesize[0], 0.8 * mm,
                fill=1, stroke=0)

    # Logo da empresa (dentro da caixa branca, centralizado) ---------------
    texto_x = 12 * mm
    info_logo = _logo_imagem()
    if info_logo:
        try:
            reader_logo, (px_larg, px_alt) = info_logo
            # caixa branca no canto esquerdo do cabeçalho
            bw = 34 * mm
            bh = 22 * mm
            bx = 10 * mm
            by = barra_topo + 1 * mm
            # logo mantendo proporção, cabendo dentro de 30 x 16 mm
            escala = min(30 * mm / px_larg, 16 * mm / px_alt)
            larg_logo = px_larg * escala
            alt_logo = px_alt * escala
            # canto inferior esquerdo = centro da caixa - metade do logo
            x0 = bx + bw / 2.0 - larg_logo / 2.0
            y0 = by + bh / 2.0 - alt_logo / 2.0
            canvas.setFillColor(colors.white)
            canvas.roundRect(bx, by, bw, bh, 4 * mm, fill=1, stroke=0)
            canvas.drawImage(reader_logo, x0, y0, larg_logo, alt_logo,
                             mask="auto", preserveAspectRatio=True,
                             anchor="sw")
            texto_x = bx + bw + 8 * mm
        except Exception:
            pass

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 15)
    canvas.drawString(texto_x, centro_y - 4.5 * mm, EMPRESA)

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(doc.pagesize[0] - 12 * mm,
                           doc.pagesize[1] - 12 * mm,
                           datetime.now().strftime("%d/%m/%Y %H:%M"))
    canvas.restoreState()

    # Rodapé ---------------------------------------------------------------
    canvas.saveState()
    canvas.setStrokeColor(P["borda"])
    canvas.line(12 * mm, 12 * mm, doc.pagesize[0] - 12 * mm, 12 * mm)
    canvas.setFillColor(P["texto"])
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        doc.pagesize[0] / 2, 8 * mm,
        f"{EMPRESA} - Relatório gerado em {datetime.now():%d/%m/%Y %H:%M} "
        f"| Página {doc.page}")
    canvas.restoreState()


def _build(doc, historia):
    """Compila o documento usando o cabeçalho/rodapé padrão da marca."""
    doc.build(historia,
              onFirstPage=_base_page,
              onLaterPages=_base_page)


def _tabela(dados, larguras):
    """Cria uma tabela com o estilo padrão da marca."""
    tbl = Table(dados, colWidths=larguras, repeatRows=1)
    estilos = [
        ("BACKGROUND", (0, 0), (-1, 0), P["roxo"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, -1), (-1, -1), P["dourado"]),
        ("GRID", (0, 0), (-1, -2), 0.4, P["borda"]),
        ("GRID", (0, -1), (-1, -1), 0.6, P["dourado"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2),
         [colors.white, P["fundo"]]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    tbl.setStyle(TableStyle(estilos))
    return tbl


# ---------------------------------------------------------------------------
# Relatório 1 - Gastos Aureni
# ---------------------------------------------------------------------------
def gerar_pdf_gastos(caminho, de=None, ate=None, categorias=None,
                     parent=None):
    clausulas = []
    params = []
    if de:
        clausulas.append("data >= ?")
        params.append(de)
    if ate:
        clausulas.append("data <= ?")
        params.append(ate)
    if categorias:
        clausulas.append("categoria IN (%s)" % ",".join("?" * len(categorias)))
        params.extend(categorias)
    where = " AND ".join(clausulas) if clausulas else ""
    gastos = db.listar_gastos(where, params)

    doc = SimpleDocTemplate(
        caminho, pagesize=A4,
        topMargin=30 * mm, bottomMargin=18 * mm,
        leftMargin=12 * mm, rightMargin=12 * mm,
        title=f"Relatório de Receitas e Despesas - {EMPRESA}",
        author=EMPRESA)
    S = _estilos()

    historia = []
    historia.append(Paragraph(EMPRESA, S["titulo"]))
    historia.append(Paragraph(
        "Relatório de Receitas e Despesas (Aureni)", S["subtitulo"]))

    filtro_txt = ""
    if de:
        filtro_txt += f" de {_fmt_data(de)}"
    if ate:
        filtro_txt += f" até {_fmt_data(ate)}"
    if categorias:
        filtro_txt += f" | Categorias: {', '.join(categorias)}"
    if not filtro_txt:
        filtro_txt = " (período completo)"
    historia.append(Paragraph(f"Período: <b>{filtro_txt}</b>", S["normal"]))

    if not gastos:
        historia.append(Paragraph("Nenhum gasto encontrado para os filtros "
                                  "informados.", S["normal"]))
        _build(doc, historia)
        return len(gastos)

    # Tabela ---------------------------------------------------------------
    dados_tabela = [[Paragraph("<b>Data</b>", S["normal"]),
                     Paragraph("<b>Tipo</b>", S["normal"]),
                     Paragraph("<b>Descrição</b>", S["normal"]),
                     Paragraph("<b>Categoria</b>", S["normal"]),
                     Paragraph("<b>Valor (R$)</b>", S["normal"]),
                     Paragraph("<b>Forma de pagamento</b>", S["normal"])]]
    receitas_total = 0.0
    despesas_total = 0.0
    for g in gastos:
        valor = f"{g['valor']:,.2f}".replace(",", ".")
        dados_tabela.append([
            Paragraph(_fmt_data(g["data"]), S["normal"]),
            Paragraph(g["tipo_operacao"], S["normal"]),
            Paragraph(g["descricao"], S["normal"]),
            Paragraph(g["categoria"], S["normal"]),
            Paragraph(valor, S["normal"]),
            Paragraph(g["forma_pagamento"] or "-", S["normal"]),
        ])
        if g["tipo_operacao"] == "Recebimento":
            receitas_total += g["valor"]
        else:
            despesas_total += g["valor"]

    dados_tabela.append([
        Paragraph("<b>Total</b>", S["resumo"]), "", "", "",
        Paragraph(f"<b>{receitas_total + despesas_total:,.2f}</b>".replace(",", "."),
                  S["resumo"]),
        ""])

    tabela = _tabela(dados_tabela,
                     larguras=[19 * mm, 24 * mm, 48 * mm, 27 * mm,
                               29 * mm, 34 * mm])
    historia.append(KeepTogether([Spacer(1, 4), tabela]))

    resumo = Paragraph(
        f"<b>Total de receitas: R$ {receitas_total:,.2f}</b> | "
        f"<b>Total de despesas: R$ {despesas_total:,.2f}</b>",
        S["subtitulo"])
    historia.append(Spacer(1, 6))
    historia.append(resumo)

    _build(doc, historia)
    return len(gastos)


# ---------------------------------------------------------------------------
# Relatório 2 - Pagamentos por Funcionário
# ---------------------------------------------------------------------------
def gerar_pdf_funcionarios(caminho, de=None, ate=None, funcionario=None,
                           parent=None):
    clausulas = []
    params = []
    if de:
        clausulas.append("data >= ?")
        params.append(de)
    if ate:
        clausulas.append("data <= ?")
        params.append(ate)
    if funcionario:
        clausulas.append("nome_funcionario = ?")
        params.append(funcionario)
    where = " AND ".join(clausulas) if clausulas else ""
    lancamentos = db.listar_lancamentos_func(where, params)

    doc = SimpleDocTemplate(
        caminho, pagesize=A4,
        topMargin=30 * mm, bottomMargin=18 * mm,
        leftMargin=12 * mm, rightMargin=12 * mm,
        title=f"Extrato de Funcionários - {EMPRESA}",
        author=EMPRESA)
    S = _estilos()

    historia = []
    historia.append(Paragraph(EMPRESA, S["titulo"]))
    titulo = ("Extrato de Vencimentos" if funcionario else
              "Extrato Geral de Vencimentos")
    if funcionario:
        titulo += f" - {funcionario}"
    historia.append(Paragraph(titulo, S["subtitulo"]))

    filtro_txt = ""
    if de:
        filtro_txt += f" de {_fmt_data(de[:10])}"
    if ate:
        filtro_txt += f" até {_fmt_data(ate[:10])}"
    if not filtro_txt:
        filtro_txt = " (período completo)"
    historia.append(Paragraph(f"Período:<b>{filtro_txt}</b>", S["normal"]))

    if not lancamentos:
        historia.append(Paragraph("Nenhum lançamento encontrado para os "
                                  "filtros informados.", S["normal"]))
        _build(doc, historia)
        return 0

    # Separa por funcionário (agrupado) -----------------------------------
    por_func = {}
    for l in lancamentos:
        por_func.setdefault(l["nome_funcionario"], []).append(l)

    for nome, itens in sorted(por_func.items()):
        extratos = []
        extratos.append(Paragraph(f"Funcionário: <b>{nome}</b>", S["subtitulo"]))
        dados_tabela = [[Paragraph("<b>Data</b>", S["normal"]),
                         Paragraph("<b>Tipo</b>", S["normal"]),
                         Paragraph("<b>Valor bruto (R$)</b>", S["normal"]),
                         Paragraph("<b>Descontos (R$)</b>", S["normal"]),
                         Paragraph("<b>Valor líquido (R$)</b>", S["normal"]),
                         Paragraph("<b>Status</b>", S["normal"])]]
        total_bruto = total_desc = total_liq = 0.0
        for l in itens:
            dados_tabela.append([
                Paragraph(_fmt_data(l["data"]), S["normal"]),
                Paragraph(l["tipo_operacao"], S["normal"]),
                Paragraph(f"{l['valor_bruto']:,.2f}", S["normal"]),
                Paragraph(f"{l['descontos']:,.2f}", S["normal"]),
                Paragraph(f"{l['valor_liquido']:,.2f}", S["normal"]),
                Paragraph(l["status_pagamento"], S["normal"]),
            ])
            total_bruto += l["valor_bruto"]
            total_desc += l["descontos"]
            total_liq += l["valor_liquido"]

        dados_tabela.append([
            Paragraph("<b>Totais</b>", S["resumo"]), "",
            Paragraph(f"<b>{total_bruto:,.2f}</b>", S["resumo"]),
            Paragraph(f"<b>{total_desc:,.2f}</b>", S["resumo"]),
            Paragraph(f"<b>{total_liq:,.2f}</b>", S["resumo"]), ""])

        tabela = _tabela(dados_tabela,
                         larguras=[19 * mm, 27 * mm, 31 * mm,
                                   31 * mm, 31 * mm, 28 * mm])
        extratos.append(Spacer(1, 3))
        extratos.append(tabela)
        extratos.append(Spacer(1, 8))
        historia.append(KeepTogether(extratos))

    resumo = Paragraph(
        f"<b>Total geral de vencimentos (líquido): "
        f"R$ {sum(l['valor_liquido'] for l in lancamentos):,.2f}</b>",
        S["subtitulo"])
    historia.append(Spacer(1, 6))
    historia.append(resumo)

    _build(doc, historia)
    return len(lancamentos)


# ---------------------------------------------------------------------------
# Relatório 3 - Resumo financeiro mensal (dashboard em PDF)
# ---------------------------------------------------------------------------
def gerar_pdf_resumo(caminho, ano_mes, parent=None):
    resumo = db.resumo_mes(ano_mes)
    serie = db.serie_mensal(6)

    doc = SimpleDocTemplate(
        caminho, pagesize=A4,
        topMargin=30 * mm, bottomMargin=18 * mm,
        leftMargin=12 * mm, rightMargin=12 * mm,
        title=f"Resumo Financeiro - {EMPRESA}",
        author=EMPRESA)
    S = _estilos()

    historia = []
    historia.append(Paragraph(EMPRESA, S["titulo"]))
    historia.append(Paragraph(f"Resumo Financeiro - {ano_mes[:4]}/{ano_mes[5:7]}",
                              S["subtitulo"]))

    dados = [
        ["Descrição", "Valor (R$)"],
        ["Receitas", f"{resumo['receitas']:,.2f}"],
        ["Despesas com gastos (Aureni)", f"{resumo['despesas_gastos']:,.2f}"],
        ["Pagamentos de funcionários", f"{resumo['pagamentos_funcionarios']:,.2f}"],
        ["Despesas totais", f"{resumo['despesa_total']:,.2f}"],
        ["Saldo do mês", f"{resumo['saldo']:,.2f}"],
    ]
    tabela = Table(dados, colWidths=[90 * mm, 90 * mm])
    stilo = [
        ("BACKGROUND", (0, 0), (-1, 0), P["roxo"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, P["borda"]),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, P["fundo"]]),
        ("BACKGROUND", (0, -1), (-1, -1), P["dourado"]),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    tabela.setStyle(TableStyle(stilo))
    historia.append(tabela)
    historia.append(Spacer(1, 14))

    historia.append(Paragraph("Evolução - últimos 6 meses", S["subtitulo"]))
    dados2 = [["Mês", "Receitas (R$)", "Despesas (R$)"]]
    for m in serie:
        dados2.append([m["label"], f"{m['receitas']:,.2f}",
                       f"{m['despesas']:,.2f}"])
    tabela2 = Table(dados2, colWidths=[60 * mm, 60 * mm, 60 * mm])
    stilo2 = [
        ("BACKGROUND", (0, 0), (-1, 0), P["roxo"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, P["borda"]),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, P["fundo"]]),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    tabela2.setStyle(TableStyle(stilo2))
    historia.append(tabela2)

    _build(doc, historia)
    return True