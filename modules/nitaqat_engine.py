"""
AuditLink — Nitaqat Engine (Profession-based)
════════════════════════════════════════════════
Computes Saudization ratios per PROFESSION (المهنة) from GOSI data.
This matches Page 5 of the report: توطين المهن.
"""

import pandas as pd

from .profession_quotas import get_quota, get_quota_source, DEFAULT_QUOTA

SAUDI_KEYWORDS = ['سعودي', 'سعودية', 'saudi', 'السعودية']


def is_saudi(nationality_val) -> bool:
    """Return True if the nationality string indicates Saudi."""
    if pd.isna(nationality_val):
        return False
    val = str(nationality_val).strip().lower()
    return any(kw.lower() in val for kw in SAUDI_KEYWORDS)


def compute_profession_nitaqat(gosi_df, active_only=True) -> pd.DataFrame:
    """
    Compute Saudization % per profession from GOSI data.

    Args:
        gosi_df: GOSI DataFrame with 'profession', 'nationality', 'gosi_status'.
        active_only: If True, only include active employees.

    Returns:
        DataFrame with columns:
        profession, total, saudi_count, non_saudi_count, saudi_pct, status, action
    """
    if gosi_df is None or gosi_df.empty:
        return pd.DataFrame()

    df = gosi_df.copy()

    # Filter to active only
    if active_only and 'gosi_status' in df.columns:
        df = df[
            df['gosi_status'].fillna('').str.contains('نشط', na=False)
            & ~df['gosi_status'].fillna('').str.contains('غير نشط', na=False)
        ]

    if 'nationality' not in df.columns or 'profession' not in df.columns:
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    df['_is_saudi'] = df['nationality'].apply(is_saudi)

    grouped = df.groupby('profession').agg(
        total=('_is_saudi', 'count'),
        saudi_count=('_is_saudi', 'sum'),
    ).reset_index()

    grouped['non_saudi_count'] = grouped['total'] - grouped['saudi_count']
    grouped['saudi_pct'] = (grouped['saudi_count'] / grouped['total'] * 100).round(1)

    # Apply HRSD profession-specific quota
    quotas = grouped['profession'].apply(get_quota_source)
    grouped['required_pct'] = [q[0] for q in quotas]
    grouped['quota_source'] = [q[1] for q in quotas]

    # Determine status and required action using per-profession quota
    def _status_and_action(row):
        req_pct = row['required_pct']
        if row['total'] == 0:
            return 'غير متاح', '', 0

        if row['saudi_pct'] >= req_pct:
            return f'محقق النسبة ({req_pct}%) ✅', '', 0

        target_saudis = -(-row['total'] * req_pct // 100)  # ceil
        needed = max(1, int(target_saudis - row['saudi_count']))
        return (
            f'غير محقق ({req_pct}% مطلوب) ❌',
            f'يلزم توطين {needed} سعودي للوصول إلى {req_pct}%',
            needed,
        )

    results = grouped.apply(_status_and_action, axis=1, result_type='expand')
    results.columns = ['status', 'action', 'required_saudis']
    grouped = pd.concat([grouped, results], axis=1)

    return grouped.sort_values('saudi_pct', ascending=True).reset_index(drop=True)


def get_nitaqat_summary(nitaqat_df: pd.DataFrame) -> dict:
    """Return overall profession Saudization statistics."""
    if nitaqat_df is None or nitaqat_df.empty:
        return {}

    total_emp = int(nitaqat_df['total'].sum())
    total_saudi = int(nitaqat_df['saudi_count'].sum())
    total_non_saudi = int(nitaqat_df['non_saudi_count'].sum())
    overall_pct = round(total_saudi / total_emp * 100, 1) if total_emp > 0 else 0.0

    achieved = int(nitaqat_df['status'].str.contains('محقق النسبة', na=False).sum())
    not_achieved = len(nitaqat_df) - achieved
    total_needed = int(nitaqat_df['required_saudis'].sum())

    return {
        'total_employees': total_emp,
        'total_saudi': total_saudi,
        'total_non_saudi': total_non_saudi,
        'overall_pct': overall_pct,
        'total_professions': len(nitaqat_df),
        'professions_achieved': achieved,
        'professions_not_achieved': not_achieved,
        'total_saudis_needed': total_needed,
    }
