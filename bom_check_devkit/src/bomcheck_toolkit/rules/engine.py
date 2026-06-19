from __future__ import annotations

from collections import defaultdict
import re

from bomcheck_toolkit.models import BomItem, CheckIssue, PdfRef, RefMatch
from bomcheck_toolkit.utils import contains_any


def build_bom_index(items: list[BomItem]) -> dict[str, list[BomItem]]:
    idx: dict[str, list[BomItem]] = defaultdict(list)
    for item in items:
        for ref in item.refdes_list:
            idx[ref].append(item)
    return dict(idx)


def build_pdf_index(refs: list[PdfRef]) -> dict[str, list[PdfRef]]:
    idx: dict[str, list[PdfRef]] = defaultdict(list)
    for ref in refs:
        idx[ref.refdes].append(ref)
    return dict(idx)


def classify_pdf_only(refdes: str, pdf_refs: list[PdfRef], nc_keywords: list[str]) -> tuple[str, str, str]:
    context = " ".join(r.context_text for r in pdf_refs)
    if refdes.startswith("TP"):
        return "PDF_ONLY_TESTPOINT", "ignore", "测试点默认不进 BOM"
    if refdes.startswith("ID"):
        if contains_any(context, ["MARK", "BADMARK", "MARKPOINT", "MARK点", "BADMARK点", "NC"]):
            return "PDF_ONLY_MARKPOINT", "ignore", "Markpoint/Badmark 默认不进 BOM"
    if _looks_like_ic_pin_name(refdes, context):
        return "PDF_ONLY_PIN_NAME", "ignore", "疑似 IC 引脚名或功能脚，不作为漏 BOM"
    if contains_any(context, nc_keywords) or any(r.is_nc_context for r in pdf_refs):
        return "PDF_ONLY_NC", "info", "PDF 附近标注 NC/DNP/不贴，BOM 没有通常合理"
    return "PDF_ONLY_SUSPECT", "warning", "PDF 有该位号，但 BOM 中没有，也未发现 NC/DNP/TP/Mark 证据"


def _item_blob(item: BomItem) -> str:
    return f"{item.value} {item.mpn} {item.remark}"


def _extract_tvs_model(text: str) -> str | None:
    t = str(text).upper().replace(" ", "")
    m = re.search(r"SMBJ\d+(?:\.\d+)?C?A", t)
    if m:
        return m.group(0)
    m = re.search(r"PESD[A-Z0-9\.\-]+", t)
    if m:
        return m.group(0)
    return None


def _refdes_prefix(refdes: str) -> str:
    m = re.match(r"([A-Z]+)", refdes.upper())
    return m.group(1) if m else ""


def _looks_like_ic_pin_name(refdes: str, context: str) -> bool:
    prefix = _refdes_prefix(refdes)
    if prefix not in {"BAT", "SW"}:
        return False
    has_ic_ref = re.search(r"\bU\d+[A-Z]?\b", context.upper()) is not None
    has_ic_model = re.search(r"\b[A-Z]{2,}\d{3,}[A-Z0-9/\.-]*\b", context.upper()) is not None
    pin_keywords = ["VIN", "VBUS", "SYS1", "SYS2", "SCL", "SDA", "GND", "BTST", "FB"]
    pin_hits = sum(1 for keyword in pin_keywords if contains_any(context, [keyword]))
    return ((has_ic_ref or has_ic_model) and pin_hits >= 1) or pin_hits >= 3


def _normalize_value_token(value: str) -> str:
    token = value.upper().replace(" ", "").replace("µ", "U").replace("μ", "U")
    token = token.replace("OHM", "R").replace("Ω", "R")
    token = token.replace("KR", "K").replace("MR", "M")
    return token


def _extract_passive_values(text: str, prefix: str) -> set[str]:
    source = str(text).replace("µ", "u").replace("μ", "u")
    if prefix == "R":
        pattern = r"\b\d+(?:\.\d+)?\s*(?:MΩ|KΩ|Ω|MOHM|KOHM|OHM|MR|KR|R|K|M)\b"
    elif prefix == "C":
        pattern = r"\b\d+(?:\.\d+)?\s*(?:PF|NF|UF|uF|MF)\b"
    elif prefix == "L":
        pattern = r"\b\d+(?:\.\d+)?\s*(?:NH|UH|uH|MH)\b"
    else:
        return set()
    return {_normalize_value_token(m.group(0)) for m in re.finditer(pattern, source, re.IGNORECASE)}


