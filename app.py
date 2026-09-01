{\rtf1\ansi\ansicpg1252\cocoartf2907
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import sqlite3\
import pandas as pd\
from datetime import datetime, date\
import io\
import os\
from reportlab.lib.pagesizes import A4\
from reportlab.lib import colors\
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable\
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle\
from reportlab.lib.units import cm\
\
# ==========================================\
# CONFIGURA\'c7\'c3O GERAL DA P\'c1GINA\
# ==========================================\
st.set_page_config(\
    page_title="Finan\'e7as Fam\'edlia Almeida",\
    page_icon="\uc0\u55357 \u56508 ",\
    layout="wide",\
    initial_sidebar_state="expanded"\
)\
\
# ==========================================\
# ESTILIZA\'c7\'c3O CSS MODERNA\
# ==========================================\
st.markdown("""\
<style>\
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');\
    \
    html, body, [class*="css"] \{\
        font-family: 'Plus Jakarta Sans', sans-serif;\
    \}\
    \
    .header-box \{\
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);\
        padding: 24px 30px;\
        border-radius: 16px;\
        color: white;\
        margin-bottom: 25px;\
        box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.25);\
    \}\
    .header-title \{\
        font-size: 28px;\
        font-weight: 800;\
        margin: 0;\
        letter-spacing: -0.5px;\
        color: #FFFFFF;\
    \}\
    .header-subtitle \{\
        font-size: 14px;\
        color: #DBEAFE;\
        margin-top: 5px;\
        margin-bottom: 0;\
    \}\
    \
    .metric-card \{\
        background: #FFFFFF;\
        border: 1px solid #E5E7EB;\
        padding: 20px;\
        border-radius: 14px;\
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);\
        transition: transform 0.2s ease, box-shadow 0.2s ease;\
    \}\
    .metric-card:hover \{\
        transform: translateY(-2px);\
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);\
    \}\
    .metric-title \{\
        font-size: 13px;\
        font-weight: 600;\
        color: #6B7280;\
        text-transform: uppercase;\
        letter-spacing: 0.5px;\
    \}\
    .metric-value \{\
        font-size: 22px;\
        font-weight: 800;\
        margin-top: 6px;\
    \}\
    .metric-green \{ color: #059669; \}\
    .metric-red \{ color: #DC2626; \}\
    .metric-blue \{ color: #2563EB; \}\
    .metric-purple \{ color: #7C3AED; \}\
</style>\
""", unsafe_allow_html=True)\
\
# ==========================================\
# CAMADA DE BANCO DE DADOS (SQLite)\
# ==========================================\
DB_FILE = "financas_familia_almeida.db"\
\
def get_db():\
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)\
    conn.row_factory = sqlite3.Row\
    return conn\
\
def init_database():\
    conn = get_db()\
    cursor = conn.cursor()\
    \
    cursor.execute("""\
    CREATE TABLE IF NOT EXISTS transacoes (\
        id INTEGER PRIMARY KEY AUTOINCREMENT,\
        data TEXT NOT NULL,\
        dia INTEGER NOT NULL,\
        mes INTEGER NOT NULL,\
        ano INTEGER NOT NULL,\
        descricao TEXT NOT NULL,\
        categoria TEXT NOT NULL,\
        tipo TEXT NOT NULL,\
        debito REAL DEFAULT 0.0,\
        credito REAL DEFAULT 0.0,\
        observacoes TEXT\
    )\
    """)\
    \
    cursor.execute("""\
    CREATE TABLE IF NOT EXISTS categorias (\
        id INTEGER PRIMARY KEY AUTOINCREMENT,\
        nome TEXT UNIQUE NOT NULL,\
        tipo TEXT NOT NULL\
    )\
    """)\
    \
    cursor.execute("""\
    CREATE TABLE IF NOT EXISTS metas_economias (\
        id INTEGER PRIMARY KEY AUTOINCREMENT,\
        nome TEXT NOT NULL,\
        valor_alvo REAL NOT NULL,\
        valor_atual REAL DEFAULT 0.0,\
        data_limite TEXT,\
        categoria TEXT\
    )\
    """)\
    \
    cursor.execute("SELECT COUNT(*) FROM categorias")\
    if cursor.fetchone()[0] == 0:\
        categorias_iniciais = [\
            ("Sal\'e1rio", "Receita"),\
            ("Rendimentos de Investimentos", "Receita"),\
            ("Servi\'e7os Extras / Freelance", "Receita"),\
            ("Outras Receitas", "Receita"),\
            ("Moradia (Aluguel, Condom\'ednio, IPTU)", "Despesa"),\
            ("Alimenta\'e7\'e3o & Supermercado", "Despesa"),\
            ("Transporte & Combust\'edvel", "Despesa"),\
            ("Sa\'fade, Conv\'eanio & Farm\'e1cia", "Despesa"),\
            ("Educa\'e7\'e3o & Cursos", "Despesa"),\
            ("Lazer, Restaurantes & Viagens", "Despesa"),\
            ("Assinaturas & Conectividade", "Despesa"),\
            ("Compras Pessoais & Vestu\'e1rio", "Despesa"),\
            ("Manuten\'e7\'e3o & Imprevistos", "Despesa"),\
            ("Impostos & Tarifas Banc\'e1rias", "Despesa"),\
            ("Reserva de Emerg\'eancia", "Economia"),\
            ("Poupan\'e7a para Objetivos", "Economia"),\
            ("Renda Fixa (CDB, Tesouro)", "Investimento"),\
            ("Renda Vari\'e1vel (A\'e7\'f5es e FIIs)", "Investimento"),\
            ("Previd\'eancia Privada", "Investimento")\
        ]\
        cursor.executemany("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", categorias_iniciais)\
        \
    conn.commit()\
    conn.close()\
\
init_database()\
\
# ==========================================\
# FUN\'c7\'d5ES DE CRUD\
# ==========================================\
def get_categorias(tipo=None):\
    conn = get_db()\
    cursor = conn.cursor()\
    if tipo:\
        cursor.execute("SELECT nome FROM categorias WHERE tipo = ? ORDER BY nome ASC", (tipo,))\
    else:\
        cursor.execute("SELECT nome, tipo FROM categorias ORDER BY tipo, nome ASC")\
    rows = cursor.fetchall()\
    conn.close()\
    if tipo:\
        return [r["nome"] for r in rows]\
    return [dict(r) for r in rows]\
