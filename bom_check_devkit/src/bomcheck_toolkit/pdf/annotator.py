from __future__ import annotations

from pathlib import Path
import re

import fitz

from bomcheck_toolkit.models import CheckIssue, RefMatch

COLOR_MAP = {
    "OK": (0, 0.8, 0),
    "BOM_ONLY": (1, 0, 0),
    "PDF_ONLY_SUSPECT": (1, 0.45, 0),
    "PDF_ONLY_NC": (1, 0.9, 0),
    "PDF_ONLY_TESTPOINT": (0.5, 0.5, 0.5),
    "PDF_ONLY_MARKPOINT": (0.5, 0.5, 0.5),
    "PDF_ONLY_PIN_NAME": (0.5, 0.5, 0.5),
    "MULTI_PDF_MATCH": (0.6, 0, 0.8),
}

SEVERITY_COLOR = {
    "error": (1, 0, 0),
    "warning": (1, 0.45, 0),
    "info": (1, 0.9, 0),
    "ignore": (0.5, 0.5, 0.5),
}

LEGEND_ITEMS = [
    ((1, 0, 0), "红色: 错误，必须处理"),
    ((1, 0.45, 0), "橙色: 警告，需要复核"),
    ((1, 0.9, 0), "黄色: 信息/不贴，通常可接受"),
    ((0.6, 0, 0.8), "紫色: 多处匹配"),
    ((0, 0.8, 0), "绿色: 匹配成功"),
    ((0.5, 0.5, 0.5), "灰色: 测试点/标记点/管脚名忽略"),
]


def _issue_by_ref(issues: list[CheckIssue]) -> dict[str, CheckIssue]:
    # Prefer highest severity.
    rank = {"error": 3, "warning": 2, "info": 1, "ignore": 0}
    out: dict[str, CheckIssue] = {}
    for issue in issues:
        if not issue.refdes:
            continue
        if issue.refdes not in out or rank[issue.severity] > rank[out[issue.refdes].severity]:
            out[issue.refdes] = issue
    return out


def add_color_legend(page: fitz.Page) -> None:
    fontname = "china-s"
    x0, y0 = 36, 34
    width, height = 278, 132
    panel = fitz.Rect(x0, y0, x0 + width, y0 + height)
    page.draw_rect(panel, color=(0.15, 0.15, 0.15), fill=(1, 1, 1), width=0.6, overlay=True)
    page.insert_textbox(
        fitz.Rect(x0 + 10, y0 + 8, x0 + width - 10, y0 + 26),
        "标注颜色说明",
        fontsize=10,
        fontname=fontname,
        color=(0, 0, 0),
        overlay=True,
    )
    y = y0 + 32
    for color, text in LEGEND_ITEMS:
        page.draw_rect(fitz.Rect(x0 + 12, y + 2, x0 + 24, y + 12), color=color, fill=None, width=1.6, overlay=True)
        page.insert_textbox(
            fitz.Rect(x0 + 32, y, x0 + width - 10, y + 15),
            text,
            fontsize=8.5,
            fontname=fontname,
            color=(0, 0, 0),
            overlay=True,
        )
        y += 15


def _issue_label(issue: CheckIssue) -> str:
    if issue.rule_id == "CRITICAL_TVS_MISMATCH":
        bom = re.search(r"BOM=([^,;\s]+)", issue.evidence)
        pdf = re.search(r"PDF=([^,;\s]+)", issue.evidence)
        if bom and pdf:
            return f"型号不一致\nBOM {bom.group(1)}\nSCH {pdf.group(1)}"
        return "型号不一致\n" + issue.evidence.strip()
    if issue.rule_id == "VALUE_MISMATCH":
        bom = re.search(r"BOM values=\[([^\]]+)\]", issue.evidence)
        pdf = re.search(r"PDF nearby values=\[([^\]]+)\]", issue.evidence)
        if bom and pdf:
            bom_value = bom.group(1).replace("'", "").split(",")[0].strip()
            pdf_value = pdf.group(1).replace("'", "").split(",")[0].strip()
            return f"参数不一致\nBOM {bom_value}\nSCH {pdf_value}"
    if issue.rule_id == "PDF_ONLY_SUSPECT":
        return "物料表未找到\n图纸存在此位号\n请确认是否漏料"
    if issue.rule_id == "DUPLICATE_STANDARD_REFDES":
        rows = re.findall(r"row (\d+)", issue.evidence)
        row_text = "/".join(rows[:3]) if rows else ""
        return "物料表重复\n此位号重复" + (f"\n行 {row_text}" if row_text else "")
    prefix = "错误" if issue.severity == "error" else "警告"
    return f"{prefix}\n{issue.refdes}\n{issue.title[:12]}"


