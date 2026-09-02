import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import io
import os
import urllib.parse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# ==========================================
# CONFIGURAÇÃO GERAL DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Finanças Família Almeida",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ESTILIZAÇÃO CSS MODERNA
# ==========================================
st.markdown("""
<style translate="no">
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .header-box {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 24px 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.25);
    }
    .header-title {
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
        color: #FFFFFF;
    }
    .header-subtitle {
        font-size: 14px;
        color: #DBEAFE;
        margin-top: 5px;
        margin-bottom: 0;
    }
    
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .metric-title {
        font-size: 13px;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 22px;
        font-weight: 800;
        margin-top: 6px;
    }
    .metric-green { color: #059669; }
    .metric-red { color: #DC2626; }
    .metric-blue { color: #2563EB; }
    .metric-purple { color: #7C3AED; }
    
    .login-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.08);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SISTEMA DE LOGIN COM SENHA
# ==========================================
def check_authentication():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        
    if not st.session_state.authenticated:
        col_esq, col_login, col_dir = st.columns(3)
        with col_login:
            st.markdown("""
            <div class="login-card" translate="no">
                <h2 style="color: #1E3A8A; margin-bottom: 4px;">🏛️ Finanças Família Almeida</h2>
                <p style="color: #6B7280; font-size: 14px; margin-bottom: 20px;">Acesso Restrito e Seguro</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("form_login"):
                senha_digitada = st.text_input("Digite a senha de acesso:", type="password", placeholder="Sua senha...")
                btn_entrar = st.form_submit_button("🔓 Acessar Sistema", type="primary", use_container_width=True)
                
                if btn_entrar:
                    senha_correta = st.secrets.get("SENHA_ACESSO", "Almeida@2026")
                    if senha_digitada == senha_correta:
                        st.session_state.authenticated = True
                        st.success("Acesso autorizado!")
                        st.rerun()
                    else:
                        st.error("Senha incorreta. Tente novamente.")
        st.stop()

check_authentication()

# ==========================================
# CONEXÃO COM BANCO DE DADOS (SUPABASE / POSTGRESQL / SQLITE)
# ==========================================
IS_POSTGRES = False
engine = None
db_error_msg = None

try:
    if "postgres" in st.secrets:
        pg = st.secrets["postgres"]
        user_enc = urllib.parse.quote_plus(str(pg.get("user", "postgres")))
        pass_enc = urllib.parse.quote_plus(str(pg.get("password", "")))
        host = str(pg.get("host", "")).strip()
        port = int(pg.get("port", 6543))
        dbname = str(pg.get("database", "postgres")).strip()
        DATABASE_URL = f"postgresql+psycopg2://{user_enc}:{pass_enc}@{host}:{port}/{dbname}"
        
        from sqlalchemy import create_engine, text
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as test_conn:
            test_conn.execute(text("SELECT 1"))
        IS_POSTGRES = True
        
    elif "DATABASE_URL" in st.secrets and len(str(st.secrets["DATABASE_URL"]).strip()) > 0:
        raw_url = str(st.secrets["DATABASE_URL"]).strip()
        if raw_url.startswith("postgres://"):
            raw_url = "postgresql+psycopg2://" + raw_url[11:]
        elif raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+psycopg2://"):
            raw_url = "postgresql+psycopg2://" + raw_url[13:]
            
        from sqlalchemy import create_engine, text
        engine = create_engine(raw_url, pool_pre_ping=True)
        with engine.connect() as test_conn:
            test_conn.execute(text("SELECT 1"))
        IS_POSTGRES = True
        
except Exception as e:
    IS_POSTGRES = False
    engine = None
    db_error_msg = str(e)

DB_FILE = "financas_familia_almeida.db"

def get_sqlite_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transacoes (
                id SERIAL PRIMARY KEY,
                data TEXT NOT NULL,
                dia INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                descricao TEXT NOT NULL,
                categoria TEXT NOT NULL,
                tipo TEXT NOT NULL,
                debito DOUBLE PRECISION DEFAULT 0.0,
                credito DOUBLE PRECISION DEFAULT 0.0,
                observacoes TEXT
            );
            """))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                nome TEXT UNIQUE NOT NULL,
                tipo TEXT NOT NULL
            );
            """))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS metas_economias (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                valor_alvo DOUBLE PRECISION NOT NULL,
                valor_atual DOUBLE PRECISION DEFAULT 0.0,
                data_limite TEXT,
                categoria TEXT
            );
            """))
            
            res = conn.execute(text("SELECT COUNT(*) FROM categorias")).scalar()
            if res == 0:
                categorias_iniciais = [
                    ("Salário", "Receita"),
                    ("Rendimentos de Investimentos", "Receita"),
                    ("Serviços Extras / Freelance", "Receita"),
                    ("Outras Receitas", "Receita"),
                    ("Moradia (Aluguel, Condomínio, IPTU)", "Despesa"),
                    ("Alimentação & Supermercado", "Despesa"),
                    ("Transporte & Combustível", "Despesa"),
                    ("Saúde, Convênio & Farmácia", "Despesa"),
                    ("Educação & Cursos", "Despesa"),
                    ("Lazer, Restaurantes & Viagens", "Despesa"),
                    ("Assinaturas & Conectividade", "Despesa"),
                    ("Compras Pessoais & Vestuário", "Despesa"),
                    ("Manutenção & Imprevistos", "Despesa"),
                    ("Impostos & Tarifas Bancárias", "Despesa"),
                    ("Reserva de Emergência", "Economia"),
                    ("Poupança para Objetivos", "Economia"),
                    ("Renda Fixa (CDB, Tesouro)", "Investimento"),
                    ("Renda Variável (Ações e FIIs)", "Investimento"),
                    ("Previdência Privada", "Investimento")
                ]
                for nome, tipo in categorias_iniciais:
                    conn.execute(text("INSERT INTO categorias (nome, tipo) VALUES (:n, :t) ON CONFLICT DO NOTHING"), {"n": nome, "t": tipo})
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            dia INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            ano INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            tipo TEXT NOT NULL,
            debito REAL DEFAULT 0.0,
            credito REAL DEFAULT 0.0,
            observacoes TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            tipo TEXT NOT NULL
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS metas_economias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor_alvo REAL NOT NULL,
            valor_atual REAL DEFAULT 0.0,
            data_limite TEXT,
            categoria TEXT
        )
        """)
        cursor.execute("SELECT COUNT(*) FROM categorias")
        if cursor.fetchone()[0] == 0:
            categorias_iniciais = [
                ("Salário", "Receita"),
                ("Rendimentos de Investimentos", "Receita"),
                ("Serviços Extras / Freelance", "Receita"),
                ("Outras Receitas", "Receita"),
                ("Moradia (Aluguel, Condomínio, IPTU)", "Despesa"),
                ("Alimentação & Supermercado", "Despesa"),
                ("Transporte & Combustível", "Despesa"),
                ("Saúde, Convênio & Farmácia", "Despesa"),
                ("Educação & Cursos", "Despesa"),
                ("Lazer, Restaurantes & Viagens", "Despesa"),
                ("Assinaturas & Conectividade", "Despesa"),
                ("Compras Pessoais & Vestuário", "Despesa"),
                ("Manutenção & Imprevistos", "Despesa"),
                ("Impostos & Tarifas Bancárias", "Despesa"),
                ("Reserva de Emergência", "Economia"),
                ("Poupança para Objetivos", "Economia"),
                ("Renda Fixa (CDB, Tesouro)", "Investimento"),
                ("Renda Variável (Ações e FIIs)", "Investimento"),
                ("Previdência Privada", "Investimento")
            ]
            cursor.executemany("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", categorias_iniciais)
        conn.commit()
        conn.close()