\
def add_categoria(nome, tipo):\
    conn = get_db()\
    cursor = conn.cursor()\
    try:\
        cursor.execute("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", (nome.strip(), tipo))\
        conn.commit()\
        success = True\
    except sqlite3.IntegrityError:\
        success = False\
    conn.close()\
    return success\
\
def insert_transacao(data_str, descricao, categoria, tipo, valor, observacoes=""):\
    d_obj = datetime.strptime(data_str, "%Y-%m-%d").date()\
    debito = float(valor) if tipo in ["D\'e9bito", "Aplica\'e7\'e3o", "Economia"] else 0.0\
    credito = float(valor) if tipo == "Cr\'e9dito" else 0.0\
    \
    conn = get_db()\
    cursor = conn.cursor()\
    cursor.execute("""\
    INSERT INTO transacoes (data, dia, mes, ano, descricao, categoria, tipo, debito, credito, observacoes)\
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\
    """, (data_str, d_obj.day, d_obj.month, d_obj.year, descricao.strip(), categoria, tipo, debito, credito, observacoes.strip()))\
    conn.commit()\
    conn.close()\
\
def update_transacao(transacao_id, data_str, descricao, categoria, tipo, valor, observacoes=""):\
    d_obj = datetime.strptime(data_str, "%Y-%m-%d").date()\
    debito = float(valor) if tipo in ["D\'e9bito", "Aplica\'e7\'e3o", "Economia"] else 0.0\
    credito = float(valor) if tipo == "Cr\'e9dito" else 0.0\
    \
    conn = get_db()\
    cursor = conn.cursor()\
    cursor.execute("""\
    UPDATE transacoes \
    SET data = ?, dia = ?, mes = ?, ano = ?, descricao = ?, categoria = ?, tipo = ?, debito = ?, credito = ?, observacoes = ?\
    WHERE id = ?\
    """, (data_str, d_obj.day, d_obj.month, d_obj.year, descricao.strip(), categoria, tipo, debito, credito, observacoes.strip(), transacao_id))\
    conn.commit()\
    conn.close()\
\
def delete_transacao(transacao_id):\
    conn = get_db()\
    cursor = conn.cursor()\
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))\
    conn.commit()\
    conn.close()\
\
def load_transacoes(mes=None, ano=None):\
    conn = get_db()\
    query = "SELECT * FROM transacoes WHERE 1=1"\
    params = []\
    if ano:\
        query += " AND ano = ?"\
        params.append(ano)\
    if mes:\
        query += " AND mes = ?"\
        params.append(mes)\
    query += " ORDER BY data ASC, id ASC"\
    df = pd.read_sql_query(query, conn, params=params)\
    conn.close()\
    \
    if not df.empty:\
        df['saldo_linha'] = df['credito'] - df['debito']\
        df['saldo_acumulado'] = df['saldo_linha'].cumsum()\
    else:\
        df = pd.DataFrame(columns=[\
            'id', 'data', 'dia', 'mes', 'ano', 'descricao', \
            'categoria', 'tipo', 'debito', 'credito', 'observacoes', \
            'saldo_linha', 'saldo_acumulado'\
        ])\
    return df\
\
def get_anos_disponiveis():\
    conn = get_db()\
    cursor = conn.cursor()\
    cursor.execute("SELECT DISTINCT ano FROM transacoes ORDER BY ano DESC")\
    anos = [r[0] for r in cursor.fetchall()]\
    conn.close()\
    current_year = datetime.now().year\
    if current_year not in anos:\
        anos.insert(0, current_year)\
    return anos\
\
def format_currency(val):\
    if pd.isna(val) or val is None:\
        val = 0.0\
    return f"R$ \{val:,.2f\}".replace(",", "X").replace(".", ",").replace("X", ".")\
\
def get_metas():\
    conn = get_db()\
    cursor = conn.cursor()\
    cursor.execute("SELECT * FROM metas_economias ORDER BY id DESC")\
    rows = cursor.fetchall()\
    conn.close()\
    return [dict(r) for r in rows]\
\
def insert_meta(nome, valor_alvo, valor_atual, data_limite, categoria):\
    conn = get_db()\
    cursor = conn.cursor()\
    cursor.execute("""\
    INSERT INTO metas_economias (nome, valor_alvo, valor_atual, data_limite, categoria)\
    VALUES (?, ?, ?, ?, ?)\
    """, (nome, float(valor_alvo), float(valor_atual), data_limite, categoria))\
    conn.commit()\
    conn.close()\
\
def update_meta_valor(meta_id, novo_valor):\
    conn = get_db()\
    cursor = conn.cursor()\
    cursor.execute("UPDATE metas_economias SET valor_atual = ? WHERE id = ?", (float(novo_valor), meta_id))\
    conn.commit()\
    conn.close()\
\
def delete_meta(meta_id):\
    conn = get_db()\
    cursor = conn.cursor()\
    cursor.execute("DELETE FROM metas_economias WHERE id = ?", (meta_id,))\
    conn.commit()\
    conn.close()\
