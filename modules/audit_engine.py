"""
AuditLink — Audit Engine
═══════════════════════════
5 cross-reference comparison rules matching the real report format.
Each "page" is a simple set-difference on national_id between two systems.
"""

import pandas as pd


# ─────────────────────────────────────────────────
#  Page Metadata
# ─────────────────────────────────────────────────
AUDIT_PAGES = {
    'page1': {
        'title': 'موجود في التأمين الصحي غير موجود في التأمينات الاجتماعية',
        'title_short': 'التأمين الصحي ∉ التأمينات',
        'icon': '🏥',
        'color': '#ff453a',
    },
    'page2': {
        'title': 'موجود في التأمينات الاجتماعية غير موجود في التأمين الطبي',
        'title_short': 'التأمينات ∉ التأمين الصحي',
        'icon': '📋',
        'color': '#ff9f0a',
    },
    'page3': {
        'title': 'موجود في الرواتب غير موجود في التأمينات الاجتماعية',
        'title_short': 'الرواتب ∉ التأمينات',
        'icon': '💰',
        'color': '#ff453a',
    },
    'page4': {
        'title': 'موجود في التأمينات الاجتماعية غير موجود في الرواتب',
        'title_short': 'التأمينات ∉ الرواتب',
        'icon': '📋',
        'color': '#ff9f0a',
    },
    'page5': {
        'title': 'غير نشط في التأمينات الاجتماعية وموجود في الرواتب',
        'title_short': 'غير نشط ∩ الرواتب',
        'icon': '🚫',
        'color': '#ff453a',
    },
    'page6': {
        'title': 'غير نشط في التأمينات الاجتماعية وموجود في التأمين الطبي',
        'title_short': 'غير نشط ∩ الطبي',
        'icon': '🚫',
        'color': '#ff453a',
    },
}


def _id_series(df):
    """Return the national_id column as a 1-D Series, or None if unavailable.

    Guards against the edge case where a DataFrame ends up with two columns
    named `national_id` — `df['national_id']` would then return a DataFrame,
    causing `.isin()` to fail downstream. In that case we take the first
    column to keep the audit running.
    """
    if df is None or df.empty or 'national_id' not in df.columns:
        return None
    col = df['national_id']
    if isinstance(col, pd.DataFrame):
        col = col.iloc[:, 0]
    return col


def _get_ids(df) -> set:
    """Get set of national_ids from a DataFrame."""
    s = _id_series(df)
    if s is None:
        return set()
    return set(s.dropna().unique())


def _has_id_col(df) -> bool:
    """Check that DataFrame is valid and has a usable national_id column."""
    return _id_series(df) is not None


# ─────────────────────────────────────────────────
#  Page 1: Medical ∉ GOSI
# ─────────────────────────────────────────────────
def page1_medical_not_in_gosi(medical_df, gosi_df):
    """صفحة 1: موجود في التأمين الصحي غير موجود في التأمينات الاجتماعية"""
    med_ids = _id_series(medical_df)
    if med_ids is None or not _has_id_col(gosi_df):
        return None  # unavailable — needs both files

    gosi_ids = _get_ids(gosi_df)
    result = medical_df[~med_ids.isin(gosi_ids)].copy()

    if result.empty:
        return result

    def _action(row):
        relation = str(row.get('relation', '1')).strip()
        if relation != '1':
            return 'تابعين لا يلزم اجراء'
        return 'لا يلزم اجراء'

    result['الإجراء المطلوب'] = result.apply(_action, axis=1)
    return result.reset_index(drop=True)


# ─────────────────────────────────────────────────
#  Page 2: GOSI ∉ Medical
# ─────────────────────────────────────────────────
def page2_gosi_not_in_medical(gosi_df, medical_df):
    """صفحة 2: موجود في التأمينات الاجتماعية غير موجود في التأمين الطبي"""
    gosi_ids = _id_series(gosi_df)
    if gosi_ids is None or not _has_id_col(medical_df):
        return None

    medical_ids = _get_ids(medical_df)
    result = gosi_df[~gosi_ids.isin(medical_ids)].copy()

    if result.empty:
        return result

    def _action(row):
        status = str(row.get('gosi_status', '')).strip()
        if 'غير نشط' in status:
            return 'لا يلزم اجراء (غير نشط في التأمينات)'
        return 'يلزم اجراء (اضافة في التأمين الطبي)'

    result['الإجراء المطلوب'] = result.apply(_action, axis=1)
    return result.reset_index(drop=True)


# ─────────────────────────────────────────────────
#  Page 3: Payroll ∉ GOSI
# ─────────────────────────────────────────────────
def page3_payroll_not_in_gosi(payroll_df, gosi_df):
    """صفحة 3: موجود في الرواتب غير موجود في التأمينات الاجتماعية"""
    pay_ids = _id_series(payroll_df)
    if pay_ids is None or not _has_id_col(gosi_df):
        return None

    gosi_ids = _get_ids(gosi_df)
    result = payroll_df[~pay_ids.isin(gosi_ids)].copy()

    if result.empty:
        return result

    def _action(row):
        return 'لا يلزم اجراء'

    result['الإجراء المطلوب'] = result.apply(_action, axis=1)
    return result.reset_index(drop=True)