init_database()

# ==========================================
# FUNÇÕES DE CRUD
# ==========================================
def get_categorias(tipo=None):
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        with engine.connect() as conn:
            if tipo:
                df = pd.read_sql_query(text("SELECT nome FROM categorias WHERE tipo = :t ORDER BY nome ASC"), conn, params={"t": tipo})
                return df["nome"].tolist()
            else:
                df = pd.read_sql_query(text("SELECT nome, tipo FROM categorias ORDER BY tipo, nome ASC"), conn)
                return df.to_dict(orient="records")
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        if tipo:
            cursor.execute("SELECT nome FROM categorias WHERE tipo = ? ORDER BY nome ASC", (tipo,))
            rows = cursor.fetchall()
            conn.close()
            return [r["nome"] for r in rows]
        else:
            cursor.execute("SELECT nome, tipo FROM categorias ORDER BY tipo, nome ASC")
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]

def add_categoria(nome, tipo):
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        try:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO categorias (nome, tipo) VALUES (:n, :t)"), {"n": nome.strip(), "t": tipo})
            return True
        except Exception:
            return False
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", (nome.strip(), tipo))
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        conn.close()
        return success

def insert_transacao(data_str, descricao, categoria, tipo, valor, observacoes=""):
    d_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
    debito = float(valor) if tipo in ["Débito", "Aplicação", "Economia"] else 0.0
    credito = float(valor) if tipo == "Crédito" else 0.0
    
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO transacoes (data, dia, mes, ano, descricao, categoria, tipo, debito, credito, observacoes)
            VALUES (:d, :dia, :mes, :ano, :desc, :cat, :tipo, :deb, :cred, :obs)
            """), {
                "d": data_str, "dia": d_obj.day, "mes": d_obj.month, "ano": d_obj.year,
                "desc": descricao.strip(), "cat": categoria, "tipo": tipo,
                "deb": debito, "cred": credito, "obs": observacoes.strip()
            })
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO transacoes (data, dia, mes, ano, descricao, categoria, tipo, debito, credito, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data_str, d_obj.day, d_obj.month, d_obj.year, descricao.strip(), categoria, tipo, debito, credito, observacoes.strip()))
        conn.commit()
        conn.close()

def update_transacao(transacao_id, data_str, descricao, categoria, tipo, valor, observacoes=""):
    d_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
    debito = float(valor) if tipo in ["Débito", "Aplicação", "Economia"] else 0.0
    credito = float(valor) if tipo == "Crédito" else 0.0
    
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("""
            UPDATE transacoes 
            SET data = :d, dia = :dia, mes = :mes, ano = :ano, descricao = :desc, categoria = :cat, tipo = :tipo, debito = :deb, credito = :cred, observacoes = :obs
            WHERE id = :id
            """), {
                "d": data_str, "dia": d_obj.day, "mes": d_obj.month, "ano": d_obj.year,
                "desc": descricao.strip(), "cat": categoria, "tipo": tipo,
                "deb": debito, "cred": credito, "obs": observacoes.strip(), "id": transacao_id
            })
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE transacoes 
        SET data = ?, dia = ?, mes = ?, ano = ?, descricao = ?, categoria = ?, tipo = ?, debito = ?, credito = ?, observacoes = ?
        WHERE id = ?
        """, (data_str, d_obj.day, d_obj.month, d_obj.year, descricao.strip(), categoria, tipo, debito, credito, observacoes.strip(), transacao_id))
        conn.commit()
        conn.close()

