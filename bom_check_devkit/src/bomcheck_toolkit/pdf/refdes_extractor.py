from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import fitz  # PyMuPDF

from bomcheck_toolkit.models import PdfRef, PdfTextToken
from bomcheck_toolkit.utils import contains_any, normalize_refdes

DEFAULT_PREFIXES = [
    "TVS", "ESD", "ANT", "LED", "BAT", "NTC", "FUSE", "FB", "TP", "SW", "ID", "JP", "CN",
    "J", "U", "R", "C", "L", "Q", "D", "Y", "X",
]


def build_refdes_regex(prefixes: list[str] | None = None) -> re.Pattern:
    prefixes = prefixes or DEFAULT_PREFIXES
    prefixes_sorted = sorted(prefixes, key=len, reverse=True)
    p = "|".join(re.escape(x) for x in prefixes_sorted)
    return re.compile(rf"(?<![A-Za-z0-9_])({p})([0-9]+[A-Za-z]?)(?![A-Za-z0-9_])", re.IGNORECASE)


def build_embedded_regex(prefixes: list[str] | None = None) -> re.Pattern:
    prefixes = prefixes or DEFAULT_PREFIXES
    prefixes_sorted = sorted(prefixes, key=len, reverse=True)
    p = "|".join(re.escape(x) for x in prefixes_sorted)
    return re.compile(rf"^({p})([0-9]+)", re.IGNORECASE)


def is_likely_frame_token(text: str, page_width: float, page_height: float, bbox: tuple[float, float, float, float]) -> bool:
    x0, y0, x1, y1 = bbox
    t = text.strip()
    if t in {"1", "2", "3", "4", "5", "A", "B", "C", "D"}:
        if x0 < 30 or y0 < 30 or x1 > page_width - 30 or y1 > page_height - 30:
            return True
    # bottom-right title block
    if x0 > page_width * 0.70 and y0 > page_height * 0.80:
        return True
    if y0 < 10 or y1 > page_height - 10:
        return True
    return False


def get_words(page: fitz.Page) -> list[PdfTextToken]:
    words = page.get_text("words")
    tokens: list[PdfTextToken] = []
    for w in words:
        x0, y0, x1, y1, text = w[:5]
        bbox = (float(x0), float(y0), float(x1), float(y1))
        if is_likely_frame_token(str(text), float(page.rect.width), float(page.rect.height), bbox):
            continue
        tokens.append(PdfTextToken(page.number, str(text), bbox))
    return tokens


def context_for_bbox(tokens: list[PdfTextToken], bbox: tuple[float, float, float, float], x_margin: float = 80, y_margin: float = 60) -> str:
    x0, y0, x1, y1 = bbox
    cx0, cy0, cx1, cy1 = x0 - x_margin, y0 - y_margin, x1 + x_margin, y1 + y_margin
    nearby = []
    for tok in tokens:
        tx0, ty0, tx1, ty1 = tok.bbox
        if tx1 >= cx0 and tx0 <= cx1 and ty1 >= cy0 and ty0 <= cy1:
            nearby.append((ty0, tx0, tok.text))
    nearby.sort()
    return " ".join(t for _, _, t in nearby)


def find_page_name(tokens: list[PdfTextToken]) -> str:
    text = " ".join(t.text for t in tokens)
    m = re.search(r"\b\d{2}\s*:\s*[^\n]+?(?=\s+YJ-|\s+Schematic|$)", text)
    if m:
        return m.group(0).strip()
    return ""


def _has_signal_suffix(text: str, match: re.Match) -> bool:
    return match.end() < len(text) and text[match.end()] in {"+", "-"}


def _looks_like_note_text_token(text: str, match: re.Match) -> bool:
    if match.end() >= len(text):
        return False
    tail = text[match.end():]
    note_keywords = ["容值", "功耗", "略大", "信号", "建议", "范围", "默认", "可调", "注意"]
    return any(keyword in tail for keyword in note_keywords)


def _refdes_parts(refdes: str) -> tuple[str, int | None]:
    m = re.match(r"([A-Z]+)(\d+)", refdes.upper())
    if not m:
        return refdes.upper(), None
    return m.group(1), int(m.group(2))