\
# ==========================================\
# GERADOR DE RELAT\'d3RIO EM PDF\
# ==========================================\
def generate_pdf_report(mes, ano):\
    df = load_transacoes(mes, ano)\
    buffer = io.BytesIO()\
    doc = SimpleDocTemplate(\
        buffer,\
        pagesize=A4,\
        rightMargin=1.5*cm,\
        leftMargin=1.5*cm,\
        topMargin=1.5*cm,\
        bottomMargin=1.5*cm\
    )\
    \
    styles = getSampleStyleSheet()\
    title_style = ParagraphStyle(\
        'DocTitle',\
        parent=styles['Heading1'],\
        fontSize=18,\
        leading=22,\
        textColor=colors.HexColor('#1E3A8A'),\
        alignment=1,\
        spaceAfter=4\
    )\
    subtitle_style = ParagraphStyle(\
        'DocSubtitle',\
        parent=styles['Normal'],\
        fontSize=11,\
        leading=14,\
        textColor=colors.HexColor('#4B5563'),\
        alignment=1,\
        spaceAfter=15\
    )\
    section_style = ParagraphStyle(\
        'SectionHeading',\
        parent=styles['Heading2'],\
        fontSize=12,\
        leading=16,\
        textColor=colors.HexColor('#1E3A8A'),\
        spaceBefore=12,\
        spaceAfter=6\
    )\
    cell_style = ParagraphStyle(\
        'CellText',\
        parent=styles['Normal'],\
        fontSize=8,\
        leading=10,\
        textColor=colors.HexColor('#1F2937')\
    )\
    header_cell_style = ParagraphStyle(\
        'HeaderCellText',\
        parent=styles['Normal'],\
        fontSize=8,\
        leading=10,\
        fontName="Helvetica-Bold",\
        textColor=colors.white\
    )\
\
    elements = []\
    \
    elements.append(Paragraph("<b>Finan\'e7as Fam\'edlia Almeida</b>", title_style))\
    nome_meses = ["Janeiro", "Fevereiro", "Mar\'e7o", "Abril", "Maio", "Junho", \
                  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]\
    mes_str = nome_meses[mes-1] if (mes and 1 <= mes <= 12) else "Consolidado Anual"\
    elements.append(Paragraph(f"Relat\'f3rio Financeiro Oficial \'97 \{mes_str\} / \{ano\}", subtitle_style))\
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceAfter=14))\
    \
    total_credito = df['credito'].sum() if not df.empty else 0.0\
    total_debito = df[df['tipo'] == 'D\'e9bito']['debito'].sum() if not df.empty else 0.0\
    total_aplicado = df[df['tipo'] == 'Aplica\'e7\'e3o']['debito'].sum() if not df.empty else 0.0\
    total_poupado = df[df['tipo'] == 'Economia']['debito'].sum() if not df.empty else 0.0\
    saldo_liquido = total_credito - total_debito - total_aplicado - total_poupado\
    \
    summary_data = [\
        [\
            Paragraph("<b>Total Entradas</b>", cell_style),\
            Paragraph("<b>Despesas</b>", cell_style),\
            Paragraph("<b>Aplica\'e7\'f5es</b>", cell_style),\
            Paragraph("<b>Economias</b>", cell_style),\
            Paragraph("<b>Saldo L\'edquido</b>", cell_style)\
        ],\
        [\
            format_currency(total_credito),\
            format_currency(total_debito),\
            format_currency(total_aplicado),\
            format_currency(total_poupado),\
            format_currency(saldo_liquido)\
        ]\
    ]\
    \
    summary_table = Table(summary_data, colWidths=[3.4*cm, 3.4*cm, 3.4*cm, 3.4*cm, 3.4*cm])\
    summary_table.setStyle(TableStyle([\
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3F4F6')),\
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F9FAFB')),\
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),\
        ('TEXTCOLOR', (0,1), (0,1), colors.HexColor('#059669')),\
        ('TEXTCOLOR', (1,1), (1,1), colors.HexColor('#DC2626')),\
        ('TEXTCOLOR', (2,1), (2,1), colors.HexColor('#2563EB')),\
        ('TEXTCOLOR', (3,1), (3,1), colors.HexColor('#7C3AED')),\
        ('TEXTCOLOR', (4,1), (4,1), colors.HexColor('#0D9488') if saldo_liquido >= 0 else colors.HexColor('#DC2626')),\
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),\
        ('FONTSIZE', (0,1), (-1,1), 9),\
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),\
        ('TOPPADDING', (0,0), (-1,-1), 5),\
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),\
    ]))\
    elements.append(summary_table)\
    elements.append(Spacer(1, 14))\
    \
    elements.append(Paragraph("<b>Extrato de Lan\'e7amentos</b>", section_style))\
    table_data = [[\
        Paragraph("<b>Data</b>", header_cell_style),\
        Paragraph("<b>Lan\'e7amento</b>", header_cell_style),\
        Paragraph("<b>Categoria</b>", header_cell_style),\
        Paragraph("<b>Tipo</b>", header_cell_style),\
        Paragraph("<b>D\'e9bito</b>", header_cell_style),\
        Paragraph("<b>Cr\'e9dito</b>", header_cell_style),\
        Paragraph("<b>Saldo</b>", header_cell_style),\
    ]]\
    \
    for _, row in df.iterrows():\
        deb_str = format_currency(row['debito']) if row['debito'] > 0 else "-"\
        cred_str = format_currency(row['credito']) if row['credito'] > 0 else "-"\
        saldo_str = format_currency(row['saldo_acumulado'])\
        \
        table_data.append([\
            f"\{int(row['dia']):02d\}/\{int(row['mes']):02d\}/\{int(row['ano'])\}",\
            Paragraph(str(row['descricao'])[:32], cell_style),\
            Paragraph(str(row['categoria'])[:25], cell_style),\
            str(row['tipo']),\
            deb_str,\
            cred_str,\
            saldo_str\
        ])\
        \
    item_table = Table(table_data, colWidths=[1.8*cm, 4.3*cm, 3.5*cm, 1.8*cm, 2.2*cm, 2.2*cm, 2.2*cm])\
    item_table.setStyle(TableStyle([\
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),\
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),\
        ('ALIGN', (0,1), (0,-1), 'CENTER'),\
        ('ALIGN', (3,1), (3,-1), 'CENTER'),\
        ('ALIGN', (4,0), (-1,-1), 'RIGHT'),\
        ('FONTSIZE', (0,1), (-1,-1), 8),\
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),\
        ('TOPPADDING', (0,0), (-1,-1), 3.5),\
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),\
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9FAFB')])\
    ]))\
    elements.append(item_table)\
    \
    elements.append(Spacer(1, 15))\
    data_geracao = datetime.now().strftime("%d/%m/%Y \'e0s %H:%M")\
    elements.append(Paragraph(f"<font size=7 color='#6B7280'>Documento emitido pelo aplicativo Finan\'e7as Fam\'edlia Almeida em \{data_geracao\}.</font>", cell_style))\
    \
    doc.build(elements)\
    buffer.seek(0)\
    return buffer.getvalue()\