def _label_size(text: str) -> tuple[float, float]:
    lines = text.splitlines()
    max_chars = max((len(line) for line in lines), default=8)
    width = max(64, min(128, max_chars * 5.6 + 12))
    height = max(22, len(lines) * 9.0 + 8)
    return width, height


def _expanded(rect: fitz.Rect, margin: float) -> fitz.Rect:
    return rect + (-margin, -margin, margin, margin)


def _intersection_area(a: fitz.Rect, b: fitz.Rect) -> float:
    x0 = max(a.x0, b.x0)
    y0 = max(a.y0, b.y0)
    x1 = min(a.x1, b.x1)
    y1 = min(a.y1, b.y1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0)


def _occupied_rects(page: fitz.Page, match_rects: list[fitz.Rect]) -> list[fitz.Rect]:
    rects: list[fitz.Rect] = []
    for word in page.get_text("words"):
        x0, y0, x1, y1 = word[:4]
        rects.append(_expanded(fitz.Rect(x0, y0, x1, y1), 2))

    page_area = page.rect.width * page.rect.height
    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect and 0 < rect.get_area() < page_area * 0.08:
            rects.append(_expanded(fitz.Rect(rect), 1))
        for item in drawing.get("items", []):
            item_rect = _drawing_item_rect(item)
            if item_rect and item_rect.get_area() < page_area * 0.08:
                rects.append(_expanded(item_rect, 2))

    rects.extend(_expanded(rect, 3) for rect in match_rects)
    return rects


def _drawing_item_rect(item: tuple) -> fitz.Rect | None:
    kind = item[0] if item else None
    if kind == "l" and len(item) >= 3:
        p1, p2 = item[1], item[2]
        return fitz.Rect(min(p1.x, p2.x), min(p1.y, p2.y), max(p1.x, p2.x), max(p1.y, p2.y))
    if kind == "re" and len(item) >= 2:
        return fitz.Rect(item[1])
    points = [value for value in item[1:] if isinstance(value, fitz.Point)]
    if points:
        return fitz.Rect(
            min(point.x for point in points),
            min(point.y for point in points),
            max(point.x for point in points),
            max(point.y for point in points),
        )
    return None


def _candidate_label_rects(anchor: fitz.Rect, width: float, height: float, severity: str) -> list[fitz.Rect]:
    gaps = [8, 24, 40, 64, 88, 120, 160]
    offsets = [0, -22, 22, -44, 44, -72, 72, -104, 104]
    candidates: list[fitz.Rect] = []
    for gap in gaps:
        for offset in offsets:
            candidates.append(fitz.Rect(anchor.x1 + gap, anchor.y0 + offset, anchor.x1 + gap + width, anchor.y0 + offset + height))
            candidates.append(fitz.Rect(anchor.x0 - gap - width, anchor.y0 + offset, anchor.x0 - gap, anchor.y0 + offset + height))
            candidates.append(fitz.Rect(anchor.x0 + offset, anchor.y0 - gap - height, anchor.x0 + offset + width, anchor.y0 - gap))
            candidates.append(fitz.Rect(anchor.x0 + offset, anchor.y1 + gap, anchor.x0 + offset + width, anchor.y1 + gap + height))
    if severity == "error":
        return sorted(candidates, key=lambda r: (r.x0 > anchor.x0, abs(r.y0 - anchor.y0)))
    return sorted(candidates, key=lambda r: (r.x0 < anchor.x0, abs(r.y0 - anchor.y0)))


