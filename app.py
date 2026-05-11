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
try:
    import google.generativeai as _genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

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

def execute(sql, params=None):
    """Execute a write query (INSERT / UPDATE / DELETE). Returns True on success."""
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False

# ── AI Layer ──────────────────────────────────────────────────────────────────
DB_SCHEMA = """
PostgreSQL database — ELEVNOVA ERP (specialty chemicals, Portugal).
Tables:
- items(id, code, name, uom, dg_class, un_number, packing_group, min_stock, max_stock, unit_price)
- inventory(id, item_id, warehouse_id, quantity, last_updated)
- warehouses(id, name, type, location)
- stock_movements(id, item_id, warehouse_id, movement_type[IN/OUT/ADJ], quantity, reference, movement_date)
- suppliers(id, name, country, rating, payment_terms, contact_email)
- purchase_orders(id, supplier_id, status[DRAFT/CONFIRMED/RECEIVED], order_date, expected_date, total_value, notes)
- po_lines(id, po_id, item_id, quantity, unit_price, received_qty)
- hse_incidents(id, incident_date, incident_type, severity[BAIXO/MÉDIO/ALTO/MUITO ALTO], reporter, warehouse_id, description, corrective_action, status[OPEN/INVESTIGATING/CLOSED])
- risk_assessments(id, area, hazard, likelihood, severity_score, risk_score, control_measures, next_review)
- permits(id, permit_number, permit_type, area, requestor, approver, status[PENDING/ACTIVE/CLOSED], risk_level, start_date, isolation_required, description, notes)
"""

@st.cache_resource
def get_ai():
    if not GENAI_AVAILABLE:
        return None
    key = ""
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        pass
    if not key:
        key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return None
    _genai.configure(api_key=key)
    return _genai.GenerativeModel("gemini-2.0-flash")

def ai_call(system, user_msg, max_tokens=600):
    """Generic Gemini call — returns text or None."""
    model = get_ai()
    if not model:
        return None
    try:
        prompt = f"{system}\n\n{user_msg}"
        response = model.generate_content(
            prompt,
            generation_config=_genai.GenerationConfig(max_output_tokens=max_tokens)
        )
        return response.text.strip()
    except Exception as e:
        st.error(f"AI error: {e}")
        return None

def nl_to_sql(question):
    """Convert natural language to safe read-only SQL. Returns (sql, error)."""
    system = f"""You are a PostgreSQL expert for ELEVNOVA ERP.
Convert the user's question into a safe read-only SELECT query.
{DB_SCHEMA}
Rules:
- Return ONLY the raw SQL query — no markdown, no backticks, no explanation
- Only SELECT statements (never INSERT/UPDATE/DELETE)
- Always add LIMIT 100
- Use JOINs when needed for readable output
- If unclear, make a reasonable best-guess query"""
    sql = ai_call(system, question, max_tokens=400)
    if not sql:
        return None, "AI not configured or unavailable."
    sql = sql.strip().strip("`").strip()
    if not sql.upper().lstrip().startswith("SELECT"):
        return None, "AI returned an unsafe query. Try rephrasing."
    return sql, None

def ai_dashboard_insights(summary):
    """Return 4 bullet-point operational insights from current data."""
    system = """You are ELEVNOVA ERP's AI Operations Analyst for QuimTejo Lda, a specialty chemicals company in Portugal.
Analyse the operational data and return exactly 4 short, specific, actionable insights.
Format: one insight per line, start each with a relevant emoji (🔴 🟠 🟡 🟢 📦 ⚠️ etc).
Be specific with numbers. Focus on risks, urgent items, and opportunities. Max 2 sentences each. No intro or outro text."""
    return ai_call(system, f"Current operational data:\n{summary}", max_tokens=350)