\
# ==========================================\
# INTERFACE PRINCIPAL\
# ==========================================\
st.markdown("""\
<div class="header-box">\
    <div style="display: flex; justify-content: space-between; align-items: center;">\
        <div>\
            <h1 class="header-title">\uc0\u55356 \u57307 \u65039  Finan\'e7as Fam\'edlia Almeida</h1>\
            <p class="header-subtitle">Sistema Integrado de Gest\'e3o Financeira, Aplica\'e7\'f5es e Economias</p>\
        </div>\
        <div style="text-align: right; background: rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 10px;">\
            <span style="font-size: 13px; font-weight: 600; color: #FFFFFF;">\uc0\u55357 \u56517  Gest\'e3o Mensal & Anual</span>\
        </div>\
    </div>\
</div>\
""", unsafe_allow_html=True)\
\
st.sidebar.title("\uc0\u55358 \u56813  Navega\'e7\'e3o & Filtros")\
\
menu = st.sidebar.radio(\
    "M\'f3dulo:",\
    [\
        "\uc0\u55357 \u56522  Dashboard Geral", \
        "\uc0\u55357 \u56541  Lan\'e7amentos & Extrato", \
        "\uc0\u55357 \u56520  An\'e1lise de Aplica\'e7\'f5es", \
        "\uc0\u55356 \u57263  Economias & Metas", \
        "\uc0\u55357 \u56516  Relat\'f3rios em PDF",\
        "\uc0\u9881 \u65039  Configura\'e7\'f5es & Categorias"\
    ]\
)\
\
st.sidebar.markdown("---")\
st.sidebar.subheader("\uc0\u55357 \u56517  Per\'edodo de An\'e1lise")\
\
anos_disponiveis = get_anos_disponiveis()\
ano_selecionado = st.sidebar.selectbox("Ano:", anos_disponiveis, index=0)\
\
nome_meses = [\
    "Todos os Meses (Anual)", "01 - Janeiro", "02 - Fevereiro", "03 - Mar\'e7o", \
    "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", \
    "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"\
]\
mes_atual_idx = datetime.now().month\
mes_selecionado_str = st.sidebar.selectbox("M\'eas:", nome_meses, index=mes_atual_idx)\
\
if mes_selecionado_str == "Todos os Meses (Anual)":\
    mes_selecionado = None\
    mes_label = f"Ano de \{ano_selecionado\}"\
else:\
    mes_selecionado = int(mes_selecionado_str.split(" - ")[0])\
    mes_label = f"\{nome_meses[mes_selecionado]\} de \{ano_selecionado\}"\
\
df_periodo = load_transacoes(mes=mes_selecionado, ano=ano_selecionado)\
df_ano = load_transacoes(mes=None, ano=ano_selecionado)\
\
total_credito = df_periodo['credito'].sum() if not df_periodo.empty else 0.0\
total_debito = df_periodo[df_periodo['tipo'] == 'D\'e9bito']['debito'].sum() if not df_periodo.empty else 0.0\
total_aplicacoes = df_periodo[df_periodo['tipo'] == 'Aplica\'e7\'e3o']['debito'].sum() if not df_periodo.empty else 0.0\
total_economias = df_periodo[df_periodo['tipo'] == 'Economia']['debito'].sum() if not df_periodo.empty else 0.0\
total_saidas_geral = total_debito + total_aplicacoes + total_economias\
saldo_liquido = total_credito - total_saidas_geral\
taxa_poupanca = ((total_aplicacoes + total_economias) / total_credito * 100) if total_credito > 0 else 0.0\
\
# 1. Dashboard Geral\
if menu == "\uc0\u55357 \u56522  Dashboard Geral":\
    st.subheader(f"Vis\'e3o Executiva \'97 \{mes_label\}")\
    \
    c1, c2, c3, c4, c5 = st.columns(5)\
    with c1:\
        st.markdown(f"""\
        <div class="metric-card">\
            <div class="metric-title">Entradas (Cr\'e9dito)</div>\
            <div class="metric-value metric-green">\{format_currency(total_credito)\}</div>\
        </div>\
        """, unsafe_allow_html=True)\
    with c2:\
        st.markdown(f"""\
        <div class="metric-card">\
            <div class="metric-title">Despesas (D\'e9bito)</div>\
            <div class="metric-value metric-red">\{format_currency(total_debito)\}</div>\
        </div>\
        """, unsafe_allow_html=True)\
    with c3:\
        st.markdown(f"""\
        <div class="metric-card">\
            <div class="metric-title">Aplica\'e7\'f5es (Invest.)</div>\
            <div class="metric-value metric-blue">\{format_currency(total_aplicacoes)\}</div>\
        </div>\
        """, unsafe_allow_html=True)\
    with c4:\
        st.markdown(f"""\
        <div class="metric-card">\
            <div class="metric-title">Economias (Reserva)</div>\
            <div class="metric-value metric-purple">\{format_currency(total_economias)\}</div>\
        </div>\
        """, unsafe_allow_html=True)\
    with c5:\
        cor_saldo = "metric-green" if saldo_liquido >= 0 else "metric-red"\
        st.markdown(f"""\
        <div class="metric-card">\
            <div class="metric-title">Saldo L\'edquido</div>\
            <div class="metric-value \{cor_saldo\}">\{format_currency(saldo_liquido)\}</div>\
        </div>\
        """, unsafe_allow_html=True)\
        \
    st.markdown("<br>", unsafe_allow_html=True)\
    \
    col_g1, col_g2 = st.columns(2)\
    with col_g1:\
        st.markdown("#### \uc0\u55357 \u56520  Evolu\'e7\'e3o Mensal do Ano")\
        if not df_ano.empty:\
            resumo_mensal = df_ano.groupby('mes').agg(\{\
                'credito': 'sum',\
                'debito': 'sum'\
            \}).reset_index()\
            resumo_mensal['Nome_Mes'] = resumo_mensal['mes'].apply(lambda m: ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"][m-1])\
            resumo_mensal['Saldo'] = resumo_mensal['credito'] - resumo_mensal['debito']\
            \
            chart_df = resumo_mensal.set_index('Nome_Mes')[['credito', 'debito', 'Saldo']]\
            chart_df.columns = ['Entradas', 'Sa\'eddas', 'Saldo L\'edquido']\
            st.bar_chart(chart_df, height=320)\
        else:\
            st.info("Nenhum lan\'e7amento registrado para este ano.")\
\
    with col_g2:\
        st.markdown("#### \uc0\u55356 \u57173  Despesas por Categoria")\
        despesas_df = df_periodo[df_periodo['tipo'] == 'D\'e9bito']\
        if not despesas_df.empty:\
            cat_df = despesas_df.groupby('categoria')['debito'].sum().reset_index()\
            cat_df = cat_df.sort_values(by='debito', ascending=False)\
            cat_df['Valor'] = cat_df['debito'].apply(format_currency)\
            cat_df['% do Total'] = (cat_df['debito'] / cat_df['debito'].sum() * 100).round(1).astype(str) + "%"\
            st.dataframe(cat_df[['categoria', 'Valor', '% do Total']], use_container_width=True, hide_index=True)\
        else:\
            st.info("Nenhuma despesa lan\'e7ada no per\'edodo.")\