# ─────────────────────────────────────────────────
#  Page 4: GOSI ∉ Payroll
# ─────────────────────────────────────────────────
def page4_gosi_not_in_payroll(gosi_df, payroll_df):
    """صفحة 4: موجود في التأمينات الاجتماعية غير موجود في الرواتب"""
    gosi_ids = _id_series(gosi_df)
    if gosi_ids is None or not _has_id_col(payroll_df):
        return None

    payroll_ids = _get_ids(payroll_df)
    result = gosi_df[~gosi_ids.isin(payroll_ids)].copy()

    if result.empty:
        return result

    def _action(row):
        status = str(row.get('gosi_status', '')).strip()
        if 'غير نشط' in status:
            return 'لا يلزم اجراء (غير نشط في التأمينات)'
        return 'يلزم اجراء (اضافة في الرواتب)'

    result['الإجراء المطلوب'] = result.apply(_action, axis=1)
    return result.reset_index(drop=True)


# ─────────────────────────────────────────────────
#  Page 5: Inactive in GOSI ∩ Payroll — should be excluded from Payroll
# ─────────────────────────────────────────────────
def page5_inactive_in_payroll(gosi_df, payroll_df):
    """صفحة 5: غير نشط في التأمينات وموجود في الرواتب — يلزم الاستبعاد من الرواتب"""
    gosi_ids = _id_series(gosi_df)
    pay_ids = _id_series(payroll_df)
    if gosi_ids is None or pay_ids is None:
        return None

    status_col = gosi_df.get('gosi_status')
    if status_col is None:
        return pd.DataFrame()

    inactive_mask = status_col.astype(str).str.contains('غير نشط', na=False)
    inactive_ids = set(gosi_ids[inactive_mask].dropna().unique())
    if not inactive_ids:
        return pd.DataFrame()

    result = payroll_df[pay_ids.isin(inactive_ids)].copy()
    if result.empty:
        return result

    result['الإجراء المطلوب'] = 'الاستبعاد من الرواتب'
    return result.reset_index(drop=True)


# ─────────────────────────────────────────────────
#  Page 6: Inactive in GOSI ∩ Medical — should be excluded from Medical
# ─────────────────────────────────────────────────
def page6_inactive_in_medical(gosi_df, medical_df):
    """صفحة 6: غير نشط في التأمينات وموجود في التأمين الطبي — يلزم الاستبعاد من التأمين الطبي"""
    gosi_ids = _id_series(gosi_df)
    med_ids = _id_series(medical_df)
    if gosi_ids is None or med_ids is None:
        return None

    status_col = gosi_df.get('gosi_status')
    if status_col is None:
        return pd.DataFrame()

    inactive_mask = status_col.astype(str).str.contains('غير نشط', na=False)
    inactive_ids = set(gosi_ids[inactive_mask].dropna().unique())
    if not inactive_ids:
        return pd.DataFrame()

    result = medical_df[med_ids.isin(inactive_ids)].copy()
    if result.empty:
        return result

    result['الإجراء المطلوب'] = 'الاستبعاد من التأمين الطبي'
    return result.reset_index(drop=True)


# ─────────────────────────────────────────────────
#  Run All Audits
# ─────────────────────────────────────────────────
def run_all_audits(gosi_df=None, medical_df=None, muqeem_df=None, payroll_df=None) -> dict:
    """
    Run all 6 audit page comparisons.
    Returns dict of {page_key: DataFrame or None}.
    """
    return {
        'page1': page1_medical_not_in_gosi(medical_df, gosi_df),
        'page2': page2_gosi_not_in_medical(gosi_df, medical_df),
        'page3': page3_payroll_not_in_gosi(payroll_df, gosi_df),
        'page4': page4_gosi_not_in_payroll(gosi_df, payroll_df),
        'page5': page5_inactive_in_payroll(gosi_df, payroll_df),
        'page6': page6_inactive_in_medical(gosi_df, medical_df),
    }


PAGE_REQUIREMENTS = {
    'page1': ('التأمين الصحي', 'التأمينات'),
    'page2': ('التأمينات', 'التأمين الصحي'),
    'page3': ('الرواتب', 'التأمينات'),
    'page4': ('التأمينات', 'الرواتب'),
    'page5': ('التأمينات', 'الرواتب'),
    'page6': ('التأمينات', 'التأمين الصحي'),
}


PAGE_KEYS = ['page1', 'page2', 'page3', 'page4', 'page5', 'page6']


def get_audit_summary(results: dict) -> dict:
    """
    Generate summary counts for each page.

    A page with `None` result means one of its required files was not uploaded
    and the comparison is unavailable (distinct from "zero mismatches").
    """
    summary = {}
    for key in PAGE_KEYS:
        df = results.get(key)
        if df is None:
            summary[key] = {'available': False, 'total': 0, 'actions': {}}
            continue
        if not df.empty and 'الإجراء المطلوب' in df.columns:
            action_counts = df['الإجراء المطلوب'].value_counts().to_dict()
            total = len(df)
        else:
            action_counts = {}
            total = 0
        summary[key] = {'available': True, 'total': total, 'actions': action_counts}
    return summary