def delete_transacao(transacao_id):
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM transacoes WHERE id = :id"), {"id": transacao_id})
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))
        conn.commit()
        conn.close()

def load_transacoes(mes=None, ano=None):
    query_str = "SELECT * FROM transacoes WHERE 1=1"
    params_dict = {}
    params_list = []
    
    if ano:
        query_str += " AND ano = :ano" if IS_POSTGRES else " AND ano = ?"
        params_dict["ano"] = ano
        params_list.append(ano)
    if mes:
        query_str += " AND mes = :mes" if IS_POSTGRES else " AND mes = ?"
        params_dict["mes"] = mes
        params_list.append(mes)
        
    query_str += " ORDER BY data ASC, id ASC"
    
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        with engine.connect() as conn:
            df = pd.read_sql_query(text(query_str), conn, params=params_dict)
    else:
        conn = get_sqlite_conn()
        df = pd.read_sql_query(query_str, conn, params=params_list)
        conn.close()
        
    if not df.empty:
        df['saldo_linha'] = df['credito'] - df['debito']
        df['saldo_acumulado'] = df['saldo_linha'].cumsum()
    else:
        df = pd.DataFrame(columns=[
            'id', 'data', 'dia', 'mes', 'ano', 'descricao', 
            'categoria', 'tipo', 'debito', 'credito', 'observacoes', 
            'saldo_linha', 'saldo_acumulado'
        ])
    return df

def get_anos_disponiveis():
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        with engine.connect() as conn:
            df = pd.read_sql_query(text("SELECT DISTINCT ano FROM transacoes ORDER BY ano DESC"), conn)
            anos = df['ano'].tolist()
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ano FROM transacoes ORDER BY ano DESC")
        anos = [r[0] for r in cursor.fetchall()]
        conn.close()
        
    current_year = datetime.now().year
    if current_year not in anos:
        anos.insert(0, current_year)
    return anos

def format_currency(val):
    if pd.isna(val) or val is None:
        val = 0.0
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_metas():
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        with engine.connect() as conn:
            df = pd.read_sql_query(text("SELECT * FROM metas_economias ORDER BY id DESC"), conn)
            return df.to_dict(orient="records")
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM metas_economias ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

def insert_meta(nome, valor_alvo, valor_atual, data_limite, categoria):
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO metas_economias (nome, valor_alvo, valor_atual, data_limite, categoria)
            VALUES (:n, :alvo, :atual, :dt, :cat)
            """), {
                "n": nome, "alvo": float(valor_alvo), "atual": float(valor_atual),
                "dt": data_limite, "cat": categoria
            })
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO metas_economias (nome, valor_alvo, valor_atual, data_limite, categoria)
        VALUES (?, ?, ?, ?, ?)
        """, (nome, float(valor_alvo), float(valor_atual), data_limite, categoria))
        conn.commit()
        conn.close()

def update_meta_valor(meta_id, novo_valor):
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("UPDATE metas_economias SET valor_atual = :v WHERE id = :id"), {"v": float(novo_valor), "id": meta_id})
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE metas_economias SET valor_atual = ? WHERE id = ?", (float(novo_valor), meta_id))
        conn.commit()
        conn.close()

def delete_meta(meta_id):
    if IS_POSTGRES and engine is not None:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM metas_economias WHERE id = :id"), {"id": meta_id})
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM metas_economias WHERE id = ?", (meta_id,))
        conn.commit()
        conn.close()