\
    st.markdown("---")\
    col_p1, col_p2 = st.columns(2)\
    with col_p1:\
        st.markdown(f"**Taxa de Economia & Aporte:** `\{taxa_poupanca:.1f\}%` guardada/investida.")\
        st.progress(min(max(taxa_poupanca / 100, 0.0), 1.0))\
    with col_p2:\
        st.markdown(f"**Resultado L\'edquido do Per\'edodo:** `\{format_currency(saldo_liquido)\}`")\
\
# 2. Lan\'e7amentos & Extrato\
elif menu == "\uc0\u55357 \u56541  Lan\'e7amentos & Extrato":\
    st.subheader("Gerenciador de Lan\'e7amentos")\
    \
    tab_novo, tab_editar = st.tabs(["\uc0\u10133  Novo Lan\'e7amento", "\u9999 \u65039  Editar Lan\'e7amento"])\
    \
    with tab_novo:\
        with st.form("form_novo_lancamento", clear_on_submit=True):\
            col_f1, col_f2, col_f3 = st.columns(3)\
            with col_f1:\
                data_lancamento = st.date_input("Data do Lan\'e7amento:", value=date.today(), key="novo_data")\
                tipo_lancamento = st.selectbox(\
                    "Tipo de Opera\'e7\'e3o:", \
                    ["D\'e9bito (Despesa)", "Cr\'e9dito (Receita)", "Aplica\'e7\'e3o (Investimento)", "Economia (Reserva/Metas)"],\
                    key="novo_tipo"\
                )\
            \
            tipo_map = \{\
                "D\'e9bito (Despesa)": ("D\'e9bito", "Despesa"),\
                "Cr\'e9dito (Receita)": ("Cr\'e9dito", "Receita"),\
                "Aplica\'e7\'e3o (Investimento)": ("Aplica\'e7\'e3o", "Investimento"),\
                "Economia (Reserva/Metas)": ("Economia", "Economia")\
            \}\
            tipo_db, cat_tipo = tipo_map[tipo_lancamento]\
            categorias_disponiveis = get_categorias(cat_tipo)\
            if not categorias_disponiveis:\
                categorias_disponiveis = get_categorias()\
                \
            with col_f2:\
                descricao = st.text_input("Descri\'e7\'e3o / Lan\'e7amento:", placeholder="Ex: Sal\'e1rio, Supermercado, Aporte CDB...", key="novo_desc")\
                categoria = st.selectbox("Categoria Agregada:", categorias_disponiveis, key="novo_cat")\
                \
            with col_f3:\
                valor = st.number_input("Valor (R$):", min_value=0.01, step=50.0, format="%.2f", key="novo_valor")\
                observacoes = st.text_input("Observa\'e7\'f5es (Opcional):", placeholder="Detalhes...", key="novo_obs")\
                \
            submitted = st.form_submit_button("\uc0\u55357 \u56510  Salvar Lan\'e7amento", use_container_width=True)\
            if submitted:\
                if not descricao:\
                    st.error("Preencha a descri\'e7\'e3o do lan\'e7amento.")\
                else:\
                    insert_transacao(\
                        data_str=data_lancamento.strftime("%Y-%m-%d"),\
                        descricao=descricao,\
                        categoria=categoria,\
                        tipo=tipo_db,\
                        valor=valor,\
                        observacoes=observacoes\
                    )\
                    st.success(f"Lan\'e7amento '\{descricao\}' de \{format_currency(valor)\} registrado com sucesso!")\
                    st.rerun()\
