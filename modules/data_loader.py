"""
AuditLink — Data Loader Module
═══════════════════════════════
Loads and normalizes the 4 source Excel files.
Common key: national_id (رقم الهوية / رقم الإقامة / Iqama No)
"""

import re
import pandas as pd


def normalize_id(series: pd.Series) -> pd.Series:
    """Clean ID numbers: remove .0, whitespace, etc."""
    return (
        series.astype(str)
              .str.strip()
              .str.replace(r'\.0$', '', regex=True)
              .str.replace(r'\s+', '', regex=True)
    )


_AR_TASHKEEL_RE = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]')
_INVISIBLE_RE = re.compile(r'[\u00A0\u200B-\u200F\u202A-\u202E\u2060-\u206F\uFEFF]')
_NON_WORD_RE = re.compile(r'[\s\-_/\\()\[\].,:;|]+')
_SAUDI_ID_RE = re.compile(r'^[1-4]\d{9}$')


def _norm_header(s: str) -> str:
    """Normalize a column header for loose matching.

    Strips invisible format/bidi characters common in government exports
    (RLM, LRM, ZWSP, BOM, NBSP…), Arabic tashkeel and tatweel, then
    normalizes letter forms (أ/إ/آ→ا, ى→ي, ة→ه) and removes separators.
    """
    s = str(s).strip().lower()
    s = _INVISIBLE_RE.sub('', s)
    s = _AR_TASHKEEL_RE.sub('', s)
    s = (s.replace('أ', 'ا')
           .replace('إ', 'ا')
           .replace('آ', 'ا')
           .replace('ٱ', 'ا')
           .replace('ى', 'ي')
           .replace('ئ', 'ي')
           .replace('ؤ', 'و')
           .replace('ة', 'ه'))
    s = _NON_WORD_RE.sub('', s)
    return s


def _find_id_column_by_values(df: pd.DataFrame, exclude: set = None) -> str | None:
    """Heuristic fallback: find a column whose values look like Saudi IDs.

    A Saudi National ID or Iqama is a 10-digit number starting with 1-4.
    Returns the name of the column with the highest match ratio among
    non-null values, requiring at least 70% to match. Used when header
    auto-detection fails entirely (e.g. corrupted headers, unknown language).
    """
    exclude = exclude or set()
    best_col = None
    best_ratio = 0.0
    for col in df.columns:
        if col in exclude:
            continue
        vals = df[col].dropna().astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        if len(vals) == 0:
            continue
        matches = vals.str.match(_SAUDI_ID_RE).sum()
        ratio = matches / len(vals)
        if ratio >= 0.7 and ratio > best_ratio:
            best_ratio = ratio
            best_col = col
    return best_col


def _detect_columns(df: pd.DataFrame, mapping: dict) -> dict:
    """Auto-detect column names from aliases list.

    Matching is layered for robustness against real-world header variants:
      1. exact equality (after strip+lower)
      2. normalized equality (Arabic-aware, punctuation-insensitive)
      3. normalized substring (either direction) — a column named
         "رقم الهوية / الإقامة" still matches the alias "رقم الهوية".
    """
    result = {}
    cols = list(df.columns)
    norm_cols = {c: _norm_header(c) for c in cols}
    used = set()

    for standard_name, aliases in mapping.items():
        norm_aliases = [(a, _norm_header(a)) for a in aliases]
        found = None

        for alias, _ in norm_aliases:
            for c in cols:
                if c in used:
                    continue
                if c.strip().lower() == alias.strip().lower():
                    found = c
                    break
            if found:
                break

        if not found:
            for _, na in norm_aliases:
                for c in cols:
                    if c in used:
                        continue
                    if norm_cols[c] == na:
                        found = c
                        break
                if found:
                    break

        if not found:
            for _, na in norm_aliases:
                if not na:
                    continue
                for c in cols:
                    if c in used:
                        continue
                    nc = norm_cols[c]
                    if na in nc or nc in na:
                        found = c
                        break
                if found:
                    break

        if found:
            result[found] = standard_name
            used.add(found)

    return result


