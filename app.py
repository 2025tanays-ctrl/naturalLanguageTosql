"""
QueryCraft — Natural Language to SQL Query Assistant
Student: Tanay Siddharth Shelar | ID: 150096725092
"""

import os
import sys
from pathlib import Path

# ── Bootstrap: load .env and fix import path ─────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import json
from datetime import datetime

from src import database, validator, ai_generator, evaluator, storage, automation

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QueryCraft — AI SQL Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialise databases on first run ─────────────────────────────────────────
@st.cache_resource
def initialise():
    database.init_db()
    storage.init_storage()
    return True

initialise()

# ── Custom CSS: Premium Dark Cyberpunk / Developer Studio Aesthetic ─────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* Global Dark Background & Resets */
    .stApp {
        background: #090d16 !important;
        color: #f1f5f9 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    [data-testid="stSidebar"] {
        background-color: #0d1322 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    /* Keyframes */
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.5); }
        70% { box-shadow: 0 0 0 14px rgba(99, 102, 241, 0); }
        100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
    }

    @keyframes pulseEmerald {
        0% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.6); }
        70% { box-shadow: 0 0 0 10px rgba(52, 211, 153, 0); }
        100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Hero Banner: Deep Obsidian & Electric Indigo Mesh */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 60%, #172554 100%);
        border-radius: 18px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 1.8rem;
        color: #ffffff;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
        animation: fadeInUp 0.5s ease-out;
    }

    .hero-banner::before {
        content: "";
        position: absolute;
        top: -40%;
        right: -20%;
        width: 350px;
        height: 350px;
        background: radial-gradient(circle, rgba(129, 140, 248, 0.25) 0%, transparent 70%);
        pointer-events: none;
    }

    .hero-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(99, 102, 241, 0.25);
        border: 1px solid rgba(129, 140, 248, 0.4);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #c7d2fe;
        margin-bottom: 0.85rem;
    }

    .hero-title {
        font-size: 2.85rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1.1;
        margin: 0;
        background: linear-gradient(135deg, #ffffff 20%, #cbd5e1 55%, #93c5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        font-size: 1.02rem;
        color: #94a3b8;
        margin-top: 0.65rem;
        max-width: 760px;
        line-height: 1.55;
    }

    .hero-meta-strip {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 12px;
        margin-top: 1.4rem;
        padding-top: 1.2rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .hero-meta-badge {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(8px);
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        color: #e2e8f0;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .live-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #34d399;
        animation: pulseEmerald 2s infinite;
    }

    /* Tabs: Deep Night Segmented Bar */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0e1626 !important;
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        margin-bottom: 1.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.92rem;
        padding: 9px 20px;
        color: #94a3b8 !important;
        background-color: transparent !important;
        border: none !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #f1f5f9 !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #818cf8 !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3) !important;
    }

    /* Section Subheading */
    .section-header {
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .section-desc {
        font-size: 0.9rem;
        color: #94a3b8;
        margin-top: 0.3rem;
        margin-bottom: 1.2rem;
        line-height: 1.5;
    }

    /* Execution Audit ID Card (Dark Cyber Card) */
    .run-badge-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(15, 23, 42, 0.7) 100%);
        border: 1px solid rgba(52, 211, 153, 0.3);
        border-radius: 12px;
        padding: 0.95rem 1.4rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 1.2rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        animation: fadeInUp 0.4s ease-out;
    }

    .run-badge-id {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        color: #38bdf8;
        font-size: 1.05rem;
    }

    /* 5-Node Stepper (Dark Matrix) */
    .pipeline-container {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        background: #0e1626;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 14px;
        margin: 1.2rem 0 1.6rem 0;
        animation: fadeInUp 0.5s ease-out;
    }

    .stepper-node {
        background: #141d2e;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 10px;
        padding: 10px 12px;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        transition: all 0.25s ease;
    }

    .stepper-node.completed {
        border-color: rgba(52, 211, 153, 0.4);
        background: linear-gradient(to bottom, rgba(16, 185, 129, 0.12), #141d2e);
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.15);
    }

    .stepper-node.active {
        border-color: rgba(129, 140, 248, 0.6);
        background: linear-gradient(to bottom, rgba(99, 102, 241, 0.2), #141d2e);
        animation: pulseGlow 2.5s infinite;
    }

    .stepper-node.failed {
        border-color: rgba(239, 68, 68, 0.5);
        background: linear-gradient(to bottom, rgba(239, 68, 68, 0.15), #141d2e);
    }

    .node-header {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 4px;
    }

    .stepper-node.completed .node-header { color: #34d399; }
    .stepper-node.active .node-header { color: #818cf8; }
    .stepper-node.failed .node-header { color: #f87171; }

    .node-title {
        font-size: 0.88rem;
        font-weight: 700;
        color: #f1f5f9;
    }

    /* KPI Cards (Dark Surface) */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 1.5rem;
    }

    .kpi-card {
        background: #131b2e;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        border-color: rgba(255, 255, 255, 0.15);
    }

    .kpi-label {
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 0.04em;
    }

    .kpi-val {
        font-size: 1.85rem;
        font-weight: 800;
        color: #f8fafc;
        margin-top: 4px;
    }

    /* Pill Badges */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    .badge-success { background: rgba(16, 185, 129, 0.18); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.35); }
    .badge-error { background: rgba(239, 68, 68, 0.18); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.35); }
    .badge-warning { background: rgba(245, 158, 11, 0.18); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.35); }
    .badge-info { background: rgba(56, 189, 248, 0.18); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); }
    .badge-neutral { background: rgba(255, 255, 255, 0.07); color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.12); }

    /* Buttons: Electric Violet / Indigo Glow */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.92rem;
        padding: 0.52rem 1.25rem;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        border: 1px solid rgba(255, 255, 255, 0.12);
        background: #172036;
        color: #e2e8f0;
    }

    div.stButton > button:hover {
        background: #232f4c;
        border-color: rgba(255, 255, 255, 0.22);
        color: #ffffff;
        transform: translateY(-1px);
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #2563eb 100%) !important;
        border: 1px solid #6366f1 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 18px rgba(99, 102, 241, 0.45);
    }

    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(99, 102, 241, 0.65);
        background: linear-gradient(135deg, #4338ca 0%, #6d28d9 50%, #1d4ed8 100%) !important;
    }

    /* Sidebar Brand Card */
    .sidebar-brand-card {
        background: linear-gradient(135deg, #131b2e 0%, #0d1322 100%);
        border-radius: 14px;
        padding: 1.25rem;
        color: #ffffff;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }

    .schema-col-pill {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        margin: 3px 0;
        background: rgba(255, 255, 255, 0.05);
        color: #e2e8f0;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Streamlit Metric Box styling */
    [data-testid="stMetric"] {
        background: #131b2e !important;
        padding: 14px 18px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
    }

    [data-testid="stMetricLabel"] p {
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricValue"] div {
        color: #f8fafc !important;
        font-weight: 800 !important;
    }

    /* Callout & Alert Boxes (Dark Frosted) */
    .callout-box {
        border-radius: 10px;
        padding: 0.9rem 1.25rem;
        margin: 0.8rem 0;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        font-size: 0.9rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }

    .callout-box.info {
        background: rgba(14, 165, 233, 0.12);
        border-left: 4px solid #0284c7;
        color: #bae6fd;
        border-top: 1px solid rgba(14, 165, 233, 0.2);
        border-right: 1px solid rgba(14, 165, 233, 0.2);
        border-bottom: 1px solid rgba(14, 165, 233, 0.2);
    }

    .callout-box.warning {
        background: rgba(245, 158, 11, 0.12);
        border-left: 4px solid #f59e0b;
        color: #fde68a;
        border-top: 1px solid rgba(245, 158, 11, 0.2);
        border-right: 1px solid rgba(245, 158, 11, 0.2);
        border-bottom: 1px solid rgba(245, 158, 11, 0.2);
    }

    .callout-box.danger {
        background: rgba(239, 68, 68, 0.12);
        border-left: 4px solid #ef4444;
        color: #fca5a5;
        border-top: 1px solid rgba(239, 68, 68, 0.2);
        border-right: 1px solid rgba(239, 68, 68, 0.2);
        border-bottom: 1px solid rgba(239, 68, 68, 0.2);
    }

    .callout-box.success {
        background: rgba(16, 185, 129, 0.12);
        border-left: 4px solid #10b981;
        color: #a7f3d0;
        border-top: 1px solid rgba(16, 185, 129, 0.2);
        border-right: 1px solid rgba(16, 185, 129, 0.2);
        border-bottom: 1px solid rgba(16, 185, 129, 0.2);
    }

    /* Streamlit Expander Dark Theming */
    div[data-testid="stExpander"] {
        background: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        margin-bottom: 8px;
    }

    div[data-testid="stExpander"] summary {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }

    /* Inputs & Selectbox Dark overrides */
    div[data-baseweb="select"] > div {
        background-color: #111827 !important;
        border-color: rgba(255, 255, 255, 0.12) !important;
        color: #f1f5f9 !important;
    }

    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
        background-color: #111827 !important;
        color: #f8fafc !important;
        border-color: rgba(255, 255, 255, 0.12) !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar Configuration ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand-card">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
            <span style="font-size: 1.6rem;">⚡</span>
            <div>
                <div style="font-weight: 800; font-size: 1.15rem; letter-spacing: -0.02em; color: #ffffff;">QueryCraft</div>
                <div style="font-size: 0.72rem; color: #a5b4fc; text-transform: uppercase; font-weight: 700;">NL-to-SQL Studio · v2.4</div>
            </div>
        </div>
        <div style="font-size: 0.78rem; color: #94a3b8; line-height: 1.4; margin-top: 6px;">
            Academic AI Project by <strong>Tanay Siddharth Shelar</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### ⚙️ Pipeline Controls")

    PROMPT_VERSIONS = {
        "v1_basic":       "v1 — Basic (Zero-shot minimal)",
        "v2_structured":  "v2 — Structured (Schema + DDL rules)",
        "v3_refined":     "v3 — Refined (AST Safety + Ambiguity Guard)",
    }
    prompt_key = st.selectbox(
        "Prompt Template",
        list(PROMPT_VERSIONS.keys()),
        format_func=lambda k: PROMPT_VERSIONS[k],
        index=1,
        help="Select the prompting strategy used to instruct OpenAI models."
    )

    model_name = st.selectbox(
        "Inference Model",
        ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gpt-4o-mini"],
        index=0,
        help="Target AI model. Google Gemini provides generous free API quota via Google AI Studio.",
    )

    st.markdown("---")
    st.markdown("#### 🗄️ Database Inspector")
    try:
        schema = database.get_schema()
        # Calculate stats
        conn_stats = database.get_readonly_connection()
        c = conn_stats.cursor()
        c.execute("SELECT count(*) FROM employees")
        emp_count = c.fetchone()[0]
        c.execute("SELECT count(*) FROM departments")
        dept_count = c.fetchone()[0]
        conn_stats.close()

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Employees", emp_count)
        with col_s2:
            st.metric("Depts", dept_count)

        for table, columns in schema.items():
            with st.expander(f"📁 `{table}` ({len(columns)} cols)", expanded=False):
                for col in columns:
                    pk_badge = " 🔑" if col["pk"] else ""
                    nn_badge = " ★" if col["notnull"] else ""
                    st.markdown(
                        f"<div class='schema-col-pill'><b>{col['name']}</b>: <i>{col['type']}</i>{pk_badge}{nn_badge}</div>",
                        unsafe_allow_html=True
                    )
    except Exception as e:
        st.error(f"Schema load error: {e}")

    st.markdown("---")
    st.markdown("#### 🔑 Gemini API Configuration")
    gemini_env = os.getenv("GEMINI_API_KEY", "")
    gemini_input = st.text_input(
        "Google Gemini API Key",
        value=gemini_env,
        type="password",
        placeholder="AIzaSy...",
        help="Get your free key from https://aistudio.google.com/app/apikey",
    )
    if gemini_input:
        os.environ["GEMINI_API_KEY"] = gemini_input.strip()

    with st.expander("⚙️ Optional: OpenAI API Key", expanded=False):
        openai_env = os.getenv("OPENAI_API_KEY", "")
        openai_input = st.text_input(
            "OpenAI API Key",
            value=openai_env,
            type="password",
            placeholder="sk-proj-...",
        )
        if openai_input:
            os.environ["OPENAI_API_KEY"] = openai_input.strip()

    is_gemini_active = model_name.startswith("gemini")
    active_key_set = bool(os.environ.get("GEMINI_API_KEY")) if is_gemini_active else bool(os.environ.get("OPENAI_API_KEY"))

    if active_key_set:
        provider_name = "Google Gemini" if is_gemini_active else "OpenAI"
        st.markdown(f"""
        <div class="callout-box success">
            <span>🟢</span>
            <div><strong>{provider_name} Ready</strong><br><span style="font-size:0.75rem;">Model: <code>{model_name}</code></span></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        req_key = "GEMINI_API_KEY" if is_gemini_active else "OPENAI_API_KEY"
        st.markdown(f"""
        <div class="callout-box warning">
            <span>⚠️</span>
            <div><strong>No {req_key}</strong><br><span style="font-size:0.75rem;">Enter key above or in <code>.env</code>.<br><a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#60a5fa; text-decoration:underline;">Get free Gemini key ↗</a></span></div>
        </div>
        """, unsafe_allow_html=True)

# ── Hero Banner ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-banner">
    <div class="hero-pill">✨ Autonomous SQL Copilot & Evaluation Suite</div>
    <div class="hero-title">QueryCraft Studio</div>
    <div class="hero-subtitle">
        Translate natural language into secure, dialect-compliant SQLite queries with instant AST validation, read-only sandboxing, and automated reference scoring.
    </div>
    <div class="hero-meta-strip">
        <div class="hero-meta-badge">
            <span class="live-dot"></span>
            <strong>Engine:</strong> SQLite 3 (Live Sandbox)
        </div>
        <div class="hero-meta-badge">
            🛡️ <strong>AST Guard:</strong> sqlglot Transpiler
        </div>
        <div class="hero-meta-badge">
            👤 <strong>Author:</strong> Tanay Siddharth Shelar &nbsp;•&nbsp; <strong>ID:</strong> 150096725092
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Navigation Tabs ──────────────────────────────────────────────────────────
tab_query, tab_tests, tab_history, tab_compare = st.tabs([
    "💬 Query Studio", "🧪 Reference Benchmarks", "📜 Audit & History", "⚖️ Prompt Laboratory"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — QUERY STUDIO
# ══════════════════════════════════════════════════════════════════════════════
with tab_query:
    st.markdown("""
    <div class="section-header">
        <h3 class="section-title">💬 Natural Language Query Composer</h3>
        <div class="section-desc">Type your business question or click one of the quick test chips below to immediately inspect the generated SQL and sandbox results.</div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize query state
    if "user_query" not in st.session_state:
        st.session_state["user_query"] = "Show the five highest paid employees"

    # Quick prompt buttons
    st.markdown("**⚡ Quick Prompt Templates:**")
    quick_col1, quick_col2, quick_col3, quick_col4, quick_col5 = st.columns(5)

    with quick_col1:
        if st.button("👥 All Staff", use_container_width=True, help="Retrieve all employee records"):
            st.session_state["user_query"] = "Show all employees"
            st.rerun()

    with quick_col2:
        if st.button("💰 Top 5 Earners", use_container_width=True, help="Order by salary descending with limit 5"):
            st.session_state["user_query"] = "Show the five highest paid employees"
            st.rerun()

    with quick_col3:
        if st.button("📈 Salary > $80k", use_container_width=True, help="Filter employees earning over 80,000"):
            st.session_state["user_query"] = "Show employees with salary above 80000"
            st.rerun()

    with quick_col4:
        if st.button("🏢 Dept Count", use_container_width=True, help="Aggregate employees grouped by department"):
            st.session_state["user_query"] = "Count employees in each department"
            st.rerun()

    with quick_col5:
        if st.button("⚠️ Missing Col", use_container_width=True, help="Edge case: non-existent phone column"):
            st.session_state["user_query"] = "Show employee phone numbers"
            st.rerun()

    st.write("")
    question = st.text_area(
        "Natural Language Prompt",
        value=st.session_state.get("user_query", ""),
        height=95,
        placeholder='e.g. "List all employees in the Engineering department along with their email addresses"',
        help="Describe what data you want to retrieve in plain English."
    )

    btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1, 3.5])
    with btn_col1:
        generate_clicked = st.button("🚀 Generate & Execute", type="primary", use_container_width=True)
    with btn_col2:
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state["user_query"] = ""
            st.rerun()

    if generate_clicked:
        if not question.strip():
            st.markdown("""
            <div class="callout-box danger">
                <span>❌</span>
                <div><strong>Input Required:</strong> Please enter a question or click one of the quick prompt templates above.</div>
            </div>
            """, unsafe_allow_html=True)
        elif not active_key_set:
            missing_provider = "Google Gemini" if is_gemini_active else "OpenAI"
            key_var = "GEMINI_API_KEY" if is_gemini_active else "OPENAI_API_KEY"
            st.markdown(f"""
            <div class="callout-box warning">
                <span>⚠️</span>
                <div><strong>{missing_provider} API Key Required:</strong> Enter your key in the sidebar or set <code>{key_var}</code> in your <code>.env</code> file. (Get a free Gemini key at <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#60a5fa; text-decoration:underline;">aistudio.google.com</a>).<br>
                <i>You can also run all 5 database benchmarks in the <b>Reference Benchmarks</b> tab completely offline!</i></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.status("⚡ Orchestrating QueryCraft Multi-Stage Pipeline...", expanded=True) as workflow_status:
                st.write("🔍 **Stage 1/5:** Sanity check input prompt and pull current database catalog...")
                st.write(f"🤖 **Stage 2/5:** Dispatching system prompt to `{model_name}` using template `{prompt_key}`...")
                result = automation.run_workflow(
                    question=question,
                    prompt_version=prompt_key,
                    model=model_name,
                )
                stages = result.get("stages") or {}
                gen_data = stages.get("generation") or {}
                val_data = stages.get("validation") or {}
                exc_data = stages.get("execution") or {}
                val_ok = bool(val_data.get("valid", False))
                exc_ok = bool(exc_data.get("success", False))

                st.write(f"🛡️ **Stage 3/5:** SQL AST parsing via sqlglot ({'Passed ✅' if val_ok else 'Rejected ❌'})...")
                st.write(f"⚡ **Stage 4/5:** SQLite read-only sandbox execution ({'Success ✅' if exc_ok else 'Skipped/Halted ⚠️'})...")
                st.write("💾 **Stage 5/5:** Persisting run telemetry and audit logs into database...")
                workflow_status.update(label="✨ QueryCraft Pipeline Execution Complete!", state="complete", expanded=False)

            st.toast("⚡ Query successfully processed and saved to audit trail!", icon="🚀")

            # ── Run ID & Timestamp Strip ─────────────────────────────────────
            run_id = result.get("run_id", "N/A")
            st.markdown(f"""
            <div class="run-badge-card">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="live-dot"></span>
                    <div>
                        <span style="font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#38bdf8;">Execution Audit ID</span>
                        <div class="run-badge-id">{run_id}</div>
                    </div>
                </div>
                <div style="font-size: 0.85rem; color: #94a3b8; font-weight: 500;">
                    ⏱️ {datetime.now().strftime("%Y-%m-%d · %H:%M:%S")}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Visual Pipeline Stepper ───────────────────────────────────────
            step1_cls = "completed"
            step2_cls = "completed" if gen_data.get("success") else "failed"
            step3_cls = "completed" if val_ok else ("failed" if gen_data.get("success") else "")
            step4_cls = "completed" if exc_ok else ("failed" if val_ok else "")
            step5_cls = "completed"

            st.markdown(f"""
            <div class="pipeline-container">
                <div class="stepper-node {step1_cls}">
                    <div class="node-header"><span>✓</span> Stage 1</div>
                    <div class="node-title">Input Sanitized</div>
                </div>
                <div class="stepper-node {step2_cls}">
                    <div class="node-header"><span>{"✓" if gen_data.get('success') else "!"}</span> Stage 2</div>
                    <div class="node-title">AI Synthesis</div>
                </div>
                <div class="stepper-node {step3_cls}">
                    <div class="node-header"><span>{"✓" if val_ok else "!"}</span> Stage 3</div>
                    <div class="node-title">AST Validation</div>
                </div>
                <div class="stepper-node {step4_cls}">
                    <div class="node-header"><span>{"✓" if exc_ok else "!"}</span> Stage 4</div>
                    <div class="node-title">Sandbox Query</div>
                </div>
                <div class="stepper-node {step5_cls}">
                    <div class="node-header"><span>✓</span> Stage 5</div>
                    <div class="node-title">Audit Logged</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Split Results Layout ──────────────────────────────────────────
            res_left, res_right = st.columns([1.1, 0.9])

            with res_left:
                st.markdown("#### 🤖 Synthesized SQL & Token Usage")
                if gen_data.get("success"):
                    sql_code = gen_data.get("sql", "")
                    st.code(sql_code, language="sql")

                    # Download SQL button
                    st.download_button(
                        label="📥 Download SQL",
                        data=sql_code,
                        file_name=f"query_{run_id}.sql",
                        mime="text/plain",
                        key=f"dl_sql_{run_id}",
                    )

                    st.markdown(f"""
                    <div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:8px;">
                        <span class="badge-pill badge-neutral">Model: {gen_data.get('model')}</span>
                        <span class="badge-pill badge-info">Prompt Tokens: {gen_data.get('prompt_tokens', 'N/A')}</span>
                        <span class="badge-pill badge-info">Completion Tokens: {gen_data.get('completion_tokens', 'N/A')}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    if gen_data.get("raw_response"):
                        with st.expander("🔍 View Raw LLM Output"):
                            st.text(gen_data["raw_response"])
                else:
                    err_msg = gen_data.get('error', 'Unknown generation error')
                    st.markdown(f"""
                    <div class="callout-box danger">
                        <span>❌</span>
                        <div><strong>Generation Failed:</strong> {err_msg}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if "insufficient_quota" in err_msg or "credit_balance_exhausted" in err_msg:
                        st.markdown("""
                        <div class="callout-box warning">
                            <span>💳</span>
                            <div><strong>OpenAI Account Notice:</strong> Your OpenAI API key has 0 available billing credits. Add credits at <a href="https://platform.openai.com/settings/organization/billing" target="_blank" style="color:#60a5fa; text-decoration:underline;">platform.openai.com/billing</a>.<br>
                            <i>Note: You can still run all 5 database test cases in the <b>Reference Benchmarks</b> tab without OpenAI credits!</i></div>
                        </div>
                        """, unsafe_allow_html=True)

            with res_right:
                st.markdown("#### 🛡️ AST Safety & Guardrails")
                val_data = stages.get("validation", {})
                if val_data.get("valid"):
                    st.markdown("""
                    <div class="callout-box success">
                        <span>🛡️</span>
                        <div>
                            <strong>AST Verification Passed:</strong>
                            <div style="font-size:0.8rem; margin-top:4px;">
                                • Dialect: SQLite Verified<br>
                                • Permitted Statement: <code>SELECT</code> Only<br>
                                • Mutation Guards: No <code>DROP</code>, <code>DELETE</code>, or <code>UPDATE</code>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    for err in val_data.get("errors", []):
                        st.markdown(f"""
                        <div class="callout-box danger">
                            <span>🚫</span>
                            <div><strong>AST Guard Rejection:</strong> {err}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    for warn in val_data.get("warnings", []):
                        st.markdown(f"""
                        <div class="callout-box warning">
                            <span>⚠️</span>
                            <div><strong>AST Warning:</strong> {warn}</div>
                        </div>
                        """, unsafe_allow_html=True)

            # ── Execution Data Table ──────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### ⚡ Sandbox Execution Output")
            exc_data = stages.get("execution", {})

            if exc_data.get("success"):
                exec_data = exc_data.get("data", {})
                rows = exec_data.get("rows", [])
                columns = exec_data.get("columns", [])

                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("Rows Returned", len(rows))
                m_col2.metric("Columns", len(columns))
                m_col3.metric("Isolation Mode", "PRAGMA query_only")

                if rows:
                    df = pd.DataFrame(rows, columns=columns)
                    st.dataframe(df, use_container_width=True)

                    # Export CSV
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Export Results to CSV",
                        data=csv_data,
                        file_name=f"query_result_{run_id}.csv",
                        mime="text/csv",
                        key=f"dl_csv_{run_id}",
                    )
                else:
                    st.markdown("""
                    <div class="callout-box info">
                        <span>ℹ️</span>
                        <div>Query completed successfully with an empty result set (0 records).</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="callout-box danger">
                    <span>❌</span>
                    <div><strong>Execution Skipped or Failed:</strong> {exc_data.get('error', 'Execution halted by safety policy.')}</div>
                </div>
                """, unsafe_allow_html=True)

            # Evaluation if matched
            eval_res = stages.get("evaluation")
            if eval_res:
                st.markdown("---")
                if eval_res.get("passed"):
                    st.markdown(f"""
                    <div class="callout-box success">
                        <span>🏆</span>
                        <div><strong>Benchmark Evaluation Verified:</strong> {eval_res.get('reason')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="callout-box warning">
                        <span>⚠️</span>
                        <div><strong>Benchmark Evaluation Note:</strong> {eval_res.get('reason')}</div>
                    </div>
                    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — REFERENCE BENCHMARKS
# ══════════════════════════════════════════════════════════════════════════════
with tab_tests:
    st.markdown("""
    <div class="section-header">
        <h3 class="section-title">🧪 Reference Test Benchmarks</h3>
        <div class="section-desc">Execute deterministic benchmark suites directly against SQLite. No API key required — checks exact matching, aggregation, ordering, and edge-case error bounds.</div>
    </div>
    """, unsafe_allow_html=True)

    col_btn_test, _ = st.columns([1.5, 3.5])
    with col_btn_test:
        run_benchmarks = st.button("▶️ Run Complete Benchmark Suite", type="primary", use_container_width=True)

    if run_benchmarks:
        with st.status("🧪 Executing 5 Reference Benchmarks against SQLite...", expanded=True) as test_box:
            st.write("• Checking TC001: Retrieve all employee records (Row Count & Content)...")
            st.write("• Checking TC002: Salary threshold filtering (> $80,000)...")
            st.write("• Checking TC003: Departmental headcount aggregation...")
            st.write("• Checking TC004: Ranking top 5 highest earners (DESC ordering)...")
            st.write("• Checking TC005: Schema edge case — unsupported column rejection...")
            test_results = automation.run_all_reference_tests()
            test_box.update(label="✨ All 5 Reference Benchmarks Verified!", state="complete", expanded=False)

        passed = sum(1 for r in test_results if r.get("passed"))
        failed = len(test_results) - passed
        pass_rate = int((passed / len(test_results)) * 100)

        # KPI Dashboard Cards
        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card" style="border-top: 3px solid #6366f1;">
                <div class="kpi-label">Total Benchmarks</div>
                <div class="kpi-val">{len(test_results)}</div>
            </div>
            <div class="kpi-card" style="border-top: 3px solid #10b981;">
                <div class="kpi-label">Passed</div>
                <div class="kpi-val" style="color: #34d399;">{passed}</div>
            </div>
            <div class="kpi-card" style="border-top: 3px solid #ef4444;">
                <div class="kpi-label">Failed</div>
                <div class="kpi-val" style="color: #f87171;">{failed}</div>
            </div>
            <div class="kpi-card" style="border-top: 3px solid #38bdf8;">
                <div class="kpi-label">Pass Rate</div>
                <div class="kpi-val" style="color: #38bdf8;">{pass_rate}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if passed == len(test_results):
            st.balloons()
            st.toast("🎉 100% Score! All 5 reference benchmark tests successfully passed.", icon="🏆")

        # Detailed cards
        st.markdown("#### Test Execution Results")
        for r in test_results:
            is_pass = r.get("passed", False)
            status_text = "PASS" if is_pass else "FAIL"
            badge_class = "badge-success" if is_pass else "badge-error"
            icon = "✅" if is_pass else "❌"

            with st.expander(f"{icon} **{r.get('test_id')}** — {r.get('question')} [{status_text}]", expanded=not is_pass):
                st.markdown(f"**Verification Reason:** {r.get('reason')}")
                if r.get("sql"):
                    st.code(r["sql"], language="sql")

                det = r.get("details", {})
                if det:
                    if "rows" in det and det["rows"] is not None:
                        df = pd.DataFrame(det["rows"], columns=det.get("columns", []))
                        st.dataframe(df, use_container_width=True)
                    elif "error" in det:
                        st.markdown(f"""
                        <div class="callout-box warning">
                            <span>⚠️</span>
                            <div><strong>Expected Handled Error:</strong> <code>{det['error']}</code></div>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="callout-box info">
            <span>💡</span>
            <div>Click <strong>Run Complete Benchmark Suite</strong> above to trigger the 5 deterministic verification test cases.</div>
        </div>
        """, unsafe_allow_html=True)

    # Reference Case Definitions
    st.markdown("---")
    st.markdown("#### 📋 Test Case Catalog Definitions")
    for tc in evaluator.REFERENCE_CASES:
        with st.expander(f"📌 `{tc['id']}`: {tc['question']}"):
            st.markdown(f"**Verification Strategy:** `{tc['check_type']}`")
            if tc.get("expected_sql"):
                st.code(tc["expected_sql"], language="sql")
            if tc.get("expected_row_count") is not None:
                st.markdown(f"**Expected Row Count:** `{tc['expected_row_count']}`")
            if tc.get("expected_error"):
                st.markdown(f"**Expected Error Pattern:** `{tc['expected_error']}`")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AUDIT & EXECUTION HISTORY
# ══════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.markdown("""
    <div class="section-header">
        <h3 class="section-title">📜 Audit Trail & Query Telemetry</h3>
        <div class="section-desc">Search, inspect, and export all generated queries, AST validation statuses, and execution metadata stored in SQLite.</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        history = storage.get_history(limit=50)

        # Controls row
        hist_col1, hist_col2, hist_col3 = st.columns([2, 1.5, 1])
        with hist_col1:
            search_term = st.text_input("🔍 Search past queries", placeholder="Filter by question keyword...").strip().lower()
        with hist_col2:
            status_filter = st.selectbox("Status Filter", ["All Runs", "Valid AST Only", "Successful Executions Only"])
        with hist_col3:
            st.write("")
            refresh_btn = st.button("🔄 Refresh", use_container_width=True)
            if refresh_btn:
                st.rerun()

        if not history:
            st.markdown("""
            <div class="callout-box info">
                <span>ℹ️</span>
                <div>No recorded query runs yet. Switch to the <b>Query Studio</b> tab to generate and execute your first prompt!</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Filter history
            filtered_history = history
            if search_term:
                filtered_history = [r for r in filtered_history if search_term in r.get("question", "").lower()]

            if status_filter == "Valid AST Only":
                filtered_history = [r for r in filtered_history if r.get("validation_status") == "valid"]
            elif status_filter == "Successful Executions Only":
                filtered_history = [r for r in filtered_history if r.get("execution_status") == "success"]

            # History Stats
            tot_runs = len(history)
            valid_runs = sum(1 for r in history if r.get("validation_status") == "valid")
            exec_runs = sum(1 for r in history if r.get("execution_status") == "success")

            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
            s_col1.metric("Total Runs", tot_runs)
            s_col2.metric("Valid AST", f"{valid_runs}/{tot_runs}")
            s_col3.metric("Executed", f"{exec_runs}/{tot_runs}")
            with s_col4:
                # Export history JSON
                history_json = json.dumps(history, indent=2, default=str)
                st.download_button(
                    label="📥 Export Audit JSON",
                    data=history_json,
                    file_name="querycraft_audit_history.json",
                    mime="application/json",
                    use_container_width=True,
                )

            st.write("")
            st.markdown(f"**Displaying {len(filtered_history)} of {tot_runs} runs:**")

            for run in filtered_history:
                run_id = run.get("run_id", "?")
                ts     = run.get("timestamp", "")[:19]
                q      = run.get("question", "")
                pv     = run.get("prompt_version", "")
                vs     = run.get("validation_status", "")
                es     = run.get("execution_status", "")
                rc     = run.get("row_count")

                vs_badge = "badge-success" if vs == "valid" else "badge-error"
                es_badge = "badge-success" if es == "success" else ("badge-neutral" if es == "skipped" else "badge-error")

                header_label = f"**{run_id}** · {ts} · {q[:65]}{'…' if len(q) > 65 else ''}"

                with st.expander(header_label, expanded=False):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.markdown(f"**Run ID:** `{run_id}`")
                    c2.markdown(f"**Prompt Strategy:** `{pv}`")
                    c3.markdown(f"**Validation:** <span class='badge-pill {vs_badge}'>{vs.upper()}</span>", unsafe_allow_html=True)
                    c4.markdown(f"**Execution:** <span class='badge-pill {es_badge}'>{es.upper()}</span>", unsafe_allow_html=True)

                    if run.get("generated_sql"):
                        st.code(run["generated_sql"], language="sql")

                    if run.get("row_count") is not None:
                        st.markdown(f"**Rows returned:** `{rc}`")

                    if run.get("result_json"):
                        try:
                            data = json.loads(run["result_json"])
                            rows = data.get("rows", [])
                            cols = data.get("columns", [])
                            if rows:
                                df = pd.DataFrame(rows, columns=cols)
                                st.dataframe(df, use_container_width=True)
                        except Exception:
                            pass

                    if run.get("error_message"):
                        st.markdown(f"""
                        <div class="callout-box danger">
                            <span>❌</span>
                            <div>{run['error_message']}</div>
                        </div>
                        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Could not load telemetry history: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PROMPT LABORATORY & BENCHMARKING
# ══════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.markdown("""
    <div class="section-header">
        <h3 class="section-title">⚖️ Prompt Engineering Laboratory</h3>
        <div class="section-desc">Run natural language inputs across all three prompt versions (v1, v2, v3) in parallel to evaluate SQL generation quality, strictness, and schema compliance.</div>
    </div>
    """, unsafe_allow_html=True)

    cmp_question = st.text_input(
        "Question to evaluate across prompt strategies:",
        value="Show the five highest paid employees",
        help="This question will be executed concurrently with v1, v2, and v3 prompt configurations."
    )

    cmp_btn, _ = st.columns([1.5, 3.5])
    with cmp_btn:
        compare_clicked = st.button("🔬 Compare All 3 Strategies", type="primary", use_container_width=True)

    if compare_clicked:
        if not active_key_set:
            st.markdown("""
            <div class="callout-box warning">
                <span>⚠️</span>
                <div><strong>API Key Required:</strong> Comparing prompt versions requires an active API key (set in the sidebar or in <code>.env</code>).</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            cols = st.columns(3)
            versions = ["v1_basic", "v2_structured", "v3_refined"]
            labels = ["v1 — Basic", "v2 — Structured", "v3 — Refined"]

            for col, ver, lab in zip(cols, versions, labels):
                with col:
                    st.markdown(f"""
                    <div style="background:#131b2e; border:1px solid rgba(255, 255, 255, 0.08); border-radius:10px; padding:10px; text-align:center; font-weight:700; margin-bottom:12px; color:#f1f5f9;">
                        {lab}
                    </div>
                    """, unsafe_allow_html=True)
                    with st.spinner(f"Inference with {ver}…"):
                        res = automation.run_workflow(
                            question=cmp_question,
                            prompt_version=ver,
                            model=model_name,
                        )
                    stages = res.get("stages") or {}
                    gen = stages.get("generation") or {}
                    val = stages.get("validation") or {}
                    exc = stages.get("execution") or {}

                    if gen.get("success"):
                        st.code(gen.get("sql", ""), language="sql")
                        v_ok = bool(val.get("valid", False))
                        e_ok = bool(exc.get("success", False))

                        st.markdown(f"""
                        <div style="display:flex; gap:6px; margin: 8px 0;">
                            <span class="badge-pill {'badge-success' if v_ok else 'badge-error'}">AST: {'VALID' if v_ok else 'REJECT'}</span>
                            <span class="badge-pill {'badge-success' if e_ok else 'badge-error'}">EXEC: {'OK' if e_ok else 'FAIL'}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        if exc.get("success"):
                            rows = exc.get("data", {}).get("rows", [])
                            cols2 = exc.get("data", {}).get("columns", [])
                            if rows:
                                st.dataframe(pd.DataFrame(rows, columns=cols2), use_container_width=True)
                    else:
                        st.markdown(f"""
                        <div class="callout-box danger">
                            <span>❌</span>
                            <div>{gen.get('error', 'Generation failed')}</div>
                        </div>
                        """, unsafe_allow_html=True)

            st.toast("📊 Prompt strategy comparative analysis finished!", icon="⚖️")

    # Static comparison matrix
    st.markdown("---")
    st.markdown("#### 📊 Strategy Architecture Matrix")

    comparison_data = {
        "Capabilities & Safety Guardrails": [
            "Database Schema Injected",
            "Target SQLite Dialect Specified",
            "Read-Only SELECT Restriction Rule",
            "Prohibited Mutation Clauses (DROP/UPDATE/DELETE)",
            "Non-Existent Schema Fallback (CANNOT_ANSWER)",
            "Strict JSON/Code Fence Output Control",
        ],
        "v1 — Basic":       ["❌ No", "❌ No", "❌ No", "❌ No", "❌ No", "❌ No"],
        "v2 — Structured":  ["✅ Yes", "✅ Yes", "⚠️ Partial", "⚠️ Partial", "❌ No", "✅ Yes"],
        "v3 — Refined":     ["✅ Full DDL", "✅ Strict", "✅ Complete", "✅ Enforced", "✅ Active", "✅ Strict Guard"],
    }
    st.table(pd.DataFrame(comparison_data).set_index("Capabilities & Safety Guardrails"))

    # Raw prompt templates
    st.markdown("---")
    st.markdown("#### 📄 Inspect Raw Prompt Templates")
    for ver in ["v1_basic", "v2_structured", "v3_refined"]:
        with st.expander(f"📑 `{ver}.txt` Template"):
            try:
                prompt_path = PROJECT_ROOT / "prompts" / f"{ver}.txt"
                st.code(prompt_path.read_text(), language="markdown")
            except FileNotFoundError:
                st.warning(f"Prompt template file not found: {ver}.txt")