\
    with tab_editar:\
        df_todas = load_transacoes(mes=None, ano=ano_selecionado)\
        if not df_todas.empty:\
            opcoes_transacoes = df_todas['id'].tolist()\
            \
            def format_opcao(tid):\
                row = df_todas[df_todas['id'] == tid].iloc[0]\
                val = row['debito'] if row['debito'] > 0 else row['credito']\
                return f"ID \{tid\} | \{int(row['dia']):02d\}/\{int(row['mes']):02d\}/\{int(row['ano'])\} - \{row['descricao']\} (\{format_currency(val)\}) [\{row['tipo']\}]"\
            \
            transacao_selecionada_id = st.selectbox(\
                "Selecione o lan\'e7amento que deseja editar:",\
                opcoes_transacoes,\
                format_func=format_opcao,\
                key="select_edit_transacao"\
            )\
            \
            item_atual = df_todas[df_todas['id'] == transacao_selecionada_id].iloc[0]\
            data_atual_obj = datetime.strptime(item_atual['data'], "%Y-%m-%d").date()\
            valor_atual_num = float(item_atual['debito'] if item_atual['debito'] > 0 else item_atual['credito'])\
            \
            tipo_invert_map = \{\
                "D\'e9bito": "D\'e9bito (Despesa)",\
                "Cr\'e9dito": "Cr\'e9dito (Receita)",\
                "Aplica\'e7\'e3o": "Aplica\'e7\'e3o (Investimento)",\
                "Economia": "Economia (Reserva/Metas)"\
            \}\
            tipo_label_atual = tipo_invert_map.get(item_atual['tipo'], "D\'e9bito (Despesa)")\
            lista_tipos = ["D\'e9bito (Despesa)", "Cr\'e9dito (Receita)", "Aplica\'e7\'e3o (Investimento)", "Economia (Reserva/Metas)"]\
            tipo_index_atual = lista_tipos.index(tipo_label_atual) if tipo_label_atual in lista_tipos else 0\
            \
            with st.form(f"form_editar_\{transacao_selecionada_id\}"):\
                c_e1, c_e2, c_e3 = st.columns(3)\
                with c_e1:\
                    edit_data = st.date_input("Data:", value=data_atual_obj, key=f"edit_data_\{transacao_selecionada_id\}")\
                    edit_tipo_label = st.selectbox(\
                        "Tipo de Opera\'e7\'e3o:", \
                        lista_tipos, \
                        index=tipo_index_atual, \
                        key=f"edit_tipo_\{transacao_selecionada_id\}"\
                    )\
                \
                tipo_map = \{\
                    "D\'e9bito (Despesa)": ("D\'e9bito", "Despesa"),\
                    "Cr\'e9dito (Receita)": ("Cr\'e9dito", "Receita"),\
                    "Aplica\'e7\'e3o (Investimento)": ("Aplica\'e7\'e3o", "Investimento"),\
                    "Economia (Reserva/Metas)": ("Economia", "Economia")\
                \}\
                edit_tipo_db, edit_cat_tipo = tipo_map[edit_tipo_label]\
                cats_para_editar = get_categorias(edit_cat_tipo)\
                if not cats_para_editar:\
                    cats_para_editar = get_categorias()\
                cat_index_atual = cats_para_editar.index(item_atual['categoria']) if item_atual['categoria'] in cats_para_editar else 0\
                \
                with c_e2:\
                    edit_descricao = st.text_input("Descri\'e7\'e3o / Lan\'e7amento:", value=str(item_atual['descricao']), key=f"edit_desc_\{transacao_selecionada_id\}")\
                    edit_categoria = st.selectbox("Categoria:", cats_para_editar, index=cat_index_atual, key=f"edit_cat_\{transacao_selecionada_id\}")\
                    \
                with c_e3:\
                    edit_valor = st.number_input("Valor (R$):", min_value=0.01, step=50.0, format="%.2f", value=valor_atual_num, key=f"edit_val_\{transacao_selecionada_id\}")\
                    edit_obs = st.text_input("Observa\'e7\'f5es:", value=str(item_atual['observacoes'] or ''), key=f"edit_obs_\{transacao_selecionada_id\}")\
                    \
                btn_salvar_edicao = st.form_submit_button("\uc0\u55357 \u56510  Salvar Altera\'e7\'f5es", type="primary", use_container_width=True)\
                if btn_salvar_edicao:\
                    if not edit_descricao:\
                        st.error("A descri\'e7\'e3o n\'e3o pode ficar vazia.")\
                    else:\
                        update_transacao(\
                            transacao_id=transacao_selecionada_id,\
                            data_str=edit_data.strftime("%Y-%m-%d"),\
                            descricao=edit_descricao,\
                            categoria=edit_categoria,\
                            tipo=edit_tipo_db,\
                            valor=edit_valor,\
                            observacoes=edit_obs\
                        )\
                        st.success(f"Lan\'e7amento '\{edit_descricao\}' atualizado com sucesso!")\
                        st.rerun()\
        else:\
            st.info("Nenhum lan\'e7amento cadastrado no ano selecionado para editar.")\
\
    st.markdown("---")\
    st.subheader(f"Extrato Cronol\'f3gico \'97 \{mes_label\}")\
    \
    if not df_periodo.empty:\
        df_exibir = df_periodo.copy()\
        df_exibir['Data'] = df_exibir['dia'].astype(int).astype(str).str.zfill(2) + '/' + df_exibir['mes'].astype(int).astype(str).str.zfill(2) + '/' + df_exibir['ano'].astype(int).astype(str)\
        df_exibir['D\'e9bito'] = df_exibir['debito'].apply(lambda x: format_currency(x) if x > 0 else "-")\
        df_exibir['Cr\'e9dito'] = df_exibir['credito'].apply(lambda x: format_currency(x) if x > 0 else "-")\
        df_exibir['Saldo'] = df_exibir['saldo_acumulado'].apply(format_currency)\
        \
        busca = st.text_input("\uc0\u55357 \u56589  Filtrar lan\'e7amentos:", "")\
        if busca:\
            df_exibir = df_exibir[\
                df_exibir['descricao'].str.contains(busca, case=False, na=False) |\
                df_exibir['categoria'].str.contains(busca, case=False, na=False) |\
                df_exibir['Data'].str.contains(busca, case=False, na=False)\
            ]\
        \
        st.dataframe(\
            df_exibir[['id', 'Data', 'descricao', 'categoria', 'tipo', 'D\'e9bito', 'Cr\'e9dito', 'Saldo', 'observacoes']],\
            column_config=\{\
                "id": st.column_config.NumberColumn("ID", width="small"),\
                "Data": st.column_config.TextColumn("Data", width="small"),\
                "descricao": st.column_config.TextColumn("Lan\'e7amento", width="medium"),\
                "categoria": st.column_config.TextColumn("Categoria", width="medium"),\
                "tipo": st.column_config.TextColumn("Tipo", width="small"),\
                "D\'e9bito": st.column_config.TextColumn("D\'e9bito (R$)", width="small"),\
                "Cr\'e9dito": st.column_config.TextColumn("Cr\'e9dito (R$)", width="small"),\
                "Saldo": st.column_config.TextColumn("Saldo Acumulado", width="small"),\
                "observacoes": st.column_config.TextColumn("Observa\'e7\'f5es", width="medium"),\
            \},\
            use_container_width=True,\
            hide_index=True\
        )\
        \
        with st.expander("\uc0\u55357 \u56785 \u65039  Excluir Lan\'e7amento"):\
            col_del1, col_del2 = st.columns(2)\
            with col_del1:\
                transacao_para_excluir = st.selectbox(\
                    "Selecione o lan\'e7amento para excluir:",\
                    df_periodo['id'].tolist(),\
                    format_func=lambda tid: f"ID \{tid\} - \{df_periodo[df_periodo['id']==tid]['descricao'].values[0]\}"\
                )\
            with col_del2:\
                st.markdown("<br>", unsafe_allow_html=True)\
                if st.button("Excluir", type="primary", use_container_width=True):\
                    delete_transacao(transacao_para_excluir)\
                    st.success("Lan\'e7amento exclu\'eddo!")\
                    st.rerun()\
    else:\
        st.info(f"Nenhum lan\'e7amento em \{mes_label\}.")\