def _apply_mapping(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    """Rename columns and collapse any accidental duplicates.

    If the source file already contains a column matching a standard name
    (e.g. both 'رقم الهوية' and a literal 'national_id'), `df.rename` would
    produce two columns with the same name. Keep the one from the mapping
    (which came from detection) and drop the pre-existing duplicate.
    """
    keep = set(col_map.values())
    df = df.drop(columns=[c for c in df.columns if c in keep and c not in col_map], errors='ignore')
    return df.rename(columns=col_map)


def _require_id(df: pd.DataFrame, file_label: str) -> pd.DataFrame:
    """Assert that `national_id` exists and normalize it."""
    if 'national_id' not in df.columns:
        raise ValueError(
            f"تعذّر التعرف على عمود رقم الهوية/الإقامة في ملف {file_label}. "
            f"الأعمدة الموجودة: {list(df.columns)}"
        )
    df['national_id'] = normalize_id(df['national_id'])
    return df


def _ensure_id_mapping(df: pd.DataFrame, col_map: dict) -> dict:
    """If alias detection missed `national_id`, fall back to value-based scan."""
    if 'national_id' in col_map.values():
        return col_map
    id_col = _find_id_column_by_values(df, exclude=set(col_map.keys()))
    if id_col is not None:
        col_map[id_col] = 'national_id'
    return col_map


# ─────────────────────────────────────────────────
#  GOSI (التأمينات الاجتماعية)
# ─────────────────────────────────────────────────
def load_gosi_file(file) -> pd.DataFrame:
    """
    Columns: رقم الهوية, اسم المشترك, حالة المشترك, الجنسية, الجنس, المهنة, تاريخ الإلتحاق
    """
    df = pd.read_excel(file, dtype=str)
    df.columns = df.columns.str.strip()

    col_map = _detect_columns(df, {
        'national_id':   ['رقم الهوية', 'رقم الإقامة', 'Iqama No', 'national_id'],
        'name':          ['اسم المشترك', 'الاسم', 'Name', 'name'],
        'gosi_status':   ['حالة المشترك', 'الحالة', 'Status'],
        'nationality':   ['الجنسية', 'Nationality'],
        'gender':        ['الجنس', 'Gender'],
        'profession':    ['المهنة', 'Profession', 'Job Title'],
        'join_date':     ['تاريخ الإلتحاق', 'تاريخ التسجيل', 'Join Date'],
    })
    col_map = _ensure_id_mapping(df, col_map)

    df = _require_id(_apply_mapping(df, col_map), 'GOSI (التأمينات)')
    df['_in_gosi'] = True
    return df


# ─────────────────────────────────────────────────
#  Medical Insurance / CCHI (التأمين الصحي)
# ─────────────────────────────────────────────────
def load_medical_file(file) -> pd.DataFrame:
    """
    Columns: Iqama No, Member Name, Inception, Class, Risk No, Relation,
             Gender, Staff No, Type, Endt No, Premium, DOB, CCHI Si, National
    """
    df = pd.read_excel(file, dtype=str)
    df.columns = df.columns.str.strip()

    col_map = _detect_columns(df, {
        'national_id':      ['Iqama No', 'رقم الهوية', 'رقم الإقامة', 'رقم الاقامة', 'national_id'],
        'name':             ['Member Name', 'الاسم', 'Name', 'name'],
        'inception_date':   ['Inception', 'تاريخ البداية'],
        'insurance_class':  ['Class', 'الفئة'],
        'relation':         ['Relation', 'العلاقة'],
        'gender':           ['Gender', 'الجنس'],
        'staff_no':         ['Staff No', 'رقم الموظف'],
        'staff_type':       ['Type', 'النوع'],
        'premium':          ['Premium', 'القسط'],
        'dob':              ['DOB', 'تاريخ الميلاد'],
        'cchi_no':          ['CCHI Si', 'CCHI'],
        'nationality':      ['National', 'الجنسية'],
    })
    col_map = _ensure_id_mapping(df, col_map)

    df = _require_id(_apply_mapping(df, col_map), 'التأمين الصحي (Medical)')
    df['_in_medical'] = True
    return df


# ─────────────────────────────────────────────────
#  Muqeem (مقيم)
# ─────────────────────────────────────────────────
def load_muqeem_file(file) -> pd.DataFrame:
    """
    Columns: رقم الاقامة, الاسم, الجنس, الجنسية, المهنة, رقم الجواز,
             اصدار الاقامة, انتهاء الاقامة, تاريخ الميلاد, رقم صاحب العمل
    """
    df = pd.read_excel(file, dtype=str)
    df.columns = df.columns.str.strip()

    col_map = _detect_columns(df, {
        'national_id':     ['رقم الاقامة', 'رقم الإقامة', 'رقم الهوية', 'national_id'],
        'name':            ['الاسم', 'Name', 'name'],
        'gender':          ['الجنس', 'Gender'],
        'nationality':     ['الجنسية', 'Nationality'],
        'profession':      ['المهنة', 'Profession'],
        'passport_no':     ['رقم الجواز', 'Passport'],
        'iqama_issue':     ['اصدار الاقامة', 'Iqama Issue'],
        'iqama_expiry':    ['انتهاء الاقامة', 'Iqama Expiry'],
        'dob':             ['تاريخ الميلاد', 'DOB'],
        'sponsor_no':      ['رقم صاحب العمل', 'Sponsor'],
    })
    col_map = _ensure_id_mapping(df, col_map)

    df = _require_id(_apply_mapping(df, col_map), 'مقيم (Muqeem)')
    df['_in_muqeem'] = True
    return df


# ─────────────────────────────────────────────────
#  Payroll (الرواتب)
# ─────────────────────────────────────────────────
def load_payroll_file(file) -> pd.DataFrame:
    """
    Columns: رقم الهوية, Employees Number, ARABIC NAME, NAME,
             START UP DATE, الوظيفة, الشعبة, DEGREE
    """
    df = pd.read_excel(file, dtype=str)
    df.columns = df.columns.str.strip()

    col_map = _detect_columns(df, {
        'national_id':       ['رقم الهوية', 'رقم الإقامة', 'Iqama No', 'national_id'],
        'employee_number':   ['Employees Number', 'رقم الموظف', 'Employee Number'],
        'name_ar':           ['ARABIC NAME', 'الاسم العربي'],
        'name':              ['NAME', 'الاسم', 'name'],
        'start_date':        ['START UP DATE', 'تاريخ البداية'],
        'job_title':         ['الوظيفة', 'Job Title', 'Position'],
        'department':        ['الشعبة', 'القسم', 'Section', 'Department'],
        'degree':            ['DEGREE', 'الدرجة'],
    })
    col_map = _ensure_id_mapping(df, col_map)

    df = _require_id(_apply_mapping(df, col_map), 'الرواتب (Payroll)')
    df['_in_payroll'] = True
    return df