def check_value_mismatch(refdes: str, bom_items: list[BomItem], pdf_refs: list[PdfRef]) -> list[CheckIssue]:
    issues: list[CheckIssue] = []
    if not bom_items or not pdf_refs:
        return issues
    pdf_context = " ".join(r.context_text for r in pdf_refs)
    bom_blob = " ".join(_item_blob(i) for i in bom_items)

    if refdes.startswith("TVS"):
        bom_tvs = _extract_tvs_model(bom_blob)
        pdf_tvs = _extract_tvs_model(pdf_context)
        if bom_tvs and pdf_tvs and bom_tvs != pdf_tvs:
            issues.append(CheckIssue(
                severity="error",
                rule_id="CRITICAL_TVS_MISMATCH",
                title="TVS 型号或关键参数与 PDF 不一致",
                refdes=refdes,
                bom_row=bom_items[0].row_index,
                pdf_page=pdf_refs[0].page_index + 1,
                evidence=f"BOM={bom_tvs}, PDF={pdf_tvs}",
                suggestion="确认原理图是否未更新，或 BOM 是否误改。",
            ))
            return issues

    prefix = _refdes_prefix(refdes)
    if prefix in {"R", "C", "L"}:
        bom_values = _extract_passive_values(bom_blob, prefix)
        pdf_values = _extract_passive_values(pdf_context, prefix)
        if bom_values and pdf_values and bom_values.isdisjoint(pdf_values):
            issues.append(CheckIssue(
                severity="warning",
                rule_id="VALUE_MISMATCH",
                title="BOM 与 PDF 附近文本可能不一致",
                refdes=refdes,
                bom_row=bom_items[0].row_index,
                pdf_page=pdf_refs[0].page_index + 1,
                evidence=f"BOM values={sorted(bom_values)}; PDF nearby values={sorted(pdf_values)}",
                suggestion="人工确认该器件型号/参数是否一致。",
            ))
    return issues


def run_rules(items: list[BomItem], pdf_refs: list[PdfRef], nc_keywords: list[str] | None = None) -> tuple[list[RefMatch], list[CheckIssue]]:
    nc_keywords = nc_keywords or ["NC", "DNP", "DNI", "OPEN", "不贴", "空贴", "选贴", "预留"]
    bom_idx = build_bom_index(items)
    pdf_idx = build_pdf_index(pdf_refs)
    all_refs = sorted(set(bom_idx) | set(pdf_idx))

    matches: list[RefMatch] = []
    issues: list[CheckIssue] = []

    for ref in sorted(bom_idx):
        rows = bom_idx[ref]
        if len(rows) > 1:
            if not any(i.is_substitute for i in rows):
                issues.append(CheckIssue(
                    severity="error",
                    rule_id="DUPLICATE_STANDARD_REFDES",
                    title="同一位号出现在多个标准件 BOM 行",
                    refdes=ref,
                    bom_row=rows[0].row_index,
                    evidence="; ".join(f"row {i.row_index}: {i.mpn or i.value}" for i in rows),
                    suggestion="确认是否重复下单或 BOM 合并错误。",
                ))

    for ref in all_refs:
        b = bom_idx.get(ref, [])
        p = pdf_idx.get(ref, [])
        if b and p:
            status = "OK" if len(p) == 1 else "MULTI_PDF_MATCH"
            matches.append(RefMatch(ref, b, p, status, confidence=max(r.confidence for r in p)))
            issues.extend(check_value_mismatch(ref, b, p))
        elif b and not p:
            matches.append(RefMatch(ref, b, [], "BOM_ONLY", 0.0))
            issues.append(CheckIssue(
                severity="error",
                rule_id="BOM_ONLY_REFDES",
                title="BOM 位号在 PDF 中找不到",
                refdes=ref,
                bom_row=b[0].row_index,
                evidence=f"BOM row {b[0].row_index}: {b[0].raw_refdes}",
                suggestion="检查 BOM 是否多料，或 PDF 是否不是对应版本。",
            ))
        elif p and not b:
            status, severity, note = classify_pdf_only(ref, p, nc_keywords)
            matches.append(RefMatch(ref, [], p, status, confidence=max(r.confidence for r in p)))
            if severity != "ignore":
                issues.append(CheckIssue(
                    severity=severity,  # type: ignore[arg-type]
                    rule_id=status,
                    title=note,
                    refdes=ref,
                    pdf_page=p[0].page_index + 1,
                    evidence=p[0].context_text[:180],
                    suggestion="若为 NC/DNP/测试点/Mark 点，可忽略；否则确认是否漏 BOM。",
                ))
    return matches, issues
