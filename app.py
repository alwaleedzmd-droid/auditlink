"""
╔══════════════════════════════════════════════════════════╗
║           AuditLink — نظام التدقيق ومتابعة التوطين       ║
╚══════════════════════════════════════════════════════════╝
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO

from modules.data_loader import (
    load_gosi_file, load_medical_file,
    load_muqeem_file, load_payroll_file,
)
from modules.audit_engine import (
    run_all_audits, get_audit_summary, AUDIT_PAGES, PAGE_REQUIREMENTS, PAGE_KEYS,
)
from modules.nitaqat_engine import (
    compute_profession_nitaqat, get_nitaqat_summary,
)
from modules.entity_nitaqat import compute_entity_band
from modules.nitaqat_constants import (
    list_activities, BAND_KEYS, BAND_LABELS_AR, BAND_COLORS_HEX, YEARS,
)

# ─────────────────────────────────────────────────────────
#  Page Config
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AuditLink — نظام التدقيق والتوطين",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────
#  Global CSS — Apple-style Design System
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Tajawal:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg-primary:    #f5f5f7;
    --bg-card:       #ffffff;
    --bg-glass:      rgba(255,255,255,0.72);
    --border:        rgba(0,0,0,0.08);
    --text-primary:  #1d1d1f;
    --text-secondary:#6e6e73;
    --accent-blue:   #0071e3;
    --accent-green:  #30d158;
    --accent-red:    #ff453a;
    --accent-orange: #ff9f0a;
    --accent-yellow: #ffd60a;
    --shadow-sm:     0 2px 8px rgba(0,0,0,0.06);
    --shadow-md:     0 8px 24px rgba(0,0,0,0.08);
    --shadow-lg:     0 20px 60px rgba(0,0,0,0.10);
    --radius-sm:     10px;
    --radius-md:     16px;
    --radius-lg:     20px;
}

html, body, [class*="css"] {
    font-family: 'Tajawal', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    direction: rtl;
    color: var(--text-primary);
}

.stApp { background: var(--bg-primary); }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ─── Hero Header ─── */
.hero {
    background: linear-gradient(135deg, #1d1d1f 0%, #2c2c2e 50%, #1c1c1e 100%);
    padding: 48px 60px 40px;
    margin-bottom: 0;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(0,113,227,0.3) 0%, transparent 70%);
    border-radius: 50%;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -80px; left: 100px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(48,209,88,0.2) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-size: 42px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -1px;
    margin: 0 0 8px 0;
}
.hero-title span { color: #0071e3; }
.hero-sub {
    font-size: 17px;
    color: rgba(255,255,255,0.55);
    font-weight: 400;
    margin: 0;
}

/* ─── Tab Bar ─── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card);
    border-radius: var(--radius-md);
    padding: 6px;
    gap: 4px;
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    margin: 0 60px 28px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-sm) !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    padding: 10px 24px !important;
    transition: all 0.2s ease !important;
    border: none !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent-blue) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(0,113,227,0.35) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 0 60px 40px !important; }

/* ─── Cards ─── */
.card {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-md);
    padding: 28px;
    height: 100%;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }

/* ─── KPI Cards ─── */
.kpi-card {
    background: var(--bg-card);
    border-radius: var(--radius-md);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    padding: 24px 28px;
    position: relative;
    overflow: hidden;
}
.kpi-accent { position: absolute; top:0; right:0; width:4px; height:100%; border-radius: 0 var(--radius-md) var(--radius-md) 0; }
.kpi-num { font-size: 40px; font-weight: 700; letter-spacing: -1px; margin: 4px 0; }
.kpi-label { font-size: 13px; font-weight: 500; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* ─── File Upload Zone ─── */
.upload-zone {
    background: var(--bg-card);
    border: 2px dashed var(--border);
    border-radius: var(--radius-md);
    padding: 32px 24px;
    text-align: center;
    transition: border-color 0.2s;
}
.upload-zone:hover { border-color: var(--accent-blue); }
.upload-icon { font-size: 36px; margin-bottom: 8px; }
.upload-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.upload-sub { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* ─── Status Badges ─── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.badge-red    { background: rgba(255,69,58,0.12);  color: #ff453a; }
.badge-orange { background: rgba(255,159,10,0.12); color: #ff9f0a; }
.badge-green  { background: rgba(48,209,88,0.12);  color: #25a244; }
.badge-blue   { background: rgba(0,113,227,0.10);  color: #0071e3; }

/* ─── Section Headers ─── */
.section-title {
    font-size: 22px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}
.section-sub {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 24px;
}

/* ─── Dataframe Overrides ─── */
.stDataFrame { border-radius: var(--radius-md) !important; overflow: hidden; }

/* ─── Buttons ─── */
.stButton > button {
    background: var(--accent-blue) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 12px 28px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(0,113,227,0.3) !important;
    font-family: 'Tajawal', sans-serif !important;
}
.stButton > button:hover {
    background: #0077ed !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(0,113,227,0.4) !important;
}

/* ─── File uploader ─── */
[data-testid="stFileUploader"] {
    background: var(--bg-card);
    border-radius: var(--radius-md);
    border: 1px solid var(--border);
    padding: 8px;
}
[data-testid="stFileUploader"] label { font-weight: 600 !important; color: var(--text-primary) !important; }

/* ─── Divider ─── */
.divider { border: none; border-top: 1px solid var(--border); margin: 24px 0; }

/* ─── Audit Page Card ─── */
.audit-page-card {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-md);
    padding: 28px;
    margin-bottom: 20px;
}
.audit-page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}
.audit-page-title {
    font-size: 17px;
    font-weight: 700;
    color: var(--text-primary);
}
.audit-page-count {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -1px;
}

/* ─── Summary Table ─── */
.summary-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    direction: rtl;
    color: var(--text-primary);
    background: var(--bg-card);
}
.summary-table th {
    background: #e8e8ed;
    color: var(--text-primary);
    padding: 10px 16px;
    text-align: right;
    font-weight: 700;
    border-bottom: 2px solid var(--border);
}
.summary-table td {
    padding: 10px 16px;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border);
}
.summary-table tr:last-child td {
    font-weight: 700;
    background: #f0f0f2;
    color: var(--text-primary);
}

/* ─── Nitaqat ─── */
.nitaqat-bar-wrap {
    background: #e5e5ea;
    border-radius: 99px;
    height: 12px;
    overflow: hidden;
    margin: 6px 0;
}
.nitaqat-bar-fill {
    height: 100%;
    border-radius: 99px;
    transition: width 0.5s ease;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
#  Session State Bootstrap
# ─────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        'audit_results': None,
        'audit_summary': None,
        'nitaqat_df': None,
        'nitaqat_summary': None,
        'gosi_df': None,
        'files_processed': False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ─────────────────────────────────────────────────────────
#  Helper UI Functions  (defined here — used in tabs below)
# ─────────────────────────────────────────────────────────

def _empty_state(icon, title, subtitle):
    st.markdown(f"""
    <div style="text-align:center; padding:80px 20px;">
      <div style="font-size:64px; margin-bottom:16px;">{icon}</div>
      <div style="font-size:22px; font-weight:700; color:#1d1d1f; margin-bottom:8px;">{title}</div>
      <div style="font-size:15px; color:#6e6e73;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def _kpi_card(icon, value, label, color, desc=""):
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-accent" style="background:{color};"></div>
      <div style="font-size:22px; margin-bottom:4px;">{icon}</div>
      <div class="kpi-num" style="color:{color};">{value}</div>
      <div class="kpi-label">{label}</div>
      {{"<div class='kpi-desc'>" + desc + "</div>" if desc else ""}}
    </div>
    """, unsafe_allow_html=True)


def _profession_card(row):
    profession = row['profession']
    saudi = int(row['saudi_count'])
    non_saudi = int(row['non_saudi_count'])
    total = int(row['total'])
    pct = row['saudi_pct']
    status = row['status']
    action = row.get('action', '')
    needed = int(row.get('required_saudis', 0))

    achieved = 'محقق' in str(status)
    bar_color = '#30d158' if achieved else '#ff453a'
    bar_w = min(pct, 100)
    status_badge = f'<span class="badge badge-green">{status}</span>' if achieved else f'<span class="badge badge-red">{status}</span>'

    extra_msg = ''
    if not achieved and needed > 0:
        extra_msg = f'<span style="color:#ff453a;font-size:13px;">⚠️ {action}</span>'
    if not achieved and needed == 0 and action:
        extra_msg = f'<span style="color:#ff9f0a;font-size:13px;">📝 {action}</span>'

    st.markdown(f"""
    <div class="card" style="margin-bottom:16px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <div>
          <div style="font-size:17px; font-weight:700; color:#1d1d1f;">🏷️ {profession}</div>
          <div style="font-size:13px; color:#6e6e73; margin-top:3px;">
            {total} موظف &nbsp;|&nbsp;
            <span style="color:#30d158;">{saudi} سعودي</span> &nbsp;|&nbsp;
            <span style="color:#6e6e73;">{non_saudi} غير سعودي</span>
          </div>
        </div>
        <div style="text-align:left;">
          {status_badge}
          <div style="font-size:28px; font-weight:800; color:{bar_color}; margin-top:4px;">{pct}%</div>
        </div>
      </div>

      <div class="nitaqat-bar-wrap">
        <div class="nitaqat-bar-fill" style="width:{bar_w}%; background:{bar_color};"></div>
      </div>
      {{"<div style='margin-top:10px;'>" + extra_msg + "</div>" if extra_msg else ""}}
    </div>
    """, unsafe_allow_html=True)


def _audit_summary_pie(summary):
    labels = []
    values = []
    colors = []
    for key in PAGE_KEYS:
        meta = AUDIT_PAGES[key]
        labels.append(meta['title_short'])
        values.append(summary[key]['total'])
        colors.append(meta['color'])

    if sum(values) == 0:
        return

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker_colors=colors,
        textinfo='percent+label',
        textfont_size=12,
        hovertemplate='%{label}: %{value} حالة<br>%{percent}<extra></extra>',
    )])
    fig.update_layout(
        title=dict(text="توزيع نتائج المقارنات", font=dict(size=16, family='Tajawal'), x=0.5),
        showlegend=False,
        margin=dict(t=50, b=0, l=0, r=0),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Tajawal'),
    )
    st.plotly_chart(fig, use_container_width=True)


def _audit_summary_bar(summary):
    pages = []
    totals = []
    colors = []
    for key in PAGE_KEYS:
        meta = AUDIT_PAGES[key]
        pages.append(f"صفحة {key[-1]}")
        totals.append(summary[key]['total'])
        colors.append(meta['color'])

    fig = go.Figure(go.Bar(
        x=pages,
        y=totals,
        marker_color=colors,
        text=totals,
        textposition='outside',
    ))
    fig.update_layout(
        title=dict(text="عدد الحالات لكل صفحة", font=dict(size=16, family='Tajawal'), x=0.5),
        font=dict(family='Tajawal', size=13),
        yaxis=dict(title='العدد', gridcolor='rgba(0,0,0,0.05)'),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=30, l=0, r=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def _nitaqat_bar_chart(nit_df):
    if nit_df.empty:
        return
    colors = ['#30d158' if 'محقق النسبة' in str(s) else '#ff453a' for s in nit_df['status']]
    fig = go.Figure(go.Bar(
        x=nit_df['profession'],
        y=nit_df['saudi_pct'],
        marker_color=colors,
        text=[f"{p}%" for p in nit_df['saudi_pct']],
        textposition='outside',
    ))
    fig.update_layout(
        title=dict(text="نسبة السعودة حسب المهنة", font=dict(size=16, family='Tajawal'), x=0.5),
        font=dict(family='Tajawal', size=11),
        xaxis_tickangle=-40,
        yaxis=dict(title='النسبة %', range=[0, 110], gridcolor='rgba(0,0,0,0.05)'),
        height=420,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=100, l=0, r=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def _nitaqat_needs_chart(nit_df):
    needs = nit_df[nit_df['required_saudis'] > 0].copy()
    if needs.empty:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; background:rgba(48,209,88,0.06); border-radius:16px;">
          <div style="font-size:48px;">🎉</div>
          <div style="font-size:18px; font-weight:700; color:#25a244; margin-top:12px;">جميع المهن حققت النسبة!</div>
        </div>
        """, unsafe_allow_html=True)
        return

    fig = go.Figure(go.Bar(
        x=needs['required_saudis'],
        y=needs['profession'],
        orientation='h',
        marker_color='#ff9f0a',
        text=[f"+{v}" for v in needs['required_saudis']],
        textposition='outside',
    ))
    fig.update_layout(
        title=dict(text="عدد السعوديين المطلوب لكل مهنة", font=dict(size=15, family='Tajawal'), x=0.5),
        font=dict(family='Tajawal', size=11),
        xaxis=dict(title='العدد المطلوب', gridcolor='rgba(0,0,0,0.05)'),
        height=420,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=0, l=0, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _export_audit_excel(results, summary):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sum_rows = []
        for key in PAGE_KEYS:
            meta = AUDIT_PAGES[key]
            if not summary[key].get('available', True):
                sum_rows.append({
                    'الصفحة': meta['title'],
                    'الإجراء المطلوب': 'غير متاح — ملف مطلوب مفقود',
                    'العدد': '-',
                })
                continue
            for action_text, count in summary[key]['actions'].items():
                sum_rows.append({
                    'الصفحة': meta['title'],
                    'الإجراء المطلوب': action_text,
                    'العدد': count,
                })
            sum_rows.append({
                'الصفحة': meta['title'],
                'الإجراء المطلوب': 'Grand Total',
                'العدد': summary[key]['total'],
            })
        if sum_rows:
            pd.DataFrame(sum_rows).to_excel(writer, sheet_name='ملخص التقرير', index=False)

        for key in PAGE_KEYS:
            df = results[key]
            if df is not None and not df.empty:
                meta = AUDIT_PAGES[key]
                sheet_name = f"صفحة {key[-1]}"
                cols = [c for c in df.columns if not c.startswith('_')]
                df[cols].to_excel(writer, sheet_name=sheet_name, index=False)

        for ws_name in writer.sheets:
            writer.sheets[ws_name].set_column(0, 20, 22)

    return output.getvalue()


def _export_nitaqat_excel(nit_df, nit_summary):
    output = BytesIO()
    rename = {
        'profession': 'المهنة', 'total': 'الإجمالي', 'saudi_count': 'سعوديون',
        'non_saudi_count': 'وافدون', 'saudi_pct': 'نسبة السعودة %',
        'status': 'الحالة', 'action': 'الإجراء', 'required_saudis': 'مطلوب توطين',
    }
    export_df = nit_df.rename(columns={k: v for k, v in rename.items() if k in nit_df.columns})
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df.to_excel(writer, sheet_name='توطين المهن', index=False)
        overall_df = pd.DataFrame([{
            'إجمالي الموظفين': nit_summary.get('total_employees', 0),
            'سعوديون': nit_summary.get('total_saudi', 0),
            'وافدون': nit_summary.get('total_non_saudi', 0),
            'نسبة التوطين الإجمالية %': nit_summary.get('overall_pct', 0),
            'مهن حققت النسبة': nit_summary.get('professions_achieved', 0),
            'مهن لم تحقق': nit_summary.get('professions_not_achieved', 0),
        }])
        overall_df.to_excel(writer, sheet_name='الملخص العام', index=False)
        for ws_name in writer.sheets:
            writer.sheets[ws_name].set_column(0, 15, 22)
    return output.getvalue()



# ─────────────────────────────────────────────────────────
#  Hero Header
# ─────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div style="display:flex; align-items:center; gap:16px; margin-bottom:12px;">
    <div style="font-size:48px;">🔗</div>
    <div>
      <div class="hero-title">Audit<span>Link</span></div>
      <div class="hero-sub">نظام التدقيق الذكي ومتابعة التوطين (نطاقات)</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
#  Tabs
# ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "   📂  رفع الملفات   ",
    "   🔍  تقرير المقارنات   ",
    "   📊  توطين المهن   ",
    "   🎯  نطاق المنشأة   ",
])


