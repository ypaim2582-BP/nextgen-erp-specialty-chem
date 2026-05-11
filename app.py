"""
ELEVNOVA ERP — Web Dashboard
Built with Streamlit | Connects to AWS PostgreSQL (RDS)
Author: Yuri Paim | May 2026
"""

import streamlit as st
import pandas as pd
import psycopg2
import base64
import os
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ELEVNOVA ERP — Elevate to the Next Standard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main area */
    .main { background-color: #F0F2F6; }
    h1 { color: #1B3A6B; }
    h2 { color: #2E6DB4; }
    .critical { color: #C0392B; font-weight: bold; }
    .ok       { color: #1A7A4A; font-weight: bold; }
    .warning  { color: #D05A1E; font-weight: bold; }

    /* Sidebar — dark navy with WHITE text */
    [data-testid="stSidebar"] {
        background-color: #0D1B2A !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #FFFFFF !important;
        font-size: 15px;
    }
    [data-testid="stSidebar"] hr {
        border-color: #C9A84C !important;
    }
    [data-testid="stSidebar"] h2 {
        color: #C9A84C !important;
    }
    /* Gold accent on selected nav item */
    [data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
        background-color: #C9A84C !important;
        border-radius: 6px;
    }
    /* Metric cards */
    [data-testid="metric-container"] {
        background: white;
        border-radius: 10px;
        padding: 15px;
        border-left: 4px solid #C9A84C;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    /* Refresh Data button — gold border, white text, always visible */
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        color: #FFFFFF !important;
        border: 2px solid #C9A84C !important;
        border-radius: 8px !important;
        width: 100%;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #C9A84C !important;
        color: #0D1B2A !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Logo helper ────────────────────────────────────────────────────────────────
def get_logo_html():
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{data}" style="width:100%;max-width:180px;margin:0 auto 8px;display:block;" />'
    return ""

# ── Database connection ────────────────────────────────────────────────────────
DB = {
    "host":     "nextgen-erp-db.c3qi4eq26ej7.eu-north-1.rds.amazonaws.com",
    "port":     5432,
    "user":     "postgres",
    "password": "NextGen2026!SafeDB#Specialty",   # ⚠️ Change after testing
    "database": "postgres"
}

@st.cache_resource
def get_conn():
    return psycopg2.connect(**DB)

def query(sql, params=None):
    try:
        conn = get_conn()
        return pd.read_sql_query(sql, conn, params=params)
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def scalar(sql, params=None, default=0):
    """Return the first cell of a single-row query, or default if DB is unreachable."""
    df = query(sql, params=params)
    return df.iloc[0, 0] if not df.empty else default

# ── Sidebar navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    logo_html = get_logo_html()
    if logo_html:
        st.markdown(logo_html, unsafe_allow_html=True)
    st.markdown("## ⚡ ELEVNOVA ERP")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["🏠 Dashboard", "📦 Inventory", "🔴 HSE", "🔑 Control of Work", "🚚 Procurement"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown(f"**Company:** QuimTejo Lda")
    st.markdown(f"**Date:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.markdown("---")
    if st.button("🔄 Refresh Data"):
        st.cache_resource.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.title("🏠 Operations Dashboard")
    st.markdown("**QuimTejo Lda** — Alverca do Ribatejo, Portugal | Real-time overview")
    st.markdown("---")

    # KPI cards
    col1, col2, col3, col4, col5 = st.columns(5)

    total_items    = scalar("SELECT COUNT(*) as n FROM items")
    critical_stock = scalar("""
        SELECT COUNT(*) as n FROM inventory inv
        JOIN items i ON inv.item_id=i.id
        WHERE inv.quantity < i.min_stock
    """)
    open_incidents = scalar("SELECT COUNT(*) as n FROM hse_incidents WHERE status='OPEN'")
    active_permits = scalar("SELECT COUNT(*) as n FROM permits WHERE status='ACTIVE'")
    pending_permits= scalar("SELECT COUNT(*) as n FROM permits WHERE status='PENDING'")

    col1.metric("📦 Total Materials", int(total_items))
    col2.metric("🔴 Critical Stock", int(critical_stock), delta=f"-{int(critical_stock)} alerts", delta_color="inverse")
    col3.metric("⚠️ Open Incidents", int(open_incidents), delta="Needs action" if open_incidents > 0 else "All clear", delta_color="inverse" if open_incidents > 0 else "normal")
    col4.metric("🔑 Active Permits", int(active_permits))
    col5.metric("⏳ Pending Approval", int(pending_permits), delta="Waiting" if pending_permits > 0 else "None", delta_color="inverse" if pending_permits > 0 else "normal")

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🔴 Stock Alerts")
        alerts = query("""
            SELECT i.name AS Material, inv.quantity AS "Stock Atual",
                   i.min_stock AS "Mínimo", i.uom AS "Un.",
                   ROUND(((i.min_stock - inv.quantity) / NULLIF(i.min_stock,0)) * 100, 0) AS "Deficit %"
            FROM inventory inv JOIN items i ON inv.item_id=i.id
            WHERE inv.quantity < i.min_stock
            ORDER BY (i.min_stock - inv.quantity) DESC
        """)
        if alerts.empty:
            st.success("✅ All stock levels are within limits.")
        else:
            st.dataframe(alerts, use_container_width=True, hide_index=True)

        st.subheader("⚠️ Open HSE Incidents")
        open_hse = query("""
            SELECT h.incident_date::text AS "Data", h.incident_type AS "Tipo",
                   h.severity AS "Severidade", h.reporter AS "Reportado por",
                   LEFT(h.description, 60) AS "Descrição"
            FROM hse_incidents h WHERE h.status = 'OPEN'
            ORDER BY CASE h.severity WHEN 'MUITO ALTO' THEN 0 WHEN 'ALTO' THEN 1 ELSE 2 END
        """)
        if open_hse.empty:
            st.success("✅ No open incidents.")
        else:
            st.dataframe(open_hse, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("🔑 Permits Needing Attention")
        permits_alert = query("""
            SELECT permit_number AS "Licença", permit_type AS "Tipo",
                   status AS "Estado", risk_level AS "Risco",
                   COALESCE(approver, '⏳ Pendente') AS "Aprovador",
                   LEFT(description, 50) AS "Trabalho"
            FROM permits WHERE status IN ('ACTIVE','PENDING')
            ORDER BY CASE status WHEN 'ACTIVE' THEN 0 ELSE 1 END
        """)
        if permits_alert.empty:
            st.success("✅ No active or pending permits.")
        else:
            st.dataframe(permits_alert, use_container_width=True, hide_index=True)

        st.subheader("🚨 High Risk Areas")
        risks = query("""
            SELECT area AS "Área", LEFT(hazard,45) AS "Perigo",
                   risk_score AS "Risco",
                   CASE WHEN risk_score>=15 THEN '🔴 CRÍTICO'
                        WHEN risk_score>=10 THEN '🟠 ALTO'
                        ELSE '🟡 MÉDIO' END AS "Nível"
            FROM risk_assessments
            WHERE risk_score >= 10
            ORDER BY risk_score DESC
        """)
        if risks.empty:
            st.success("✅ No critical risks.")
        else:
            st.dataframe(risks, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: INVENTORY
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📦 Inventory":
    st.title("📦 Inventory & Warehouse Management")
    st.markdown("---")

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        show_critical = st.checkbox("Show critical stock only", value=False)
    with col_f2:
        dg_only = st.checkbox("Show Dangerous Goods only", value=False)

    base_sql = """
        SELECT i.code AS "Código", i.name AS "Material",
               COALESCE(i.dg_class,'—') AS "Classe DG",
               COALESCE(i.un_number,'—') AS "Nº UN",
               w.name AS "Armazém", w.type AS "Tipo Armazém",
               inv.quantity AS "Stock Atual",
               i.min_stock AS "Mínimo", i.max_stock AS "Máximo",
               i.uom AS "Un.",
               ROUND((inv.quantity/NULLIF(i.max_stock,0))*100,1) AS "% Cap.",
               CASE WHEN inv.quantity < i.min_stock THEN '🔴 CRÍTICO'
                    ELSE '🟢 OK' END AS "Estado"
        FROM inventory inv
        JOIN items i ON inv.item_id=i.id
        JOIN warehouses w ON inv.warehouse_id=w.id
    """
    conditions = []
    if show_critical:
        conditions.append("inv.quantity < i.min_stock")
    if dg_only:
        conditions.append("i.dg_class IS NOT NULL")
    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)
    base_sql += " ORDER BY CASE WHEN inv.quantity < i.min_stock THEN 0 ELSE 1 END, i.code"

    df_inv = query(base_sql)

    total_val = scalar("""
        SELECT ROUND(SUM(inv.quantity * i.unit_price),2) AS val
        FROM inventory inv JOIN items i ON inv.item_id=i.id
    """, default=0) or 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Materials in Stock", len(df_inv))
    c2.metric("Critical Alerts", int(df_inv[df_inv["Estado"]=="🔴 CRÍTICO"].shape[0]))
    c3.metric("Estimated Stock Value", f"€{float(total_val):,.2f}")

    st.markdown("---")
    st.dataframe(df_inv, use_container_width=True, hide_index=True, height=400)

    # DG Compliance section
    st.markdown("---")
    st.subheader("🧪 Dangerous Goods Compliance Check")
    dg_df = query("""
        SELECT i.name AS "Material", i.dg_class AS "Classe DG",
               i.un_number AS "Nº UN", i.packing_group AS "Grupo Emb.",
               w.name AS "Armazém", w.type AS "Tipo Armazém",
               CASE WHEN w.type='Dangerous Goods' THEN '✅ Correto'
                    WHEN i.dg_class IS NULL THEN '— Não DG'
                    ELSE '🔴 VIOLAÇÃO' END AS "Conformidade DG"
        FROM inventory inv
        JOIN items i ON inv.item_id=i.id
        JOIN warehouses w ON inv.warehouse_id=w.id
        WHERE i.dg_class IS NOT NULL
        ORDER BY i.dg_class
    """)
    st.dataframe(dg_df, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: HSE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🔴 HSE":
    st.title("🔴 HSE Management")
    st.caption("Referência: ACT — Autoridade para as Condições do Trabalho | Lei n.º 102/2009")
    st.markdown("---")

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    total_inc  = scalar("SELECT COUNT(*) as n FROM hse_incidents")
    open_inc   = scalar("SELECT COUNT(*) as n FROM hse_incidents WHERE status='OPEN'")
    high_inc   = scalar("SELECT COUNT(*) as n FROM hse_incidents WHERE severity IN ('ALTO','MUITO ALTO')")
    closed_inc = scalar("SELECT COUNT(*) as n FROM hse_incidents WHERE status='CLOSED'")
    c1.metric("Total Incidents", int(total_inc))
    c2.metric("Open", int(open_inc), delta="Action needed" if open_inc>0 else None, delta_color="inverse")
    c3.metric("High Severity", int(high_inc))
    c4.metric("Closed", int(closed_inc))

    st.markdown("---")
    tab1, tab2 = st.tabs(["📋 Incident Register", "⚠️ Risk Assessments"])

    with tab1:
        status_filter = st.selectbox("Filter by status", ["All", "OPEN", "CLOSED", "INVESTIGATING"])
        sql = """
            SELECT h.id AS "ID", h.incident_date::text AS "Data",
                   h.incident_type AS "Tipo", h.severity AS "Severidade",
                   COALESCE(w.name,'—') AS "Local", h.reporter AS "Reportado por",
                   h.status AS "Estado",
                   LEFT(h.description,70) AS "Descrição",
                   COALESCE(h.corrective_action,'Pendente') AS "Ação Corretiva"
            FROM hse_incidents h LEFT JOIN warehouses w ON h.warehouse_id=w.id
        """
        if status_filter != "All":
            sql += f" WHERE h.status='{status_filter}'"
        sql += " ORDER BY CASE h.severity WHEN 'MUITO ALTO' THEN 0 WHEN 'ALTO' THEN 1 WHEN 'MÉDIO' THEN 2 ELSE 3 END"
        df_inc = query(sql)
        st.dataframe(df_inc, use_container_width=True, hide_index=True, height=350)

    with tab2:
        df_risk = query("""
            SELECT area AS "Área", hazard AS "Perigo",
                   likelihood AS "Probabilidade (1-5)",
                   severity_score AS "Gravidade (1-5)",
                   risk_score AS "Score de Risco",
                   CASE WHEN risk_score>=15 THEN '🔴 CRÍTICO'
                        WHEN risk_score>=10 THEN '🟠 ALTO'
                        WHEN risk_score>=6  THEN '🟡 MÉDIO'
                        ELSE '🟢 BAIXO' END AS "Nível de Risco",
                   control_measures AS "Medidas de Controlo",
                   next_review::text AS "Próxima Revisão"
            FROM risk_assessments ORDER BY risk_score DESC
        """)
        st.dataframe(df_risk, use_container_width=True, hide_index=True)
        st.info("📋 Risk Score = Probability × Severity | Critical ≥15 | High ≥10 | Medium ≥6")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: CONTROL OF WORK
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🔑 Control of Work":
    st.title("🔑 Control of Work — Permit Register")
    st.markdown("**Digital Permit-to-Work System** — The module no other ERP has natively.")
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    total_p   = scalar("SELECT COUNT(*) as n FROM permits")
    active_p  = scalar("SELECT COUNT(*) as n FROM permits WHERE status='ACTIVE'")
    pending_p = scalar("SELECT COUNT(*) as n FROM permits WHERE status='PENDING'")
    loto_p    = scalar("SELECT COUNT(*) as n FROM permits WHERE isolation_required=true AND status!='CLOSED'")
    c1.metric("Total Permits", int(total_p))
    c2.metric("🟢 Active", int(active_p))
    c3.metric("⏳ Pending Approval", int(pending_p), delta="Waiting" if pending_p>0 else None, delta_color="inverse")
    c4.metric("🔒 Require LOTO", int(loto_p))

    st.markdown("---")
    df_permits = query("""
        SELECT permit_number AS "Nº Licença",
               permit_type AS "Tipo de Trabalho",
               area AS "Área",
               requestor AS "Solicitante",
               COALESCE(approver,'⏳ Pendente') AS "Aprovador",
               status AS "Estado",
               risk_level AS "Nível de Risco",
               start_date::text AS "Data",
               CASE isolation_required WHEN true THEN '🔒 LOTO Obrigatório' ELSE '— Não requerido' END AS "Isolamento",
               LEFT(description,60) AS "Descrição do Trabalho",
               LEFT(COALESCE(notes,'—'),50) AS "Notas"
        FROM permits
        ORDER BY CASE status WHEN 'ACTIVE' THEN 0 WHEN 'PENDING' THEN 1 ELSE 2 END,
                 CASE risk_level WHEN 'MUITO ALTO' THEN 0 WHEN 'ALTO' THEN 1 ELSE 2 END
    """)
    st.dataframe(df_permits, use_container_width=True, hide_index=True, height=350)

    if int(pending_p) > 0:
        st.warning(f"⚠️ {int(pending_p)} permit(s) awaiting approval — no work should start until approved.")
    if int(loto_p) > 0:
        st.error(f"🔒 {int(loto_p)} active/pending permit(s) require energy isolation (LOTO). Verify before authorising.")

    st.markdown("---")
    st.info("💡 **ELEVNOVA Advantage:** This permit register is live-linked to your inventory and HSE modules. Any incident during an active permit is automatically associated. Conflict detection between overlapping permits — coming in next version.")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PROCUREMENT
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🚚 Procurement":
    st.title("🚚 Procurement & Suppliers")
    st.markdown("---")

    tab1, tab2 = st.tabs(["📋 Purchase Orders", "🏢 Suppliers"])

    with tab1:
        df_po = query("""
            SELECT po.id AS "PO #",
                   s.name AS "Fornecedor",
                   po.status AS "Estado",
                   po.order_date::text AS "Data Encomenda",
                   po.expected_date::text AS "Data Esperada",
                   po.total_value AS "Valor (€)",
                   i.name AS "Material",
                   pol.quantity AS "Qtd.",
                   pol.received_qty AS "Recebido",
                   i.uom AS "Un.",
                   LEFT(COALESCE(po.notes,'—'),55) AS "Notas"
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id=s.id
            JOIN po_lines pol ON pol.po_id=po.id
            JOIN items i ON pol.item_id=i.id
            ORDER BY CASE po.status WHEN 'CONFIRMED' THEN 0 WHEN 'DRAFT' THEN 1 ELSE 2 END
        """)
        total_open = df_po[df_po["Estado"].isin(["CONFIRMED","DRAFT"])]["Valor (€)"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Open Purchase Orders", len(df_po[df_po["Estado"].isin(["CONFIRMED","DRAFT"])]))
        c2.metric("Total Value Open POs", f"€{float(total_open):,.2f}")
        st.dataframe(df_po, use_container_width=True, hide_index=True)
        st.warning("⚠️ Urgent: 5,000 KG Hidróxido de Sódio on order — critical stockout. Expected 16/05/2026.")

    with tab2:
        df_sup = query("""
            SELECT s.name AS "Fornecedor", s.country AS "País",
                   s.rating AS "Rating (/5)",
                   s.payment_terms AS "Prazo (dias)",
                   s.contact_email AS "Email",
                   COUNT(po.id) AS "Encomendas Totais"
            FROM suppliers s
            LEFT JOIN purchase_orders po ON po.supplier_id=s.id
            GROUP BY s.id ORDER BY s.rating DESC
        """)
        st.dataframe(df_sup, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# Footer
st.markdown("---")
st.caption("⚡ ELEVNOVA ERP v0.1 — Elevate to the Next Standard | © 2026 Bravery & Perfection Lda | Powered by AWS RDS eu-north-1")
