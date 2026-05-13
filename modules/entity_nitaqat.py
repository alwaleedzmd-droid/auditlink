"""
AuditLink — Entity Nitaqat Engine (نطاق المنشأة)
═══════════════════════════════════════════════════
احتساب لون النطاق للمنشأة وفق الدليل الإجرائي لبرنامج نطاقات المطور 2026.

ص = m × ln(س) + t
حيث س = إجمالي العمالة، m و t من جدول النشاط × اللون × السنة.
"""

import math
import pandas as pd

from .nitaqat_constants import (
    ACTIVITIES, BAND_KEYS, BAND_LABELS_AR, BAND_COLORS_HEX,
    BAND_SERVICES, YEARS,
)


def _count_saudi_active(gosi_df: pd.DataFrame) -> tuple[int, int]:
    """Return (saudi_active, total_active) from GOSI snapshot."""
    if gosi_df is None or gosi_df.empty:
        return 0, 0

    df = gosi_df.copy()
    if 'gosi_status' in df.columns:
        df = df[
            df['gosi_status'].fillna('').str.contains('نشط', na=False)
            & ~df['gosi_status'].fillna('').str.contains('غير نشط', na=False)
        ]

    if df.empty or 'nationality' not in df.columns:
        return 0, 0

    saudi_kw = ['سعودي', 'سعودية', 'saudi', 'السعودية']
    nat = df['nationality'].fillna('').astype(str).str.lower()
    is_saudi = nat.apply(lambda v: any(k.lower() in v for k in saudi_kw))
    return int(is_saudi.sum()), int(len(df))


def compute_band_thresholds(activity: str, total_employees: int, year: int) -> dict:
    """
    Return dict { band_key: threshold_pct } for the 4 colored bands.
    Threshold for 'red' is 0 (any value below low_green).
    """
    if activity not in ACTIVITIES:
        raise ValueError(f"Unknown activity: {activity}")
    if year not in YEARS:
        raise ValueError(f"Year must be one of {YEARS}, got {year}")
    if total_employees <= 0:
        return {b: 0.0 for b in BAND_KEYS}

    ln_s = math.log(total_employees)
    bands = ACTIVITIES[activity]
    return {
        band: round(bands[band]["m"] * ln_s + bands[band]["t"][year], 2)
        for band in BAND_KEYS
    }


def assign_band(saudi_pct: float, thresholds: dict) -> str:
    """Given the entity's Saudization % and band thresholds, return band key."""
    if saudi_pct < thresholds["low_green"]:
        return "red"
    if saudi_pct < thresholds["mid_green"]:
        return "low_green"
    if saudi_pct < thresholds["high_green"]:
        return "mid_green"
    if saudi_pct < thresholds["platinum"]:
        return "high_green"
    return "platinum"


def saudis_needed_for_band(target_pct: float, total_employees: int, current_saudi: int) -> int:
    """How many additional Saudis to reach target_pct (keeping total fixed)."""
    if total_employees <= 0:
        return 0
    required = math.ceil((target_pct / 100.0) * total_employees)
    return max(0, required - current_saudi)


def simulate_band(
    saudi: int, non_saudi: int, activity: str, year: int,
) -> dict:
    """
    Recompute band given raw saudi/non_saudi counts (without a GOSI file).
    Used for what-if scenarios (adding/removing employees).
    """
    saudi = max(0, int(saudi))
    non_saudi = max(0, int(non_saudi))
    total = saudi + non_saudi
    pct = round(saudi / total * 100, 2) if total > 0 else 0.0
    thresholds = compute_band_thresholds(activity, total, year)
    band = assign_band(pct, thresholds) if total > 0 else "red"
    return {
        "activity": activity,
        "year": year,
        "total": total,
        "saudi": saudi,
        "non_saudi": non_saudi,
        "saudi_pct": pct,
        "thresholds": thresholds,
        "band": band,
        "band_label_ar": BAND_LABELS_AR[band],
        "band_color": BAND_COLORS_HEX[band],
    }


def compute_entity_band(gosi_df: pd.DataFrame, activity: str, year: int) -> dict:
    """
    Main entry. Returns full computation result:
    {
        total, saudi, non_saudi, saudi_pct,
        thresholds: {low_green, mid_green, high_green, platinum},
        band: 'low_green' | ...,
        band_label_ar, band_color,
        gaps: { band_key: saudis_needed },
        services: [...],
    }
    """
    saudi, total = _count_saudi_active(gosi_df)
    non_saudi = total - saudi
    pct = round(saudi / total * 100, 2) if total > 0 else 0.0

    thresholds = compute_band_thresholds(activity, total, year)
    band = assign_band(pct, thresholds)

    gaps = {
        b: saudis_needed_for_band(thresholds[b], total, saudi)
        for b in BAND_KEYS
    }

    return {
        "activity": activity,
        "year": year,
        "total": total,
        "saudi": saudi,
        "non_saudi": non_saudi,
        "saudi_pct": pct,
        "thresholds": thresholds,
        "band": band,
        "band_label_ar": BAND_LABELS_AR[band],
        "band_color": BAND_COLORS_HEX[band],
        "gaps": gaps,
        "services": BAND_SERVICES[band]["services"],
        "services_label": BAND_SERVICES[band]["label"],
    }