def _looks_like_ic_pin_coordinate(refdes: str, context: str) -> bool:
    prefix, number = _refdes_parts(refdes)
    if prefix not in {"C", "R"} or number is None or number > 4:
        return False
    upper = context.upper()
    grid_labels = re.findall(r"\b[A-D][1-4]\b", upper)
    has_ic_ref = re.search(r"\bU\d+[A-Z]?\b", upper) is not None
    has_ic_model = re.search(r"\b[A-Z]{2,}\d{3,}[A-Z0-9/\.-]*\b", upper) is not None
    pin_names = sum(1 for name in ["CSN", "CSP", "SCL", "SDA", "INT_N", "VCELL", "TS", "GND"] if name in upper)
    return len(set(grid_labels)) >= 3 and (has_ic_ref or has_ic_model) and pin_names >= 2


def _looks_like_ic_function_pin(refdes: str, context: str) -> bool:
    prefix, _ = _refdes_parts(refdes)
    if prefix not in {"BAT", "SW"}:
        return False
    upper = context.upper()
    has_ic_ref = re.search(r"\bU\d+[A-Z]?\b", upper) is not None
    has_ic_model = re.search(r"\b[A-Z]{2,}\d{3,}[A-Z0-9/\.-]*\b", upper) is not None
    pin_keywords = [
        "VBUS", "VAC", "SYS1", "SYS2", "SCL", "SDA", "BTST", "REGN",
        "PMID", "PSEL", "NCE", "NQON", "STAT", "NINT", "NPG",
    ]
    pin_hits = sum(1 for keyword in pin_keywords if re.search(rf"\b{re.escape(keyword)}\b", upper))
    return ((has_ic_ref or has_ic_model) and pin_hits >= 2) or pin_hits >= 5


def extract_refdes_from_pdf(
    pdf_path: str | Path,
    prefixes: list[str] | None = None,
    bom_refdes_set: set[str] | None = None,
    nc_keywords: list[str] | None = None,
) -> list[PdfRef]:
    nc_keywords = nc_keywords or ["NC", "DNP", "DNI", "OPEN", "不贴", "空贴", "选贴", "预留"]
    exact_re = build_refdes_regex(prefixes)
    embedded_re = build_embedded_regex(prefixes)
    refs: list[PdfRef] = []

    with fitz.open(pdf_path) as doc:
        for page in doc:
            tokens = get_words(page)
            page_name = find_page_name(tokens)
            for tok in tokens:
                matches = [(m, "exact") for m in exact_re.finditer(tok.text)]
                if not matches:
                    m = embedded_re.match(tok.text)
                    if m:
                        matches = [(m, "embedded")]
                for m, match_kind in matches:
                    if _has_signal_suffix(tok.text, m):
                        continue
                    if _looks_like_note_text_token(tok.text, m):
                        continue
                    ref = normalize_refdes("".join(m.groups()))
                    # If token like C510uF is ambiguous, prefer BOM refdes candidates if provided.
                    if bom_refdes_set and ref not in bom_refdes_set and match_kind == "embedded":
                        alt_candidates = []
                        for cut in range(len(ref) - 1, 1, -1):
                            candidate = ref[:cut]
                            if candidate in bom_refdes_set:
                                alt_candidates.append(candidate)
                        if alt_candidates:
                            ref = sorted(alt_candidates, key=len, reverse=True)[0]
                        else:
                            continue
                    context = context_for_bbox(tokens, tok.bbox)
                    if _looks_like_ic_pin_coordinate(ref, context) or _looks_like_ic_function_pin(ref, context):
                        continue
                    refs.append(PdfRef(
                        refdes=ref,
                        page_index=page.number,
                        bbox=tok.bbox,
                        raw_text=tok.text,
                        context_text=context,
                        page_name=page_name,
                        is_nc_context=contains_any(context, nc_keywords),
                        confidence=0.9 if tok.text.upper() == ref else 0.75,
                    ))
    return deduplicate_pdf_refs(refs)


def deduplicate_pdf_refs(refs: list[PdfRef]) -> list[PdfRef]:
    seen = set()
    out = []
    for r in refs:
        key = (r.refdes, r.page_index, tuple(round(v, 1) for v in r.bbox))
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def index_pdf_refs(refs: list[PdfRef]) -> dict[str, list[PdfRef]]:
    idx: dict[str, list[PdfRef]] = defaultdict(list)
    for r in refs:
        idx[r.refdes].append(r)
    return dict(idx)
