from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from bomcheck_toolkit.models import BomItem
from bomcheck_toolkit.utils import normalize_refdes

DEFAULT_COLUMN_CANDIDATES = {
    "refdes": ["位号", "位置号", "RefDes", "Reference", "Designator", "REFDES"],
    "value": ["规格型号", "规格", "参数", "Value", "Description", "描述"],
    "mpn": ["厂商规格型号", "厂商型号", "Manufacturer PN", "MPN", "物料编码", "料号"],
    "qty": ["数量", "Qty", "QTY"],
    "substitute": ["子项类型", "类型", "替代", "替代料", "是否替代", "Substitute", "ALT"],
    "remark": ["物料备注", "备注", "Remark", "Comment"],
}

HEADER_REFDES_VALUES = {"位号", "位置号", "REFDES", "REFERENCE", "DESIGNATOR"}


def _split_refdes_text(text: str) -> list[str]:
    normalized = str(text).strip()
    normalized = normalized.replace("，", ",").replace("、", ",").replace("；", ";")
    normalized = re.sub(r"[;\n\t]+", ",", normalized)
    normalized = normalized.replace("/", ",")
    normalized = re.sub(r"\s+", ",", normalized)
    return [p.strip() for p in normalized.split(",") if p.strip()]


def expand_refdes_text(text: str) -> list[str]:
    """Expand reference designator text into normalized RefDes values.

    Examples:
        R1,R2 -> [R1, R2]
        R1-R3 -> [R1, R2, R3]
        C101~C103 -> [C101, C102, C103]
    """
    result: list[str] = []
    for part in _split_refdes_text(text):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^([A-Za-z]+)(\d+)\s*[-~]\s*([A-Za-z]+)?(\d+)$", part)
        if m:
            p1, n1, p2, n2 = m.groups()
            p2 = p2 or p1
            if p1.upper() == p2.upper():
                start, end = int(n1), int(n2)
                if start <= end and end - start <= 1000:
                    width = max(len(n1), len(n2))
                    result.extend(f"{p1.upper()}{i:0{width}d}" for i in range(start, end + 1))
                    continue
        candidate = normalize_refdes(part)
        if candidate:
            result.append(candidate)
    # Preserve order while deduplicating.
    return list(dict.fromkeys(result))


def _find_column(columns: list[str], candidates: list[str]) -> str | None:
    normalized = {str(c).strip().lower(): c for c in columns}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in normalized:
            return normalized[key]
    # fuzzy contains
    for c in columns:
        cl = str(c).strip().lower()
        if any(candidate.strip().lower() in cl for candidate in candidates):
            return c
    return None


def _is_header_refdes(raw_ref: str) -> bool:
    return normalize_refdes(raw_ref) in {normalize_refdes(v) for v in HEADER_REFDES_VALUES}


def _is_substitute(sub_text: str, remark: str) -> bool:
    blob = f"{sub_text} {remark}".strip()
    upper = blob.upper()
    if any(k in upper for k in ["替代", "代用", "ALTERNATE", "SECOND SOURCE", "SUBSTITUTE", "ALT"]):
        return True
    return upper.strip() in {"Y", "YES", "TRUE", "1", "是"}


def _read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        # Try normal header first; then scan first 20 rows for a header containing 位号/RefDes.
        raw = pd.read_excel(path, header=None, dtype=str)
        header_row = 0
        for i in range(min(len(raw), 20)):
            row_text = " ".join(raw.iloc[i].dropna().astype(str).tolist())
            if any(k in row_text for k in ["位号", "位置号", "RefDes", "Designator"]):
                header_row = i
                break
        return pd.read_excel(path, header=header_row, dtype=str).fillna("")
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype=str).fillna("")
    raise ValueError(f"Unsupported BOM file type: {path.suffix}")


def parse_bom(path: str | Path, column_candidates: dict | None = None) -> list[BomItem]:
    candidates = column_candidates or DEFAULT_COLUMN_CANDIDATES
    df = _read_table(path)
    columns = list(df.columns)

    ref_col = _find_column(columns, candidates["refdes"])
    if not ref_col:
        raise ValueError(f"Cannot find RefDes column. Columns: {columns}")

    value_col = _find_column(columns, candidates.get("value", []))
    mpn_col = _find_column(columns, candidates.get("mpn", []))
    qty_col = _find_column(columns, candidates.get("qty", []))
    sub_col = _find_column(columns, candidates.get("substitute", []))
    remark_col = _find_column(columns, candidates.get("remark", []))

    items: list[BomItem] = []
    for idx, row in df.iterrows():
        raw_ref = str(row.get(ref_col, "")).strip()
        if _is_header_refdes(raw_ref):
            continue
        refs = expand_refdes_text(raw_ref)
        if not refs:
            continue
        qty = None
        if qty_col:
            try:
                qty = float(str(row.get(qty_col, "")).strip())
            except ValueError:
                qty = None
        value = str(row.get(value_col, "")).strip() if value_col else ""
        mpn = str(row.get(mpn_col, "")).strip() if mpn_col else ""
        remark = str(row.get(remark_col, "")).strip() if remark_col else ""
        sub_text = str(row.get(sub_col, "")).strip() if sub_col else ""
        is_sub = _is_substitute(sub_text, remark)
        items.append(BomItem(
            row_index=int(idx) + 2,
            raw_refdes=raw_ref,
            refdes_list=refs,
            qty=qty,
            value=value,
            mpn=mpn,
            is_substitute=is_sub,
            remark=remark,
            raw={str(k): row.get(k, "") for k in columns},
        ))
    return items