# ── Sidebar navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    logo_html = get_logo_html()
    if logo_html:
        st.markdown(logo_html, unsafe_allow_html=True)
    st.markdown("## ⚡ ELEVNOVA ERP")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["🏠 Dashboard", "📦 Inventory", "🔴 HSE", "🔑 Control of Work", "🚚 Procurement", "🤖 AI Assistant"],
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

    # ── AI Insights panel ──────────────────────────────────────
    st.markdown("---")
    ai_col, _ = st.columns([3, 1])
    with ai_col:
        st.subheader("🤖 ELEVNOVA AI — Operational Insights")
    with _:
        run_ai = st.button("✨ Generate Insights", use_container_width=True)

    if run_ai or st.session_state.get("ai_insights_cache"):
        if run_ai:
            # Gather live data summary
            inv_summary = query("""
                SELECT i.name, inv.quantity, i.min_stock, i.uom
                FROM inventory inv JOIN items i ON inv.item_id=i.id
                ORDER BY inv.quantity/NULLIF(i.min_stock,0) ASC LIMIT 10
            """).to_string(index=False)
            inc_summary = query("""
                SELECT incident_type, severity, status, incident_date::text
                FROM hse_incidents ORDER BY incident_date DESC LIMIT 5
            """).to_string(index=False)
            permit_summary = query("""
                SELECT permit_type, area, status, risk_level, isolation_required
                FROM permits WHERE status IN ('ACTIVE','PENDING')
            """).to_string(index=False)
            po_summary = query("""
                SELECT s.name as supplier, po.status, po.expected_date::text, pol.quantity, i.name as material
                FROM purchase_orders po JOIN suppliers s ON po.supplier_id=s.id
                JOIN po_lines pol ON pol.po_id=po.id JOIN items i ON pol.item_id=i.id
                WHERE po.status IN ('DRAFT','CONFIRMED')
            """).to_string(index=False)

            data_summary = f"""
INVENTORY (lowest stock levels):
{inv_summary}

RECENT HSE INCIDENTS:
{inc_summary}

ACTIVE/PENDING PERMITS:
{permit_summary}

OPEN PURCHASE ORDERS:
{po_summary}
"""
            with st.spinner("Analysing your operations..."):
                insights = ai_dashboard_insights(data_summary)
            if insights:
                st.session_state["ai_insights_cache"] = insights
        else:
            insights = st.session_state.get("ai_insights_cache", "")

        if insights:
            for line in insights.strip().split("\n"):
                if line.strip():
                    st.info(line.strip())
        elif get_ai() is None:
            st.warning("⚠️ AI not configured. Add your ANTHROPIC_API_KEY to Streamlit secrets to enable AI insights.")
    else:
        st.caption("Click **✨ Generate Insights** to get AI-powered analysis of your current operations.")

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

    # ── Stock Movement Form ─────────────────────────────────────
    st.markdown("---")
    with st.expander("➕ Record Stock Movement (Receive / Issue)", expanded=False):
        items_df = query("SELECT id, code, name, uom FROM items ORDER BY code")
        wh_df2   = query("SELECT id, name FROM warehouses ORDER BY name")
        if not items_df.empty and not wh_df2.empty:
            item_labels = [f"{r['code']} — {r['name']} ({r['uom']})" for _, r in items_df.iterrows()]
            item_ids    = items_df["id"].tolist()
            wh_labels   = wh_df2["name"].tolist()
            wh_ids      = wh_df2["id"].tolist()

            with st.form("form_stock_movement", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    sel_item  = st.selectbox("Material *", item_labels)
                    sel_item_id = item_ids[item_labels.index(sel_item)]
                with c2:
                    sel_wh   = st.selectbox("Warehouse *", wh_labels)
                    sel_wh_id = wh_ids[wh_labels.index(sel_wh)]
                with c3:
                    mv_type  = st.selectbox("Movement Type", ["IN — Goods Receipt", "OUT — Issue / Consumption", "ADJ — Adjustment"])
                qty      = st.number_input("Quantity *", min_value=0.01, step=0.5, format="%.2f")
                ref      = st.text_input("Reference (PO number, batch, reason)", placeholder="e.g. PO-2026-001 or Manual adjustment")
                mv_submit= st.form_submit_button("📦 Record Movement", use_container_width=True)

            if mv_submit:
                mv_code = mv_type.split(" — ")[0]  # "IN", "OUT", or "ADJ"
                actual_qty = qty if mv_code == "IN" else -qty
                # Insert stock movement
                ok1 = execute("""
                    INSERT INTO stock_movements (item_id, warehouse_id, movement_type, quantity, reference, movement_date)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (sel_item_id, sel_wh_id, mv_code, qty, ref.strip() or None))
                # Update inventory balance
                ok2 = execute("""
                    UPDATE inventory SET quantity = quantity + %s
                    WHERE item_id=%s AND warehouse_id=%s
                """, (actual_qty, sel_item_id, sel_wh_id)) if ok1 else False
                if ok1 and ok2:
                    st.success(f"✅ Movement recorded — {mv_code} {qty:.2f} units. Inventory updated.")
                    st.cache_resource.clear()
                    st.rerun()
                elif ok1:
                    st.warning("Movement logged but inventory record not found. Check item/warehouse combination.")

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
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Incident Register", "⚠️ Risk Assessments", "➕ Log New Incident", "✏️ Update Incident"])

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

    with tab3:
        st.subheader("Log a New HSE Incident")
        wh_df = query("SELECT id, name FROM warehouses ORDER BY name")
        wh_options = ["(No specific location)"] + wh_df["name"].tolist() if not wh_df.empty else ["(No specific location)"]
        wh_id_map  = dict(zip(wh_df["name"].tolist(), wh_df["id"].tolist())) if not wh_df.empty else {}

        with st.form("form_new_incident", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                inc_date  = st.date_input("Incident Date", value=datetime.today().date())
                inc_type  = st.selectbox("Incident Type", [
                    "Near Miss", "First Aid", "Medical Treatment",
                    "Lost Time Injury", "Environmental Spill",
                    "Property Damage", "Fire", "Chemical Exposure", "Other"
                ])
                severity  = st.selectbox("Severity", ["BAIXO", "MÉDIO", "ALTO", "MUITO ALTO"])
            with c2:
                reporter  = st.text_input("Reported by *", placeholder="Full name")
                location  = st.selectbox("Location / Warehouse", wh_options)
                inc_status= st.selectbox("Initial Status", ["OPEN", "INVESTIGATING"])
            description  = st.text_area("Description of what happened *", height=110, placeholder="Describe the incident clearly...")
            corrective   = st.text_area("Immediate corrective action taken (if any)", height=80, placeholder="Leave blank if none yet.")
            submitted = st.form_submit_button("📝 Submit Incident Report", use_container_width=True)

        if submitted:
            if not reporter.strip() or not description.strip():
                st.error("Reporter name and description are required.")
            else:
                wh_id = wh_id_map.get(location)
                ok = execute("""
                    INSERT INTO hse_incidents
                        (incident_date, incident_type, severity, reporter,
                         warehouse_id, description, corrective_action, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (inc_date, inc_type, severity, reporter.strip(),
                      wh_id, description.strip(), corrective.strip() or None, inc_status))
                if ok:
                    st.success(f"✅ Incident logged successfully! Dashboard counters will update on next refresh.")
                    st.cache_resource.clear()
                    st.rerun()

    with tab4:
        st.subheader("Update an Existing Incident")
        incidents_df = query("SELECT id, incident_date::text, incident_type, severity, status FROM hse_incidents ORDER BY id DESC")
        if incidents_df.empty:
            st.info("No incidents found.")
        else:
            inc_labels = [f"ID {r['id']} — {r['incident_date']} | {r['incident_type']} | {r['severity']} | {r['status']}"
                          for _, r in incidents_df.iterrows()]
            inc_ids    = incidents_df["id"].tolist()
            selected   = st.selectbox("Select incident to update", inc_labels)
            sel_id     = inc_ids[inc_labels.index(selected)]

            with st.form("form_update_incident"):
                new_status     = st.selectbox("New Status", ["OPEN", "INVESTIGATING", "CLOSED"])
                corrective_upd = st.text_area("Corrective Action / Investigation Notes", height=100,
                                              placeholder="Describe actions taken, root cause, outcome...")
                upd_submitted = st.form_submit_button("💾 Save Update", use_container_width=True)

            if upd_submitted:
                ok = execute("""
                    UPDATE hse_incidents
                    SET status=%s, corrective_action=%s
                    WHERE id=%s
                """, (new_status, corrective_upd.strip() or None, sel_id))
                if ok:
                    st.success(f"✅ Incident #{sel_id} updated to {new_status}.")
                    st.cache_resource.clear()
                    st.rerun()

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

    col_form1, col_form2 = st.columns(2)

    # ── NEW PERMIT FORM ─────────────────────────────────────────
    with col_form1:
        with st.expander("➕ Request New Work Permit", expanded=False):
            with st.form("form_new_permit", clear_on_submit=True):
                permit_type = st.selectbox("Type of Work", [
                    "Hot Work", "Cold Work", "Confined Space Entry",
                    "Electrical Work", "Working at Height",
                    "Chemical Handling", "Excavation", "General Maintenance"
                ])
                area       = st.text_input("Work Area / Location *", placeholder="e.g. Tank Farm A, Reactor Zone 3")
                requestor  = st.text_input("Requested by *", placeholder="Full name + role")
                risk_level = st.selectbox("Risk Level", ["BAIXO", "MÉDIO", "ALTO", "MUITO ALTO"])
                start_date = st.date_input("Planned Start Date", value=datetime.today().date())
                isolation  = st.checkbox("🔒 Energy Isolation (LOTO) required?")
                description= st.text_area("Work Description *", height=90, placeholder="Describe the work to be performed...")
                notes      = st.text_area("Additional Safety Notes", height=70, placeholder="PPE, precautions, hazards to control...")
                p_submit   = st.form_submit_button("📋 Submit Permit Request", use_container_width=True)

            if p_submit:
                if not area.strip() or not requestor.strip() or not description.strip():
                    st.error("Area, requestor, and description are required.")
                else:
                    # Auto-generate permit number: PTW-YYYYMMDD-XXX
                    last_id = scalar("SELECT COALESCE(MAX(id),0) FROM permits") or 0
                    permit_no = f"PTW-{datetime.today().strftime('%Y%m%d')}-{int(last_id)+1:03d}"
                    ok = execute("""
                        INSERT INTO permits
                            (permit_number, permit_type, area, requestor, status,
                             risk_level, start_date, isolation_required, description, notes)
                        VALUES (%s, %s, %s, %s, 'PENDING', %s, %s, %s, %s, %s)
                    """, (permit_no, permit_type, area.strip(), requestor.strip(),
                          risk_level, start_date, isolation, description.strip(), notes.strip() or None))
                    if ok:
                        st.success(f"✅ Permit **{permit_no}** submitted — status: PENDING APPROVAL.")
                        st.cache_resource.clear()
                        st.rerun()

    # ── APPROVE / CLOSE PERMIT ───────────────────────────────────
    with col_form2:
        with st.expander("✅ Approve / Close a Permit", expanded=False):
            pending_df = query("SELECT id, permit_number, permit_type, area, status FROM permits WHERE status IN ('PENDING','ACTIVE') ORDER BY id DESC")
            if pending_df.empty:
                st.info("No pending or active permits to action.")
            else:
                p_labels = [f"{r['permit_number']} — {r['permit_type']} | {r['area']} | {r['status']}"
                            for _, r in pending_df.iterrows()]
                p_ids    = pending_df["id"].tolist()
                sel_p    = st.selectbox("Select permit", p_labels)
                sel_pid  = p_ids[p_labels.index(sel_p)]

                with st.form("form_approve_permit"):
                    action   = st.selectbox("Action", ["ACTIVE (Approve)", "CLOSED (Close / Cancel)"])
                    approver = st.text_input("Authorised by *", placeholder="Name + role")
                    p_notes  = st.text_area("Approval / Closure notes", height=80)
                    a_submit = st.form_submit_button("💾 Confirm Action", use_container_width=True)

                if a_submit:
                    if not approver.strip():
                        st.error("Authoriser name is required.")
                    else:
                        new_status = "ACTIVE" if "ACTIVE" in action else "CLOSED"
                        ok = execute("""
                            UPDATE permits
                            SET status=%s, approver=%s,
                                notes=COALESCE(NULLIF(%s,''), notes)
                            WHERE id=%s
                        """, (new_status, approver.strip(), p_notes.strip(), sel_pid))
                        if ok:
                            st.success(f"✅ Permit updated to **{new_status}**.")
                            st.cache_resource.clear()
                            st.rerun()

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

        st.markdown("---")
        with st.expander("➕ Create New Purchase Order", expanded=False):
            sup_df   = query("SELECT id, name, payment_terms FROM suppliers ORDER BY name")
            items_po = query("SELECT id, code, name, uom, unit_price FROM items ORDER BY code")
            if not sup_df.empty and not items_po.empty:
                sup_labels  = sup_df["name"].tolist()
                sup_ids     = sup_df["id"].tolist()
                item_labels = [f"{r['code']} — {r['name']} ({r['uom']})" for _, r in items_po.iterrows()]
                item_ids    = items_po["id"].tolist()
                unit_prices = items_po["unit_price"].tolist()

                with st.form("form_new_po", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        sel_sup   = st.selectbox("Supplier *", sup_labels)
                        sel_sup_id= sup_ids[sup_labels.index(sel_sup)]
                        order_date= st.date_input("Order Date", value=datetime.today().date())
                    with c2:
                        sel_item   = st.selectbox("Material *", item_labels)
                        sel_item_id= item_ids[item_labels.index(sel_item)]
                        sel_price  = unit_prices[item_ids.index(sel_item_id)]
                        exp_date   = st.date_input("Expected Delivery Date")
                    qty_po   = st.number_input("Quantity *", min_value=1.0, step=1.0, format="%.1f")
                    unit_price_override = st.number_input("Unit Price (€)", min_value=0.0,
                                                           value=float(sel_price) if sel_price else 0.0,
                                                           step=0.01, format="%.2f")
                    po_notes = st.text_area("Notes / Special Instructions", height=70)
                    po_status= st.selectbox("Status", ["DRAFT", "CONFIRMED"])
                    po_submit= st.form_submit_button("🚚 Create Purchase Order", use_container_width=True)

                if po_submit:
                    total_val = round(qty_po * unit_price_override, 2)
                    # Generate PO number
                    last_po = scalar("SELECT COALESCE(MAX(id),0) FROM purchase_orders") or 0
                    po_num  = f"PO-{datetime.today().strftime('%Y')}-{int(last_po)+1:04d}"
                    ok1 = execute("""
                        INSERT INTO purchase_orders
                            (supplier_id, status, order_date, expected_date, total_value, notes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (sel_sup_id, po_status, order_date, exp_date, total_val, po_notes.strip() or None))
                    if ok1:
                        # Get the new PO id
                        new_po_id = scalar("SELECT MAX(id) FROM purchase_orders")
                        ok2 = execute("""
                            INSERT INTO po_lines (po_id, item_id, quantity, unit_price, received_qty)
                            VALUES (%s, %s, %s, %s, 0)
                        """, (int(new_po_id), sel_item_id, qty_po, unit_price_override))
                        if ok2:
                            st.success(f"✅ Purchase Order **{po_num}** created — Total: €{total_val:,.2f} | Status: {po_status}")
                            st.cache_resource.clear()
                            st.rerun()

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
# PAGE: AI ASSISTANT
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🤖 AI Assistant":
    st.title("🤖 ELEVNOVA AI Assistant")
    st.markdown("Ask questions in plain language, get stock predictions, and let AI surface hidden risks.")
    st.markdown("---")

    if get_ai() is None:
        st.error("⚠️ AI not configured. Add `GEMINI_API_KEY` to your Streamlit secrets (see setup instructions below).")
        with st.expander("📋 How to add your API key"):
            st.markdown("""
1. Go to **https://aistudio.google.com/app/apikey** and create a free key
2. In Streamlit Cloud, open your app → **⋮ (3 dots)** → **Settings → Secrets**
3. Add this line:
```
GEMINI_API_KEY = "AIza..."
```
4. Click **Save** — the app will restart automatically
""")

    # ── SECTION 1: Natural Language Query ──────────────────────
    st.subheader("💬 Ask Anything About Your Operations")
    st.caption("Type a question in English or Portuguese — AI converts it to SQL and runs it live.")

    example_questions = [
        "Which materials are below minimum stock level?",
        "Show all open HSE incidents with high severity",
        "How many permits are pending approval?",
        "What is the total value of confirmed purchase orders?",
        "Show stock movements in the last 7 days",
        "Which supplier has the highest rating?"
    ]
    with st.expander("💡 Example questions"):
        for q in example_questions:
            st.markdown(f"• {q}")

    question = st.text_input("Your question:", placeholder='e.g. "Which materials will run out soon?"',
                              label_visibility="collapsed")
    ask_col, _ = st.columns([1, 4])
    with ask_col:
        ask_btn = st.button("🔍 Ask AI", use_container_width=True)

    if ask_btn and question.strip():
        with st.spinner("Converting to SQL and querying database..."):
            sql, err = nl_to_sql(question.strip())
        if err:
            st.error(err)
        else:
            with st.expander("🔎 Generated SQL", expanded=False):
                st.code(sql, language="sql")
            df_result = query(sql)
            if df_result.empty:
                st.info("No results found for that query.")
            else:
                st.success(f"✅ {len(df_result)} row(s) returned")
                st.dataframe(df_result, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── SECTION 2: Stock Prediction ─────────────────────────────
    st.subheader("📊 AI Stock Predictions — Days to Stockout")
    st.caption("Based on actual consumption from the last 30 days.")

    if st.button("🔮 Run Stock Prediction", use_container_width=False):
        pred_df = query("""
            WITH daily_usage AS (
                SELECT item_id, warehouse_id,
                       SUM(quantity) / GREATEST(COUNT(DISTINCT DATE(movement_date)), 1) AS daily_rate
                FROM stock_movements
                WHERE movement_type = 'OUT'
                  AND movement_date >= NOW() - INTERVAL '30 days'
                GROUP BY item_id, warehouse_id
            )
            SELECT
                i.code        AS "Code",
                i.name        AS "Material",
                i.uom         AS "Unit",
                inv.quantity  AS "Current Stock",
                i.min_stock   AS "Min Stock",
                ROUND(d.daily_rate::numeric, 2) AS "Daily Usage (avg)",
                CASE
                    WHEN d.daily_rate > 0
                    THEN FLOOR(inv.quantity / d.daily_rate)::int
                    ELSE NULL
                END AS "Days to Stockout",
                CASE
                    WHEN d.daily_rate > 0 AND FLOOR(inv.quantity / d.daily_rate) <= 7
                        THEN '🔴 CRITICAL — order NOW'
                    WHEN d.daily_rate > 0 AND FLOOR(inv.quantity / d.daily_rate) <= 14
                        THEN '🟠 LOW — order soon'
                    WHEN d.daily_rate > 0 AND FLOOR(inv.quantity / d.daily_rate) <= 30
                        THEN '🟡 MONITOR'
                    WHEN d.daily_rate > 0
                        THEN '🟢 OK'
                    ELSE '— No recent usage'
                END AS "AI Alert"
            FROM inventory inv
            JOIN items i ON inv.item_id = i.id
            LEFT JOIN daily_usage d ON d.item_id = inv.item_id AND d.warehouse_id = inv.warehouse_id
            ORDER BY
                CASE WHEN d.daily_rate > 0 THEN inv.quantity / d.daily_rate ELSE 999 END ASC
        """)
        if pred_df.empty:
            st.info("No stock movement data found for the last 30 days. Record some movements first.")
        else:
            st.dataframe(pred_df, use_container_width=True, hide_index=True, height=350)
            critical = pred_df[pred_df["AI Alert"].str.startswith("🔴", na=False)]
            if not critical.empty:
                st.error(f"🔴 {len(critical)} material(s) need immediate reorder!")
                # Ask AI to explain
                if get_ai():
                    with st.spinner("Generating AI reorder recommendations..."):
                        rec = ai_call(
                            "You are a supply chain expert. Give concise reorder recommendations.",
                            f"Critical stock items:\n{critical.to_string(index=False)}\n\nGive 1-2 sentence action for each item.",
                            max_tokens=300
                        )
                    if rec:
                        st.warning(f"**AI Recommendations:**\n\n{rec}")

    st.markdown("---")

    # ── SECTION 3: HSE Risk Analyser ────────────────────────────
    st.subheader("⚠️ AI HSE Risk Analyser")
    st.caption("AI reviews your active permits and open incidents and flags conflicts or escalating risks.")

    if st.button("🔍 Analyse Current HSE Risk", use_container_width=False):
        permits_data = query("""
            SELECT permit_type, area, status, risk_level, isolation_required, description
            FROM permits WHERE status IN ('ACTIVE','PENDING')
        """)
        incidents_data = query("""
            SELECT incident_type, severity, status, description, incident_date::text
            FROM hse_incidents WHERE status IN ('OPEN','INVESTIGATING')
            ORDER BY incident_date DESC LIMIT 10
        """)
        risks_data = query("""
            SELECT area, hazard, risk_score, control_measures
            FROM risk_assessments WHERE risk_score >= 10
            ORDER BY risk_score DESC
        """)

        if permits_data.empty and incidents_data.empty:
            st.info("No active permits or open incidents to analyse.")
        else:
            combined = f"""
ACTIVE/PENDING PERMITS:
{permits_data.to_string(index=False) if not permits_data.empty else 'None'}

OPEN/INVESTIGATING INCIDENTS:
{incidents_data.to_string(index=False) if not incidents_data.empty else 'None'}

HIGH RISK AREAS (score ≥10):
{risks_data.to_string(index=False) if not risks_data.empty else 'None'}
"""
            with st.spinner("Analysing HSE risk..."):
                analysis = ai_call(
                    """You are an HSE risk expert for a Portuguese specialty chemicals company.
Analyse the permits, incidents, and risk areas provided.
Identify: conflicts between simultaneous permits, escalating incident patterns, areas needing immediate attention.
Return 3-5 specific risk observations as bullet points with emojis. Be direct and specific.""",
                    combined, max_tokens=400
                )
            if analysis:
                for line in analysis.strip().split("\n"):
                    if line.strip():
                        st.warning(line.strip())
            else:
                st.info("AI not available — configure your API key to enable this feature.")

# ─────────────────────────────────────────────────────────────────────────────
# Footer
st.markdown("---")
st.caption("⚡ ELEVNOVA ERP v0.3 — Elevate to the Next Standard | © 2026 Bravery & Perfection Lda | Powered by AWS RDS eu-north-1 + Claude AI")
