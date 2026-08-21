# -*- coding: utf-8 -*-
"""
styles.py - Paleta de cores da marca Help! Limpeza Especializada
usada em toda a interface gráfica e nos relatórios PDF.
"""

# Cores da marca ------------------------------------------------------------
ROXO_PRINCIPAL = "#6B52B3"
AMARELO_DOURADO = "#DDAA33"
FUNDO = "#F9F9FB"
TEXTO_SECUNDARIO = "#4A3F75"
BORDA = "#E0E0E0"
BRANCO = "#FFFFFF"
VERDE = "#2E9E6B"
VERMELHO = "#C0392B"

# Folha de estilo global (QSS) ---------------------------------------------
GLOBAL_QSS = f"""
* {{
    font-family: 'Segoe UI', 'Arial';
    font-size: 10pt;
}}

QMainWindow, QDialog {{
    background-color: {FUNDO};
}}

QWidget#topBar {{
    background-color: {ROXO_PRINCIPAL};
    border-bottom: 4px solid {AMARELO_DOURADO};
}}

QLabel#appTitle {{
    color: {BRANCO};
    font-size: 16pt;
    font-weight: bold;
}}

QLabel#appSubtitle {{
    color: {AMARELO_DOURADO};
    font-size: 9pt;
}}

QLabel#pageTitle {{
    color: {ROXO_PRINCIPAL};
    font-size: 14pt;
    font-weight: bold;
}}

QLabel#cardValue {{
    color: {ROXO_PRINCIPAL};
    font-size: 18pt;
    font-weight: bold;
}}

QLabel#cardLabel {{
    color: {TEXTO_SECUNDARIO};
    font-size: 9pt;
}}

QLabel#slogan {{
    color: {AMARELO_DOURADO};
    font-style: italic;
    font-size: 9pt;
}}

QFrame#card {{
    background-color: {BRANCO};
    border: 1px solid {BORDA};
    border-radius: 8px;
}}

QTabWidget::pane {{
    border: 1px solid {BORDA};
    border-radius: 6px;
    background-color: {FUNDO};
    top: -1px;
}}

QTabBar::tab {{
    background: {BRANCO};
    color: {TEXTO_SECUNDARIO};
    padding: 8px 16px;
    border: 1px solid {BORDA};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background: {ROXO_PRINCIPAL};
    color: {BRANCO};
    font-weight: bold;
}}

QPushButton {{
    background-color: {ROXO_PRINCIPAL};
    color: {BRANCO};
    border: none;
    border-radius: 5px;
    padding: 7px 14px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: #7D63C9;
}}

QPushButton:pressed {{
    background-color: #58438F;
}}

QPushButton:disabled {{
    background-color: {BORDA};
    color: #AAAAAA;
}}

QPushButton#gold {{
    background-color: {AMARELO_DOURADO};
    color: {BRANCO};
}}

QPushButton#gold:hover {{
    background-color: #E7BC4F;
}}

QPushButton#danger {{
    background-color: {VERMELHO};
}}

QPushButton#success {{
    background-color: {VERDE};
}}

QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
    background-color: {BRANCO};
    border: 1px solid {BORDA};
    border-radius: 4px;
    padding: 5px;
    selection-background-color: {ROXO_PRINCIPAL};
}}

QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {{
    border: 1px solid {ROXO_PRINCIPAL};
}}

QTableWidget {{
    background-color: {BRANCO};
    border: 1px solid {BORDA};
    border-radius: 4px;
    gridline-color: {BORDA};
    alternate-background-color: {FUNDO};
}}

QHeaderView::section {{
    background-color: {ROXO_PRINCIPAL};
    color: {BRANCO};
    padding: 6px;
    border: none;
    font-weight: bold;
}}

QTableWidget::item:selected {{
    background-color: {AMARELO_DOURADO};
    color: #333333;
}}

QGroupBox {{
    border: 1px solid {BORDA};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
    color: {ROXO_PRINCIPAL};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}}

QScrollArea {{
    border: none;
    background-color: {FUNDO};
}}

QMessageBox, QFileDialog {{
    background-color: {FUNDO};
}}

QStatusBar {{
    background-color: {ROXO_PRINCIPAL};
    color: {BRANCO};
}}
"""


def montar_pdf_palette():
    """Cores em formato utilizável pelo ReportLab."""
    from reportlab.lib.colors import HexColor
    return {
        "roxo": HexColor("#6B52B3"),
        "dourado": HexColor("#DDAA33"),
        "fundo": HexColor("#F9F9FB"),
        "texto": HexColor("#4A3F75"),
        "borda": HexColor("#E0E0E0"),
    }