def _label_rect_near(page: fitz.Page, anchor: fitz.Rect, text: str, severity: str, occupied: list[fitz.Rect]) -> fitz.Rect:
    width, height = _label_size(text)
    page_rect = page.rect
    candidates = [rect for rect in _candidate_label_rects(anchor, width, height, severity) if page_rect.contains(rect)]
    if not candidates:
        candidates = [fitz.Rect(
            max(page_rect.x0 + 4, min(anchor.x1 + 6, page_rect.x1 - width - 4)),
            max(page_rect.y0 + 4, min(anchor.y0, page_rect.y1 - height - 4)),
            max(page_rect.x0 + 4, min(anchor.x1 + 6, page_rect.x1 - width - 4)) + width,
            max(page_rect.y0 + 4, min(anchor.y0, page_rect.y1 - height - 4)) + height,
        )]

    def score(rect: fitz.Rect) -> float:
        test_rect = _expanded(rect, 2)
        overlap = sum(_intersection_area(test_rect, other) for other in occupied)
        distance = abs(rect.x0 - anchor.x0) + abs(rect.y0 - anchor.y0)
        return overlap * 10000 + distance * 0.25

    return min(candidates, key=score)


def add_issue_label(page: fitz.Page, anchor: fitz.Rect, issue: CheckIssue, occupied: list[fitz.Rect]) -> None:
    if issue.severity not in {"error", "warning"}:
        return
    text = _issue_label(issue)
    rect = _label_rect_near(page, anchor, text, issue.severity, occupied)
    color = SEVERITY_COLOR[issue.severity]
    fill = (1, 0.93, 0.93) if issue.severity == "error" else (1, 0.97, 0.82)
    page.draw_rect(rect, color=color, fill=fill, width=0.6, overlay=True)
    y = rect.y0 + 8.5
    for line in text.splitlines():
        if line.startswith(("BOM ", "SCH ")):
            label, value = line.split(" ", 1)
            page.insert_text(
                fitz.Point(rect.x0 + 4, y),
                label,
                fontsize=6.2,
                fontname="helv",
                color=(0, 0, 0),
                overlay=True,
            )
            page.insert_text(
                fitz.Point(rect.x0 + 24, y),
                value,
                fontsize=6.2,
                fontname="helv",
                color=(0, 0, 0),
                overlay=True,
            )
        else:
            page.insert_text(
                fitz.Point(rect.x0 + 4, y),
                line,
                fontsize=6.2,
                fontname="china-s",
                color=(0, 0, 0),
                overlay=True,
            )
        y += 9.0
    occupied.append(_expanded(rect, 5))


def annotate_pdf(pdf_path: str | Path, out_path: str | Path, matches: list[RefMatch], issues: list[CheckIssue]) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    issue_map = _issue_by_ref(issues)

    with fitz.open(pdf_path) as doc:
        if len(doc) > 0:
            add_color_legend(doc[0])
        match_rects_by_page: dict[int, list[fitz.Rect]] = {}
        for match in matches:
            for pref in match.pdf_refs:
                match_rects_by_page.setdefault(pref.page_index, []).append(_expanded(fitz.Rect(pref.bbox), 2))
        occupied_by_page = {
            page_index: _occupied_rects(doc[page_index], rects)
            for page_index, rects in match_rects_by_page.items()
        }
        for match in matches:
            if not match.pdf_refs:
                continue
            issue = issue_map.get(match.refdes)
            color = SEVERITY_COLOR[issue.severity] if issue else COLOR_MAP.get(match.status, (0, 0.8, 0))
            for pref in match.pdf_refs:
                page = doc[pref.page_index]
                rect = fitz.Rect(pref.bbox)
                rect = rect + (-2, -2, 2, 2)
                annot = page.add_rect_annot(rect)
                annot.set_colors(stroke=color)
                annot.set_border(width=1.2)
                if issue:
                    annot.set_info(content=f"{issue.rule_id}: {issue.title}\n{issue.evidence}")
                else:
                    annot.set_info(content=f"{match.refdes}: {match.status}")
                annot.update()
                if issue:
                    occupied = occupied_by_page.setdefault(pref.page_index, _occupied_rects(page, []))
                    add_issue_label(page, rect, issue, occupied)
        doc.save(out_path, garbage=4, deflate=True)