\
# 3. An\'e1lise de Aplica\'e7\'f5es\
elif menu == "\uc0\u55357 \u56520  An\'e1lise de Aplica\'e7\'f5es":\
    st.subheader(f"Carteira de Aplica\'e7\'f5es & Investimentos \'97 \{mes_label\}")\
    \
    df_aplicacoes = df_periodo[df_periodo['tipo'] == 'Aplica\'e7\'e3o']\
    df_aplicacoes_ano = df_ano[df_ano['tipo'] == 'Aplica\'e7\'e3o']\
    \
    col_a1, col_a2, col_a3 = st.columns(3)\
    total_aplicado_ano = df_aplicacoes_ano['debito'].sum() if not df_aplicacoes_ano.empty else 0.0\
    with col_a1:\
        st.markdown(f"""\
        <div class="metric-card">\
            <div class="metric-title">Aportes no M\'eas</div>\
            <div class="metric-value metric-blue">\{format_currency(total_aplicacoes)\}</div>\
        </div>\
        """, unsafe_allow_html=True)\
    with col_a2:\
        st.markdown(f"""\
        <div class="metric-card">\
            <div class="metric-title">Total Aportado em \{ano_selecionado\}</div>\
            <div class="metric-value metric-blue">\{format_currency(total_aplicado_ano)\}</div>\
        </div>\
        """, unsafe_allow_html=True)\
    with col_a3:\
        rendimentos_ano = df_ano[df_ano['categoria'].str.contains("Rendimento", case=False, na=False)]['credito'].sum()\
        st.markdown(f"""\
        <div class="metric-card">\
            <div class="metric-title">Rendimentos (\{ano_selecionado\})</div>\
            <div class="metric-value metric-green">\{format_currency(rendimentos_ano)\}</div>\
        </div>\
        """, unsafe_allow_html=True)\
\
    st.markdown("<br>", unsafe_allow_html=True)\
    col_inv1, col_inv2 = st.columns(2)\
    with col_inv1:\
        st.markdown("#### \uc0\u55357 \u56522  Aportes por Classe de Ativo")\
        if not df_aplicacoes_ano.empty:\
            cat_inv = df_aplicacoes_ano.groupby('categoria')['debito'].sum().reset_index()\
            cat_inv.columns = ['Classe de Ativo', 'Total Aportado (R$)']\
            st.bar_chart(cat_inv.set_index('Classe de Ativo'), height=300)\
        else:\
            st.info("Nenhuma aplica\'e7\'e3o financeira registrada no per\'edodo.")\
            \
    with col_inv2:\
        st.markdown("#### \uc0\u55357 \u56523  Hist\'f3rico de Aportes")\
        if not df_aplicacoes.empty:\
            df_ap_show = df_aplicacoes.copy()\
            df_ap_show['Data'] = df_ap_show['dia'].astype(int).astype(str).str.zfill(2) + '/' + df_ap_show['mes'].astype(int).astype(str).str.zfill(2) + '/' + df_ap_show['ano'].astype(int).astype(str)\
            df_ap_show['Valor'] = df_ap_show['debito'].apply(format_currency)\
            st.dataframe(df_ap_show[['Data', 'descricao', 'categoria', 'Valor']], use_container_width=True, hide_index=True)\
        else:\
            st.info("Nenhum aporte no per\'edodo selecionado.")\