# ==========================================
# GERADOR DE RELATÓRIO EM PDF
# ==========================================
def generate_pdf_report(mes, ano):
    df = load_transacoes(mes, ano)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#4B5563'),
        alignment=1,
        spaceAfter=15
    )
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=12,
        spaceAfter=6
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1F2937')
    )
    header_cell_style = ParagraphStyle(
        'HeaderCellText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.white
    )

    elements = []
    
    elements.append(Paragraph("<b>Finanças Família Almeida</b>", title_style))
    nome_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_str = nome_meses[mes-1] if (mes and 1 <= mes <= 12) else "Consolidado Anual"
    elements.append(Paragraph(f"Relatório Financeiro Oficial — {mes_str} / {ano}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceAfter=14))
    
    total_credito = df['credito'].sum() if not df.empty else 0.0
    total_debito = df[df['tipo'] == 'Débito']['debito'].sum() if not df.empty else 0.0
    total_aplicado = df[df['tipo'] == 'Aplicação']['debito'].sum() if not df.empty else 0.0
    total_poupado = df[df['tipo'] == 'Economia']['debito'].sum() if not df.empty else 0.0
    saldo_liquido = total_credito - total_debito - total_aplicado - total_poupado
    
    summary_data = [
        [
            Paragraph("<b>Total Entradas</b>", cell_style),
            Paragraph("<b>Despesas</b>", cell_style),
            Paragraph("<b>Aplicações</b>", cell_style),
            Paragraph("<b>Economias</b>", cell_style),
            Paragraph("<b>Saldo Líquido</b>", cell_style)
        ],
        [
            format_currency(total_credito),
            format_currency(total_debito),
            format_currency(total_aplicado),
            format_currency(total_poupado),
            format_currency(saldo_liquido)
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[3.4*cm, 3.4*cm, 3.4*cm, 3.4*cm, 3.4*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3F4F6')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F9FAFB')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TEXTCOLOR', (0,1), (0,1), colors.HexColor('#059669')),
        ('TEXTCOLOR', (1,1), (1,1), colors.HexColor('#DC2626')),
        ('TEXTCOLOR', (2,1), (2,1), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (3,1), (3,1), colors.HexColor('#7C3AED')),
        ('TEXTCOLOR', (4,1), (4,1), colors.HexColor('#0D9488') if saldo_liquido >= 0 else colors.HexColor('#DC2626')),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 14))
    
    elements.append(Paragraph("<b>Extrato de Lançamentos</b>", section_style))
    table_data = [[
        Paragraph("<b>Data</b>", header_cell_style),
        Paragraph("<b>Lançamento</b>", header_cell_style),
        Paragraph("<b>Categoria</b>", header_cell_style),
        Paragraph("<b>Tipo</b>", header_cell_style),
        Paragraph("<b>Débito</b>", header_cell_style),
        Paragraph("<b>Crédito</b>", header_cell_style),
        Paragraph("<b>Saldo</b>", header_cell_style),
    ]]
    
    for _, row in df.iterrows():
        deb_str = format_currency(row['debito']) if row['debito'] > 0 else "-"
        cred_str = format_currency(row['credito']) if row['credito'] > 0 else "-"
        saldo_str = format_currency(row['saldo_acumulado'])
        
        table_data.append([
            f"{int(row['dia']):02d}/{int(row['mes']):02d}/{int(row['ano'])}",
            Paragraph(str(row['descricao'])[:32], cell_style),
            Paragraph(str(row['categoria'])[:25], cell_style),
            str(row['tipo']),
            deb_str,
            cred_str,
            saldo_str
        ])
        
    item_table = Table(table_data, colWidths=[1.8*cm, 4.3*cm, 3.5*cm, 1.8*cm, 2.2*cm, 2.2*cm, 2.2*cm])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (0,1), (0,-1), 'CENTER'),
        ('ALIGN', (3,1), (3,-1), 'CENTER'),
        ('ALIGN', (4,0), (-1,-1), 'RIGHT'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9FAFB')])
    ]))
    elements.append(item_table)
    
    elements.append(Spacer(1, 15))
    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")
    elements.append(Paragraph(f"<font size=7 color='#6B7280'>Documento emitido pelo aplicativo Finanças Família Almeida em {data_geracao}.</font>", cell_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================
st.markdown("""
<div class="header-box" translate="no">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 class="header-title">🏛️ Finanças Família Almeida</h1>
            <p class="header-subtitle">Sistema Integrado de Gestão Financeira, Aplicações e Economias</p>
        </div>
        <div style="text-align: right; background: rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 10px;">
            <span style="font-size: 13px; font-weight: 600; color: #FFFFFF;">📅 Gestão Mensal & Anual</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("🧭 Navegação & Filtros")

# Status da Conexão
if IS_POSTGRES:
    st.sidebar.success("🟢 Conectado ao Supabase (Nuvem)")
else:
    st.sidebar.info("⚪ Usando Banco Local (SQLite)")
    if db_error_msg:
        with st.sidebar.expander("ℹ️ Detalhes da Conexão"):
            st.caption(f"Aviso: {db_error_msg}")

if st.sidebar.button("🔒 Sair do Aplicativo"):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Módulo:",
    [
        "📊 Dashboard Geral", 
        "📝 Lançamentos & Extrato", 
        "📈 Análise de Aplicações", 
        "🎯 Economias & Metas", 
        "📄 Relatórios em PDF",
        "⚙️ Configurações & Categorias"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Período de Análise")

anos_disponiveis = get_anos_disponiveis()
ano_selecionado = st.sidebar.selectbox("Ano:", anos_disponiveis, index=0)

nome_meses = [
    "Todos os Meses (Anual)", "01 - Janeiro", "02 - Fevereiro", "03 - Março", 
    "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", 
    "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"
]
mes_atual_idx = datetime.now().month
mes_selecionado_str = st.sidebar.selectbox("Mês:", nome_meses, index=mes_atual_idx)

if mes_selecionado_str == "Todos os Meses (Anual)":
    mes_selecionado = None
    mes_label = f"Ano de {ano_selecionado}"
else:
    mes_selecionado = int(mes_selecionado_str.split(" - ")[0])
    mes_label = f"{nome_meses[mes_selecionado]} de {ano_selecionado}"

df_periodo = load_transacoes(mes=mes_selecionado, ano=ano_selecionado)
df_ano = load_transacoes(mes=None, ano=ano_selecionado)

total_credito = df_periodo['credito'].sum() if not df_periodo.empty else 0.0
total_debito = df_periodo[df_periodo['tipo'] == 'Débito']['debito'].sum() if not df_periodo.empty else 0.0
total_aplicacoes = df_periodo[df_periodo['tipo'] == 'Aplicação']['debito'].sum() if not df_periodo.empty else 0.0
total_economias = df_periodo[df_periodo['tipo'] == 'Economia']['debito'].sum() if not df_periodo.empty else 0.0
total_saidas_geral = total_debito + total_aplicacoes + total_economias
saldo_liquido = total_credito - total_saidas_geral
taxa_poupanca = ((total_aplicacoes + total_economias) / total_credito * 100) if total_credito > 0 else 0.0

# 1. Dashboard Geral
if menu == "📊 Dashboard Geral":
    st.subheader(f"Visão Executiva — {mes_label}")
    
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card" translate="no">
            <div class="metric-title">Entradas (Crédito)</div>
            <div class="metric-value metric-green">{format_currency(total_credito)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card" translate="no">
            <div class="metric-title">Despesas (Débito)</div>
            <div class="metric-value metric-red">{format_currency(total_debito)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card" translate="no">
            <div class="metric-title">Aplicações (Invest.)</div>
            <div class="metric-value metric-blue">{format_currency(total_aplicacoes)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card" translate="no">
            <div class="metric-title">Economias (Reserva)</div>
            <div class="metric-value metric-purple">{format_currency(total_economias)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        cor_saldo = "metric-green" if saldo_liquido >= 0 else "metric-red"
        st.markdown(f"""
        <div class="metric-card" translate="no">
            <div class="metric-title">Saldo Líquido</div>
            <div class="metric-value {cor_saldo}">{format_currency(saldo_liquido)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("#### 📈 Evolução Mensal do Ano")
        if not df_ano.empty:
            resumo_mensal = df_ano.groupby('mes').agg({
                'credito': 'sum',
                'debito': 'sum'
            }).reset_index()
            resumo_mensal['Nome_Mes'] = resumo_mensal['mes'].apply(lambda m: ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"][m-1])
            resumo_mensal['Saldo'] = resumo_mensal['credito'] - resumo_mensal['debito']
            
            chart_df = resumo_mensal.set_index('Nome_Mes')[['credito', 'debito', 'Saldo']]
            chart_df.columns = ['Entradas', 'Saídas', 'Saldo Líquido']
            st.bar_chart(chart_df, height=320)
        else:
            st.info("Nenhum lançamento registrado para este ano.")

    with col_g2:
        st.markdown("#### 🍕 Despesas por Categoria")
        despesas_df = df_periodo[df_periodo['tipo'] == 'Débito']
        if not despesas_df.empty:
            cat_df = despesas_df.groupby('categoria')['debito'].sum().reset_index()
            cat_df = cat_df.sort_values(by='debito', ascending=False)
            cat_df['Valor'] = cat_df['debito'].apply(format_currency)
            cat_df['% do Total'] = (cat_df['debito'] / cat_df['debito'].sum() * 100).round(1).astype(str) + "%"
            st.dataframe(cat_df[['categoria', 'Valor', '% do Total']], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma despesa lançada no período.")

    st.markdown("---")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown(f"**Taxa de Economia & Aporte:** `{taxa_poupanca:.1f}%` guardada/investida.")
        st.progress(min(max(taxa_poupanca / 100, 0.0), 1.0))
    with col_p2:
        st.markdown(f"**Resultado Líquido do Período:** `{format_currency(saldo_liquido)}`")

# 2. Lançamentos & Extrato
elif menu == "📝 Lançamentos & Extrato":
    st.subheader("Gerenciador de Lançamentos")
    
    tab_novo, tab_editar = st.tabs(["➕ Novo Lançamento", "✏️ Editar Lançamento"])
    
    with tab_novo:
        with st.form("form_novo_lancamento", clear_on_submit=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                data_lancamento = st.date_input("Data do Lançamento:", value=date.today(), key="novo_data")
                tipo_lancamento = st.selectbox(
                    "Tipo de Operação:", 
                    ["Débito (Despesa)", "Crédito (Receita)", "Aplicação (Investimento)", "Economia (Reserva/Metas)"],
                    key="novo_tipo"
                )
            
            tipo_map = {
                "Débito (Despesa)": ("Débito", "Despesa"),
                "Crédito (Receita)": ("Crédito", "Receita"),
                "Aplicação (Investimento)": ("Aplicação", "Investimento"),
                "Economia (Reserva/Metas)": ("Economia", "Economia")
            }
            tipo_db, cat_tipo = tipo_map[tipo_lancamento]
            categorias_disponiveis = get_categorias(cat_tipo)
            if not categorias_disponiveis:
                categorias_disponiveis = get_categorias()
                
            with col_f2:
                descricao = st.text_input("Descrição / Lançamento:", placeholder="Ex: Salário, Supermercado, Aporte CDB...", key="novo_desc")
                categoria = st.selectbox("Categoria Agregada:", categorias_disponiveis, key="novo_cat")
                
            with col_f3:
                valor = st.number_input("Valor (R$):", min_value=0.01, step=50.0, format="%.2f", key="novo_valor")
                observacoes = st.text_input("Observações (Opcional):", placeholder="Detalhes...", key="novo_obs")
                
            submitted = st.form_submit_button("💾 Salvar Lançamento", use_container_width=True)
            if submitted:
                if not descricao:
                    st.error("Preencha a descrição do lançamento.")
                else:
                    insert_transacao(
                        data_str=data_lancamento.strftime("%Y-%m-%d"),
                        descricao=descricao,
                        categoria=categoria,
                        tipo=tipo_db,
                        valor=valor,
                        observacoes=observacoes
                    )
                    st.success(f"Lançamento '{descricao}' de {format_currency(valor)} registrado com sucesso!")
                    st.rerun()

    with tab_editar:
        df_todas = load_transacoes(mes=None, ano=ano_selecionado)
        if not df_todas.empty:
            opcoes_transacoes = df_todas['id'].tolist()
            
            def format_opcao(tid):
                row = df_todas[df_todas['id'] == tid].iloc[0]
                val = row['debito'] if row['debito'] > 0 else row['credito']
                return f"ID {tid} | {int(row['dia']):02d}/{int(row['mes']):02d}/{int(row['ano'])} - {row['descricao']} ({format_currency(val)}) [{row['tipo']}]"
            
            transacao_selecionada_id = st.selectbox(
                "Selecione o lançamento que deseja editar:",
                opcoes_transacoes,
                format_func=format_opcao,
                key="select_edit_transacao"
            )
            
            item_atual = df_todas[df_todas['id'] == transacao_selecionada_id].iloc[0]
            data_atual_obj = datetime.strptime(str(item_atual['data'])[:10], "%Y-%m-%d").date()
            valor_atual_num = float(item_atual['debito'] if item_atual['debito'] > 0 else item_atual['credito'])
            
            tipo_invert_map = {
                "Débito": "Débito (Despesa)",
                "Crédito": "Crédito (Receita)",
                "Aplicação": "Aplicação (Investimento)",
                "Economia": "Economia (Reserva/Metas)"
            }
            tipo_label_atual = tipo_invert_map.get(item_atual['tipo'], "Débito (Despesa)")
            lista_tipos = ["Débito (Despesa)", "Crédito (Receita)", "Aplicação (Investimento)", "Economia (Reserva/Metas)"]
            tipo_index_atual = lista_tipos.index(tipo_label_atual) if tipo_label_atual in lista_tipos else 0
            
            with st.form(f"form_editar_{transacao_selecionada_id}"):
                c_e1, c_e2, c_e3 = st.columns(3)
                with c_e1:
                    edit_data = st.date_input("Data:", value=data_atual_obj, key=f"edit_data_{transacao_selecionada_id}")
                    edit_tipo_label = st.selectbox(
                        "Tipo de Operação:", 
                        lista_tipos, 
                        index=tipo_index_atual, 
                        key=f"edit_tipo_{transacao_selecionada_id}"
                    )
                
                tipo_map = {
                    "Débito (Despesa)": ("Débito", "Despesa"),
                    "Crédito (Receita)": ("Crédito", "Receita"),
                    "Aplicação (Investimento)": ("Aplicação", "Investimento"),
                    "Economia (Reserva/Metas)": ("Economia", "Economia")
                }
                edit_tipo_db, edit_cat_tipo = tipo_map[edit_tipo_label]
                cats_para_editar = get_categorias(edit_cat_tipo)
                if not cats_para_editar:
                    cats_para_editar = get_categorias()
                cat_index_atual = cats_para_editar.index(item_atual['categoria']) if item_atual['categoria'] in cats_para_editar else 0
                
                with c_e2:
                    edit_descricao = st.text_input("Descrição / Lançamento:", value=str(item_atual['descricao']), key=f"edit_desc_{transacao_selecionada_id}")
                    edit_categoria = st.selectbox("Categoria:", cats_para_editar, index=cat_index_atual, key=f"edit_cat_{transacao_selecionada_id}")
                    
                with c_e3:
                    edit_valor = st.number_input("Valor (R$):", min_value=0.01, step=50.0, format="%.2f", value=valor_atual_num, key=f"edit_val_{transacao_selecionada_id}")
                    edit_obs = st.text_input("Observações:", value=str(item_atual['observacoes'] or ''), key=f"edit_obs_{transacao_selecionada_id}")
                    
                btn_salvar_edicao = st.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True)
                if btn_salvar_edicao:
                    if not edit_descricao:
                        st.error("A descrição não pode ficar vazia.")
                    else:
                        update_transacao(
                            transacao_id=transacao_selecionada_id,
                            data_str=edit_data.strftime("%Y-%m-%d"),
                            descricao=edit_descricao,
                            categoria=edit_categoria,
                            tipo=edit_tipo_db,
                            valor=edit_valor,
                            observacoes=edit_obs
                        )
                        st.success(f"Lançamento '{edit_descricao}' atualizado com sucesso!")
                        st.rerun()
        else:
            st.info("Nenhum lançamento cadastrado no ano selecionado para editar.")

    st.markdown("---")
    st.subheader(f"Extrato Cronológico — {mes_label}")
    
    if not df_periodo.empty:
        df_exibir = df_periodo.copy()
        df_exibir['Data'] = df_exibir['dia'].astype(int).astype(str).str.zfill(2) + '/' + df_exibir['mes'].astype(int).astype(str).str.zfill(2) + '/' + df_exibir['ano'].astype(int).astype(str)
        df_exibir['Débito'] = df_exibir['debito'].apply(lambda x: format_currency(x) if x > 0 else "-")
        df_exibir['Crédito'] = df_exibir['credito'].apply(lambda x: format_currency(x) if x > 0 else "-")
        df_exibir['Saldo'] = df_exibir['saldo_acumulado'].apply(format_currency)
        
        busca = st.text_input("🔍 Filtrar lançamentos:", "")
        if busca:
            df_exibir = df_exibir[
                df_exibir['descricao'].str.contains(busca, case=False, na=False) |
                df_exibir['categoria'].str.contains(busca, case=False, na=False) |
                df_exibir['Data'].str.contains(busca, case=False, na=False)
            ]
        
        st.dataframe(
            df_exibir[['id', 'Data', 'descricao', 'categoria', 'tipo', 'Débito', 'Crédito', 'Saldo', 'observacoes']],
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "Data": st.column_config.TextColumn("Data", width="small"),
                "descricao": st.column_config.TextColumn("Lançamento", width="medium"),
                "categoria": st.column_config.TextColumn("Categoria", width="medium"),
                "tipo": st.column_config.TextColumn("Tipo", width="small"),
                "Débito": st.column_config.TextColumn("Débito (R$)", width="small"),
                "Crédito": st.column_config.TextColumn("Crédito (R$)", width="small"),
                "Saldo": st.column_config.TextColumn("Saldo Acumulado", width="small"),
                "observacoes": st.column_config.TextColumn("Observações", width="medium"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        with st.expander("🗑️ Excluir Lançamento"):
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                transacao_para_excluir = st.selectbox(
                    "Selecione o lançamento para excluir:",
                    df_periodo['id'].tolist(),
                    format_func=lambda tid: f"ID {tid} - {df_periodo[df_periodo['id']==tid]['descricao'].values[0]}"
                )
            with col_del2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Excluir", type="primary", use_container_width=True):
                    delete_transacao(transacao_para_excluir)
                    st.success("Lançamento excluído!")
                    st.rerun()
    else:
        st.info(f"Nenhum lançamento em {mes_label}.")

# 3. Análise de Aplicações
elif menu == "📈 Análise de Aplicações":
    st.subheader(f"Carteira de Aplicações & Investimentos — {mes_label}")
    
    df_aplicacoes = df_periodo[df_periodo['tipo'] == 'Aplicação']
    df_aplicacoes_ano = df_ano[df_ano['tipo'] == 'Aplicação']
    
    col_a1, col_a2, col_a3 = st.columns(3)
    total_aplicado_ano = df_aplicacoes_ano['debito'].sum() if not df_aplicacoes_ano.empty else 0.0
    with col_a1:
        st.markdown(f"""
        <div class="metric-card" translate="no">
            <div class="metric-title">Aportes no Mês</div>
            <div class="metric-value metric-blue">{format_currency(total_aplicacoes)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_a2:
        st.markdown(f"""
        <div class="metric-card" translate="no">
            <div class="metric-title">Total Aportado em {ano_selecionado}</div>
            <div class="metric-value metric-blue">{format_currency(total_aplicado_ano)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_a3:
        rendimentos_ano = df_ano[df_ano['categoria'].str.contains("Rendimento", case=False, na=False)]['credito'].sum()
        st.markdown(f"""
        <div class="metric-card" translate="no">
            <div class="metric-title">Rendimentos ({ano_selecionado})</div>
            <div class="metric-value metric-green">{format_currency(rendimentos_ano)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_inv1, col_inv2 = st.columns(2)
    with col_inv1:
        st.markdown("#### 📊 Aportes por Classe de Ativo")
        if not df_aplicacoes_ano.empty:
            cat_inv = df_aplicacoes_ano.groupby('categoria')['debito'].sum().reset_index()
            cat_inv.columns = ['Classe de Ativo', 'Total Aportado (R$)']
            st.bar_chart(cat_inv.set_index('Classe de Ativo'), height=300)
        else:
            st.info("Nenhuma aplicação financeira registrada no período.")
            
    with col_inv2:
        st.markdown("#### 📋 Histórico de Aportes")
        if not df_aplicacoes.empty:
            df_ap_show = df_aplicacoes.copy()
            df_ap_show['Data'] = df_ap_show['dia'].astype(int).astype(str).str.zfill(2) + '/' + df_ap_show['mes'].astype(int).astype(str).str.zfill(2) + '/' + df_ap_show['ano'].astype(int).astype(str)
            df_ap_show['Valor'] = df_ap_show['debito'].apply(format_currency)
            st.dataframe(df_ap_show[['Data', 'descricao', 'categoria', 'Valor']], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum aporte no período selecionado.")

# 4. Economias & Metas
elif menu == "🎯 Economias & Metas":
    st.subheader("Reserva de Emergência & Metas da Família")
    
    with st.expander("➕ Cadastrar Nova Meta"):
        with st.form("form_meta"):
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1:
                nome_meta = st.text_input("Nome do Objetivo:", placeholder="Ex: Reserva 6 Meses, Viagem")
            with c_m2:
                valor_alvo = st.number_input("Valor Alvo (R$):", min_value=100.0, step=500.0)
            with c_m3:
                valor_inicial = st.number_input("Valor Já Guardado (R$):", min_value=0.0, step=100.0)
            
            c_m4, c_m5 = st.columns(2)
            with c_m4:
                data_limite = st.date_input("Data Alvo / Limite:")
            with c_m5:
                cat_meta = st.selectbox("Categoria:", ["Reserva de Emergência", "Poupança / Metas", "Outros Objetivos"])
                
            if st.form_submit_button("Salvar Meta", use_container_width=True):
                if nome_meta:
                    insert_meta(nome_meta, valor_alvo, valor_inicial, data_limite.strftime("%Y-%m-%d"), cat_meta)
                    st.success(f"Meta '{nome_meta}' cadastrada!")
                    st.rerun()
                    
    st.markdown("---")
    metas = get_metas()
    if metas:
        for m in metas:
            perc = (float(m['valor_atual']) / float(m['valor_alvo'])) if float(m['valor_alvo']) > 0 else 0
            perc_display = min(perc * 100, 100.0)
            
            with st.container():
                st.markdown(f"### 🎯 {m['nome']}")
                col_mt1, col_mt2, col_mt3, col_mt4 = st.columns(4)
                with col_mt1:
                    st.progress(min(perc, 1.0))
                    st.caption(f"Progresso: **{perc_display:.1f}%**")
                with col_mt2:
                    st.markdown(f"**Acumulado:** `{format_currency(m['valor_atual'])}`")
                with col_mt3:
                    st.markdown(f"**Alvo:** `{format_currency(m['valor_alvo'])}`")
                with col_mt4:
                    falta = max(float(m['valor_alvo']) - float(m['valor_atual']), 0.0)
                    st.markdown(f"**Falta:** `{format_currency(falta)}`")
                
                with st.expander(f"⚙️ Atualizar ou Excluir '{m['nome']}'"):
                    c_up1, c_up2 = st.columns(2)
                    with c_up1:
                        novo_v = st.number_input("Atualizar Saldo (R$):", value=float(m['valor_atual']), step=100.0, key=f"inp_{m['id']}")
                        if st.button("Salvar Novo Saldo", key=f"btn_up_{m['id']}"):
                            update_meta_valor(m['id'], novo_v)
                            st.success("Valor atualizado!")
                            st.rerun()
                    with c_up2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("Excluir Meta", key=f"btn_del_{m['id']}", type="primary"):
                            delete_meta(m['id'])
                            st.warning("Meta excluída!")
                            st.rerun()
                st.markdown("---")
    else:
        st.info("Nenhuma meta cadastrada.")

# 5. Relatórios em PDF
elif menu == "📄 Relatórios em PDF":
    st.subheader("Gerador de Relatórios Oficiais em PDF")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown(f"""
        <div class="metric-card" translate="no">
            <h4>📄 Parâmetros do Relatório:</h4>
            <ul>
                <li><b>Cabeçalho:</b> Finanças Família Almeida</li>
                <li><b>Ano:</b> {ano_selecionado}</li>
                <li><b>Mês:</b> {nome_meses[mes_selecionado] if mes_selecionado else 'Todos os Meses (Consolidado)'}</li>
                <li><b>Total Crédito:</b> {format_currency(total_credito)}</li>
                <li><b>Total Débito / Saídas:</b> {format_currency(total_saidas_geral)}</li>
                <li><b>Saldo Líquido:</b> {format_currency(saldo_liquido)}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Gerar Relatório em PDF", type="primary", use_container_width=True):
            if df_periodo.empty:
                st.warning("Não há lançamentos no período para gerar o PDF.")
            else:
                pdf_bytes = generate_pdf_report(mes=mes_selecionado, ano=ano_selecionado)
                nome_arquivo = f"Relatorio_Financas_Almeida_{ano_selecionado}_{mes_selecionado or 'Anual'}.pdf"
                st.download_button(
                    label="📥 Baixar Relatório em PDF",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True
                )
    
    with col_r2:
        st.info("""
        **Conteúdo do Relatório:**
        - Cabeçalho formal 'Finanças Família Almeida'.
        - Resumo Executivo (Entradas, Despesas, Aplicações, Saldo Líquido).
        - Extrato Cronológico (Data, Lançamento, Categoria, Débito, Crédito, Saldo).
        - Rodapé com data e horário de emissão.
        """)

# 6. Configurações & Categorias
elif menu == "⚙️ Configurações & Categorias":
    st.subheader("Categorias & Backup")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("#### ➕ Nova Categoria")
        with st.form("form_cat", clear_on_submit=True):
            nova_cat = st.text_input("Nome da Categoria:")
            tipo_cat = st.selectbox("Tipo:", ["Despesa", "Receita", "Investimento", "Economia"])
            if st.form_submit_button("Salvar Categoria", use_container_width=True):
                if nova_cat:
                    if add_categoria(nova_cat, tipo_cat):
                        st.success(f"Categoria '{nova_cat}' adicionada!")
                        st.rerun()
                    else:
                        st.error("Categoria já existente.")
                        
    with col_c2:
        st.markdown("#### 📋 Categorias Ativas")
        df_cats = pd.DataFrame(get_categorias())
        st.dataframe(df_cats, use_container_width=True, hide_index=True)
        
    st.markdown("---")
    if not df_ano.empty:
        csv_data = df_ano.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exportar Lançamentos do Ano (CSV)",
            data=csv_data,
            file_name=f"financas_almeida_{ano_selecionado}.csv",
            mime="text/csv"
        )