# ═══════════════════════════════════════════════════════════
#  TAB 1 — File Upload
# ═══════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="section-title">رفع ملفات التقارير</div>
    <div class="section-sub">ارفع الملفات الأربعة (أو أكثر) للحصول على تقرير المقارنات وتحليل التوطين</div>
    """, unsafe_allow_html=True)

    # ── Upload grid ──
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""<div class="upload-zone">
        <div class="upload-icon">📋</div>
        <div class="upload-title">ملف التأمينات الاجتماعية (GOSI)</div>
        <div class="upload-sub">رقم الهوية، اسم المشترك، حالة المشترك، الجنسية، المهنة</div>
        </div>""", unsafe_allow_html=True)
        gosi_file = st.file_uploader("GOSI", type=["xlsx", "xls"], key="gosi_file", label_visibility="collapsed")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        st.markdown("""<div class="upload-zone">
        <div class="upload-icon">🏥</div>
        <div class="upload-title">ملف التأمين الصحي (CCHI)</div>
        <div class="upload-sub">Iqama No، Member Name، Relation، Class، Premium</div>
        </div>""", unsafe_allow_html=True)
        med_file = st.file_uploader("التأمين الصحي", type=["xlsx", "xls"], key="med_file", label_visibility="collapsed")

    with col2:
        st.markdown("""<div class="upload-zone">
        <div class="upload-icon">💰</div>
        <div class="upload-title">ملف الرواتب (Payroll)</div>
        <div class="upload-sub">رقم الهوية، Employees Number، الوظيفة، الشعبة</div>
        </div>""", unsafe_allow_html=True)
        pay_file = st.file_uploader("الرواتب", type=["xlsx", "xls"], key="pay_file", label_visibility="collapsed")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        st.markdown("""<div class="upload-zone">
        <div class="upload-icon">🌐</div>
        <div class="upload-title">ملف مقيم (Muqeem)</div>
        <div class="upload-sub">رقم الاقامة، الاسم، الجنسية، المهنة، رقم الجواز</div>
        </div>""", unsafe_allow_html=True)
        muq_file = st.file_uploader("مقيم", type=["xlsx", "xls"], key="muq_file", label_visibility="collapsed")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── File status ──
    uploaded_count = sum(1 for f in [gosi_file, med_file, pay_file, muq_file] if f is not None)

    status_cols = st.columns(4)
    file_checks = [
        ("📋 GOSI", gosi_file),
        ("🏥 التأمين الصحي", med_file),
        ("💰 الرواتب", pay_file),
        ("🌐 مقيم", muq_file),
    ]
    for i, (label, f) in enumerate(file_checks):
        with status_cols[i]:
            if f:
                st.markdown(f"""<div style="background:rgba(48,209,88,0.08);border-radius:12px;padding:12px;text-align:center;">
                <div style="font-size:20px;">✅</div>
                <div style="font-size:13px;font-weight:600;color:#25a244;">{label}</div>
                <div style="font-size:11px;color:#6e6e73;">تم الرفع</div></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div style="background:rgba(0,0,0,0.03);border-radius:12px;padding:12px;text-align:center;">
                <div style="font-size:20px;">⬜</div>
                <div style="font-size:13px;font-weight:600;color:#6e6e73;">{label}</div>
                <div style="font-size:11px;color:#aaa;">لم يُرفع</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Process Button ──
    can_process = uploaded_count >= 2
    proc_col, _ = st.columns([1, 3])
    with proc_col:
        process_btn = st.button(
            "🚀  تحليل ومقارنة البيانات",
            use_container_width=True,
            disabled=not can_process,
        )

    if not can_process:
        st.markdown("""<div style="background:rgba(255,159,10,0.08);border-radius:10px;padding:14px 18px;
        font-size:14px;font-weight:500;border-right:4px solid #ff9f0a;color:#9a6700;">
        ⚠️ يلزم رفع ملفين على الأقل لإجراء المقارنة (مثلاً: GOSI + التأمين الصحي)
        </div>""", unsafe_allow_html=True)

    if process_btn and can_process:
        with st.spinner("⚙️ جارٍ تحليل ومقارنة البيانات..."):
            loaders = [
                ('GOSI (التأمينات)',     gosi_file, load_gosi_file),
                ('التأمين الصحي',        med_file,  load_medical_file),
                ('مقيم',                 muq_file,  load_muqeem_file),
                ('الرواتب',              pay_file,  load_payroll_file),
            ]
            loaded = {}
            load_errors = []
            for label, f, loader in loaders:
                if f is None:
                    loaded[label] = None
                    continue
                try:
                    loaded[label] = loader(f)
                except Exception as exc:
                    loaded[label] = None
                    load_errors.append((label, exc))

            if load_errors:
                for label, exc in load_errors:
                    st.error(f"❌ فشل تحميل ملف {label}: {exc}")
                st.stop()

            gosi_df = loaded['GOSI (التأمينات)']
            med_df  = loaded['التأمين الصحي']
            muq_df  = loaded['مقيم']
            pay_df  = loaded['الرواتب']

            try:
                results = run_all_audits(gosi_df, med_df, muq_df, pay_df)
                summary = get_audit_summary(results)

                nit_df = compute_profession_nitaqat(gosi_df)
                nit_summary = get_nitaqat_summary(nit_df)

                st.session_state['audit_results'] = results
                st.session_state['audit_summary'] = summary
                st.session_state['gosi_df'] = gosi_df
                st.session_state['nitaqat_df'] = nit_df
                st.session_state['nitaqat_summary'] = nit_summary
                st.session_state['files_processed'] = True

                available_issues = sum(s['total'] for s in summary.values() if s.get('available', True))
                unavailable_pages = [k for k, s in summary.items() if not s.get('available', True)]
                msg = f"✅ تمت المعالجة بنجاح! تم اكتشاف {available_issues} حالة تحتاج مراجعة."
                if unavailable_pages:
                    msg += f" ({len(unavailable_pages)} مقارنة غير متاحة — يلزم رفع الملفات الناقصة)"
                st.success(msg)

            except Exception as e:
                st.error(f"❌ خطأ أثناء المقارنة: {e}")
                st.exception(e)


# ═══════════════════════════════════════════════════════════
#  TAB 2 — Audit / Cross-Reference Report
# ═══════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if not st.session_state['files_processed'] or st.session_state['audit_results'] is None:
        _empty_state("🔍", "لا توجد بيانات محللة بعد", "ارفع الملفات من تبويب «رفع الملفات» وانقر على «تحليل ومقارنة»")
    else:
        results = st.session_state['audit_results']
        summary = st.session_state['audit_summary']

        # ── Top KPI Row ──
        st.markdown('<div class="section-title">ملخص المقارنات</div>', unsafe_allow_html=True)

        kpi_cols = st.columns(len(PAGE_KEYS), gap="small")
        page_keys = PAGE_KEYS
        for i, key in enumerate(page_keys):
            meta = AUDIT_PAGES[key]
            with kpi_cols[i]:
                page_summary = summary[key]
                if not page_summary.get('available', True):
                    st.markdown(f"""
                    <div class="kpi-card" style="border-top: 3px solid #d0d0d5; opacity:0.7;">
                      <div style="font-size:24px;margin-bottom:6px;">⚠️</div>
                      <div class="kpi-num" style="color:#8a8a8e;font-size:22px;">غير متاح</div>
                      <div class="kpi-label" style="font-size:11px;line-height:1.4;">{meta['title_short']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    total = page_summary['total']
                    st.markdown(f"""
                    <div class="kpi-card" style="border-top: 3px solid {meta['color']};">
                      <div style="font-size:24px;margin-bottom:6px;">{meta['icon']}</div>
                      <div class="kpi-num" style="color:{meta['color']};font-size:36px;">{total}</div>
                      <div class="kpi-label" style="font-size:11px;line-height:1.4;">{meta['title_short']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # ── Detailed Pages ──
        for key in page_keys:
            meta = AUDIT_PAGES[key]
            page_df = results[key]
            page_summary = summary[key]
            available = page_summary.get('available', True)
            total = page_summary['total']
            actions = page_summary['actions']

            count_html = (
                f'<div class="audit-page-count" style="color:#8a8a8e;font-size:16px;">غير متاح</div>'
                if not available else
                f'<div class="audit-page-count" style="color:{meta["color"]};">{total}</div>'
            )
            st.markdown(f"""
            <div class="audit-page-card">
              <div class="audit-page-header">
                <div>
                  <div class="audit-page-title">{meta['icon']} صفحة {key[-1]} — {meta['title']}</div>
                </div>
                {count_html}
              </div>
            </div>
            """, unsafe_allow_html=True)

            if not available:
                needed_a, needed_b = PAGE_REQUIREMENTS[key]
                st.markdown(f"""
                <div style="text-align:center;padding:20px;background:rgba(255,159,10,0.08);
                border-radius:12px;margin-bottom:12px;border-right:4px solid #ff9f0a;">
                <div style="font-size:22px;">⚠️</div>
                <div style="font-size:14px;color:#9a6700;font-weight:600;">
                يتطلّب رفع ملفّي «{needed_a}» و«{needed_b}» لإجراء هذه المقارنة
                </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                continue

            if total > 0:
                # Summary Table (matches report format)
                summary_html = '<table class="summary-table"><thead><tr>'
                summary_html += f'<th>{meta["title"]}</th><th>الإجراء المطلوب</th></tr></thead><tbody>'

                for action_text, count in sorted(actions.items(), key=lambda x: -x[1]):
                    summary_html += f'<tr><td>{action_text}</td><td>{count}</td></tr>'

                summary_html += f'<tr><td><strong>Grand Total</strong></td><td><strong>{total}</strong></td></tr>'
                summary_html += '</tbody></table>'
                st.markdown(summary_html, unsafe_allow_html=True)

                st.markdown(
                    f"<div style='margin-top:16px;font-size:13px;font-weight:600;"
                    f"color:var(--text-secondary);'>📋 تفاصيل الموظفين ({total} سجل)</div>",
                    unsafe_allow_html=True,
                )

                display_cols = [c for c in page_df.columns
                                if not c.startswith('_') and c != 'الإجراء المطلوب']
                display_cols.append('الإجراء المطلوب')
                display_cols = [c for c in display_cols if c in page_df.columns]

                st.dataframe(
                    page_df[display_cols],
                    use_container_width=True,
                    height=min(500, 35 * len(page_df) + 42),
                )
            else:
                st.markdown("""
                <div style="text-align:center;padding:20px;background:rgba(48,209,88,0.06);
                border-radius:12px;margin-bottom:12px;">
                <div style="font-size:24px;">✅</div>
                <div style="font-size:14px;color:#25a244;font-weight:600;">لا توجد فروقات</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # ── Charts ──
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">الرسوم البيانية</div>', unsafe_allow_html=True)

        ch1, ch2 = st.columns(2, gap="large")
        with ch1:
            _audit_summary_pie(summary)
        with ch2:
            _audit_summary_bar(summary)

        # ── Export ──
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        ex_col, _ = st.columns([1, 4])
        with ex_col:
            excel_bytes = _export_audit_excel(results, summary)
            st.download_button(
                "📥  تنزيل تقرير المقارنات (Excel)",
                data=excel_bytes,
                file_name="AuditLink_CrossRef_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )


# ═══════════════════════════════════════════════════════════
#  TAB 3 — Profession Nationalization (توطين المهن)
# ═══════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if not st.session_state['files_processed'] or st.session_state['nitaqat_df'] is None:
        _empty_state("📊", "لا توجد بيانات للتوطين", "ارفع ملف GOSI من تبويب «رفع الملفات» للحصول على تحليل توطين المهن")
    else:
        nit_df = st.session_state['nitaqat_df']
        nit_summary = st.session_state['nitaqat_summary']

        if nit_df.empty:
            st.warning("⚠️ لا توجد بيانات مهن في ملف GOSI.")
        else:
            st.markdown('<div class="section-title">صفحة 5 — توطين المهن</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-sub">تحليل نسب السعودة حسب المهنة من بيانات التأمينات الاجتماعية</div>', unsafe_allow_html=True)

            # ── KPIs ──
            ok1, ok2, ok3, ok4, ok5 = st.columns(5, gap="small")
            with ok1:
                _kpi_card("👥", nit_summary.get('total_employees', 0), "إجمالي الموظفين", "#0071e3")
            with ok2:
                _kpi_card("🇸🇦", nit_summary.get('total_saudi', 0), "سعوديون", "#30d158")
            with ok3:
                _kpi_card("🌍", nit_summary.get('total_non_saudi', 0), "وافدون", "#ff9f0a")
            with ok4:
                pct = nit_summary.get('overall_pct', 0)
                _kpi_card("📈", f"{pct}%", "نسبة التوطين الإجمالية", "#0071e3")
            with ok5:
                ach = nit_summary.get('professions_achieved', 0)
                tot_p = nit_summary.get('total_professions', 0)
                _kpi_card("✅", f"{ach}/{tot_p}", "مهن حققت النسبة", "#30d158")

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)

            # ── Profession Cards ──
            for _, row in nit_df.iterrows():
                _profession_card(row)

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)

            # ── Charts ──
            ch_a, ch_b = st.columns(2, gap="large")
            with ch_a:
                _nitaqat_bar_chart(nit_df)
            with ch_b:
                _nitaqat_needs_chart(nit_df)

            # ── Full Table ──
            st.markdown('<div class="section-title">جدول التوطين التفصيلي</div>', unsafe_allow_html=True)
            display_nit = nit_df.rename(columns={
                'profession': 'المهنة', 'total': 'الإجمالي', 'saudi_count': 'سعوديون',
                'non_saudi_count': 'وافدون', 'saudi_pct': 'نسبة السعودة %',
                'status': 'الحالة', 'action': 'الإجراء', 'required_saudis': 'مطلوب توطين',
            })
            st.dataframe(display_nit, use_container_width=True, height=min(500, 35 * len(nit_df) + 38))

            # ── Export ──
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            ex_col2, _ = st.columns([1, 4])
            with ex_col2:
                nit_excel = _export_nitaqat_excel(nit_df, nit_summary)
                st.download_button(
                    "📥  تنزيل تقرير التوطين (Excel)",
                    data=nit_excel,
                    file_name="AuditLink_Nitaqat_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )


# ═══════════════════════════════════════════════════════════
#  TAB 4 — Entity Nitaqat Band (نطاق المنشأة - نطاقات المطور 2026)
# ═══════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if not st.session_state['files_processed'] or st.session_state['gosi_df'] is None:
        _empty_state(
            "🎯",
            "لا توجد بيانات لاحتساب النطاق",
            "ارفع ملف GOSI من تبويب «رفع الملفات» ثم اختر النشاط والسنة هنا",
        )
    else:
        st.markdown('<div class="section-title">نطاق المنشأة — نطاقات المطور 2026</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-sub">احتساب لون النطاق (أحمر / أخضر منخفض / متوسط / مرتفع / بلاتيني) '
            'وفق الدليل الإجرائي: <code>ص = m × ln(س) + t</code></div>',
            unsafe_allow_html=True,
        )

        sel_col1, sel_col2 = st.columns([3, 1], gap="large")
        with sel_col1:
            activity = st.selectbox(
                "النشاط الاقتصادي",
                options=list_activities(),
                key="entity_activity",
            )
        with sel_col2:
            year = st.selectbox("السنة", options=list(YEARS), key="entity_year")

        try:
            result = compute_entity_band(st.session_state['gosi_df'], activity, int(year))
        except Exception as e:
            st.error(f"خطأ في الاحتساب: {e}")
            st.stop()

        if result['total'] == 0:
            st.warning("⚠️ لا يوجد موظفون نشطون في ملف GOSI لاحتساب النطاق.")
            st.stop()

        # ── KPIs ──
        k1, k2, k3, k4, k5 = st.columns(5, gap="small")
        with k1:
            _kpi_card("👥", result['total'], "إجمالي العمالة النشطة", "#0071e3")
        with k2:
            _kpi_card("🇸🇦", result['saudi'], "سعوديون", "#30d158")
        with k3:
            _kpi_card("🌍", result['non_saudi'], "وافدون", "#ff9f0a")
        with k4:
            _kpi_card("📈", f"{result['saudi_pct']}%", "نسبة التوطين الفعلية (ن)", "#0071e3")
        with k5:
            _kpi_card("🎯", result['band_label_ar'], "النطاق الحالي", result['band_color'])

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # ── Thresholds visualization ──
        st.markdown('<div class="section-title">العتبات الأربع (ص) للنشاط المختار</div>', unsafe_allow_html=True)

        thr = result['thresholds']
        segments = [
            ("red",        0,                  thr['low_green']),
            ("low_green",  thr['low_green'],   thr['mid_green']),
            ("mid_green",  thr['mid_green'],   thr['high_green']),
            ("high_green", thr['high_green'],  thr['platinum']),
            ("platinum",   thr['platinum'],    100),
        ]

        # Build a horizontal stacked bar to visualize bands
        bar_fig = go.Figure()
        for band_key, start, end in segments:
            width = max(0, end - start)
            if width <= 0:
                continue
            bar_fig.add_trace(go.Bar(
                x=[width],
                y=["النطاق"],
                base=[start],
                orientation='h',
                marker=dict(color=BAND_COLORS_HEX[band_key]),
                name=BAND_LABELS_AR[band_key],
                hovertemplate=f"{BAND_LABELS_AR[band_key]}: {start:.2f}% → {end:.2f}%<extra></extra>",
                showlegend=True,
            ))
        # Marker for current position
        bar_fig.add_trace(go.Scatter(
            x=[result['saudi_pct']],
            y=["النطاق"],
            mode='markers+text',
            marker=dict(symbol='triangle-down', size=22, color='#1d1d1f', line=dict(width=2, color='white')),
            text=[f"أنت هنا: {result['saudi_pct']}%"],
            textposition='top center',
            textfont=dict(size=13, family='Tajawal', color='#1d1d1f'),
            showlegend=False,
            hovertemplate=f"نسبة التوطين الحالية: {result['saudi_pct']}%<extra></extra>",
        ))
        bar_fig.update_layout(
            barmode='stack',
            xaxis=dict(title='نسبة التوطين %', range=[0, 100], gridcolor='rgba(0,0,0,0.05)'),
            yaxis=dict(showticklabels=False),
            height=250,
            margin=dict(t=40, b=40, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Tajawal'),
            legend=dict(orientation='h', y=-0.3),
        )
        st.plotly_chart(bar_fig, use_container_width=True)

        # ── Thresholds table ──
        st.markdown('<div class="section-title">الحدود الدنيا والفجوة بعدد السعوديين</div>', unsafe_allow_html=True)

        rows_html = ""
        for bkey in BAND_KEYS:
            label = BAND_LABELS_AR[bkey]
            color = BAND_COLORS_HEX[bkey]
            min_pct = thr[bkey]
            gap = result['gaps'][bkey]
            achieved = result['saudi_pct'] >= min_pct
            mark = "✅" if achieved else "❌"
            gap_text = "—" if achieved else f"+{gap} سعودي"
            rows_html += (
                f'<tr><td><span style="display:inline-block;width:12px;height:12px;background:{color};'
                f'border-radius:3px;margin-left:6px;"></span>{label}</td>'
                f'<td>{min_pct:.2f}%</td><td>{mark}</td><td>{gap_text}</td></tr>'
            )

        st.markdown(
            f'<table class="summary-table"><thead><tr>'
            f'<th>اللون</th><th>الحد الأدنى (ص)</th><th>الحالة</th><th>المطلوب للوصول</th>'
            f'</tr></thead><tbody>{rows_html}</tbody></table>',
            unsafe_allow_html=True,
        )

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # ── Services for current band ──
        st.markdown(
            f'<div class="section-title">الخدمات المتاحة في {result["services_label"]}</div>',
            unsafe_allow_html=True,
        )
        services_html = '<ul style="font-size:14px; line-height:1.9; color:#1d1d1f;">'
        for svc in result['services']:
            services_html += f'<li>{svc}</li>'
        services_html += '</ul>'
        st.markdown(
            f'<div class="card" style="border-right:6px solid {result["band_color"]};">{services_html}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # ── Formula breakdown ──
        with st.expander("📐 تفاصيل المعادلة (ص = m × ln(س) + t)"):
            import math as _math
            from modules.nitaqat_constants import ACTIVITIES as _ACT
            ln_s = _math.log(result['total']) if result['total'] > 0 else 0
            calc_rows = ""
            for bkey in BAND_KEYS:
                m = _ACT[activity][bkey]['m']
                t = _ACT[activity][bkey]['t'][int(year)]
                y = m * ln_s + t
                calc_rows += (
                    f"<tr><td>{BAND_LABELS_AR[bkey]}</td>"
                    f"<td>{m}</td><td>{t}</td>"
                    f"<td>{m} × ln({result['total']}) + {t}</td>"
                    f"<td><strong>{y:.2f}%</strong></td></tr>"
                )
            st.markdown(
                f'<table class="summary-table"><thead><tr>'
                f'<th>اللون</th><th>m</th><th>t ({year})</th><th>الحساب</th><th>ص</th>'
                f'</tr></thead><tbody>{calc_rows}</tbody></table>',
                unsafe_allow_html=True,
            )