\
# 4. Economias & Metas\
elif menu == "\uc0\u55356 \u57263  Economias & Metas":\
    st.subheader("Reserva de Emerg\'eancia & Metas da Fam\'edlia")\
    \
    with st.expander("\uc0\u10133  Cadastrar Nova Meta"):\
        with st.form("form_meta"):\
            c_m1, c_m2, c_m3 = st.columns(3)\
            with c_m1:\
                nome_meta = st.text_input("Nome do Objetivo:", placeholder="Ex: Reserva 6 Meses, Viagem")\
            with c_m2:\
                valor_alvo = st.number_input("Valor Alvo (R$):", min_value=100.0, step=500.0)\
            with c_m3:\
                valor_inicial = st.number_input("Valor J\'e1 Guardado (R$):", min_value=0.0, step=100.0)\
            \
            c_m4, c_m5 = st.columns(2)\
            with c_m4:\
                data_limite = st.date_input("Data Alvo / Limite:")\
            with c_m5:\
                cat_meta = st.selectbox("Categoria:", ["Reserva de Emerg\'eancia", "Poupan\'e7a / Metas", "Outros Objetivos"])\
                \
            if st.form_submit_button("Salvar Meta", use_container_width=True):\
                if nome_meta:\
                    insert_meta(nome_meta, valor_alvo, valor_inicial, data_limite.strftime("%Y-%m-%d"), cat_meta)\
                    st.success(f"Meta '\{nome_meta\}' cadastrada!")\
                    st.rerun()\
                    \
    st.markdown("---")\
    metas = get_metas()\
    if metas:\
        for m in metas:\
            perc = (m['valor_atual'] / m['valor_alvo']) if m['valor_alvo'] > 0 else 0\
            perc_display = min(perc * 100, 100.0)\
            \
            with st.container():\
                st.markdown(f"### \uc0\u55356 \u57263  \{m['nome']\}")\
                col_mt1, col_mt2, col_mt3, col_mt4 = st.columns(4)\
                with col_mt1:\
                    st.progress(min(perc, 1.0))\
                    st.caption(f"Progresso: **\{perc_display:.1f\}%**")\
                with col_mt2:\
                    st.markdown(f"**Acumulado:** `\{format_currency(m['valor_atual'])\}`")\
                with col_mt3:\
                    st.markdown(f"**Alvo:** `\{format_currency(m['valor_alvo'])\}`")\
                with col_mt4:\
                    falta = max(m['valor_alvo'] - m['valor_atual'], 0.0)\
                    st.markdown(f"**Falta:** `\{format_currency(falta)\}`")\
                \
                with st.expander(f"\uc0\u9881 \u65039  Atualizar ou Excluir '\{m['nome']\}'"):\
                    c_up1, c_up2 = st.columns(2)\
                    with c_up1:\
                        novo_v = st.number_input("Atualizar Saldo (R$):", value=float(m['valor_atual']), step=100.0, key=f"inp_\{m['id']\}")\
                        if st.button("Salvar Novo Saldo", key=f"btn_up_\{m['id']\}"):\
                            update_meta_valor(m['id'], novo_v)\
                            st.success("Valor atualizado!")\
                            st.rerun()\
                    with c_up2:\
                        st.markdown("<br>", unsafe_allow_html=True)\
                        if st.button("Excluir Meta", key=f"btn_del_\{m['id']\}", type="primary"):\
                            delete_meta(m['id'])\
                            st.warning("Meta exclu\'edda!")\
                            st.rerun()\
                st.markdown("---")\
    else:\
        st.info("Nenhuma meta cadastrada.")\
\
# 5. Relat\'f3rios em PDF\
elif menu == "\uc0\u55357 \u56516  Relat\'f3rios em PDF":\
    st.subheader("Gerador de Relat\'f3rios Oficiais em PDF")\
    \
    col_r1, col_r2 = st.columns(2)\
    with col_r1:\
        st.markdown(f"""\
        <div class="metric-card">\
            <h4>\uc0\u55357 \u56516  Par\'e2metros do Relat\'f3rio:</h4>\
            <ul>\
                <li><b>Cabe\'e7alho:</b> Finan\'e7as Fam\'edlia Almeida</li>\
                <li><b>Ano:</b> \{ano_selecionado\}</li>\
                <li><b>M\'eas:</b> \{nome_meses[mes_selecionado] if mes_selecionado else 'Todos os Meses (Consolidado)'\}</li>\
                <li><b>Total Cr\'e9dito:</b> \{format_currency(total_credito)\}</li>\
                <li><b>Total D\'e9bito / Sa\'eddas:</b> \{format_currency(total_saidas_geral)\}</li>\
                <li><b>Saldo L\'edquido:</b> \{format_currency(saldo_liquido)\}</li>\
            </ul>\
        </div>\
        """, unsafe_allow_html=True)\
        \
        st.markdown("<br>", unsafe_allow_html=True)\
        if st.button("\uc0\u55357 \u56960  Gerar Relat\'f3rio em PDF", type="primary", use_container_width=True):\
            if df_periodo.empty:\
                st.warning("N\'e3o h\'e1 lan\'e7amentos no per\'edodo para gerar o PDF.")\
            else:\
                pdf_bytes = generate_pdf_report(mes=mes_selecionado, ano=ano_selecionado)\
                nome_arquivo = f"Relatorio_Financas_Almeida_\{ano_selecionado\}_\{mes_selecionado or 'Anual'\}.pdf"\
                st.download_button(\
                    label="\uc0\u55357 \u56549  Baixar Relat\'f3rio em PDF",\
                    data=pdf_bytes,\
                    file_name=nome_arquivo,\
                    mime="application/pdf",\
                    use_container_width=True\
                )\
    \
    with col_r2:\
        st.info("""\
        **Conte\'fado do Relat\'f3rio:**\
        - Cabe\'e7alho formal 'Finan\'e7as Fam\'edlia Almeida'.\
        - Resumo Executivo (Entradas, Despesas, Aplica\'e7\'f5es, Saldo L\'edquido).\
        - Extrato Cronol\'f3gico (Data, Lan\'e7amento, Categoria, D\'e9bito, Cr\'e9dito, Saldo).\
        - Rodap\'e9 com data e hor\'e1rio de emiss\'e3o.\
        """)\
\
# 6. Configura\'e7\'f5es & Categorias\
elif menu == "\uc0\u9881 \u65039  Configura\'e7\'f5es & Categorias":\
    st.subheader("Categorias & Backup")\
    \
    col_c1, col_c2 = st.columns(2)\
    with col_c1:\
        st.markdown("#### \uc0\u10133  Nova Categoria")\
        with st.form("form_cat", clear_on_submit=True):\
            nova_cat = st.text_input("Nome da Categoria:")\
            tipo_cat = st.selectbox("Tipo:", ["Despesa", "Receita", "Investimento", "Economia"])\
            if st.form_submit_button("Salvar Categoria", use_container_width=True):\
                if nova_cat:\
                    if add_categoria(nova_cat, tipo_cat):\
                        st.success(f"Categoria '\{nova_cat\}' adicionada!")\
                        st.rerun()\
                    else:\
                        st.error("Categoria j\'e1 existente.")\
                        \
    with col_c2:\
        st.markdown("#### \uc0\u55357 \u56523  Categorias Ativas")\
        df_cats = pd.DataFrame(get_categorias())\
        st.dataframe(df_cats, use_container_width=True, hide_index=True)\
        \
    st.markdown("---")\
    if not df_ano.empty:\
        csv_data = df_ano.to_csv(index=False).encode('utf-8')\
        st.download_button(\
            "\uc0\u55357 \u56549  Exportar Lan\'e7amentos do Ano (CSV)",\
            data=csv_data,\
            file_name=f"financas_almeida_\{ano_selecionado\}.csv",\
            mime="text/csv"\
        )}