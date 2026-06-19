from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Any

from bomcheck_toolkit.models import CheckIssue, RefMatch
from bomcheck_toolkit.parsers.bom_parser import parse_bom
from bomcheck_toolkit.pdf.annotator import annotate_pdf
from bomcheck_toolkit.pdf.refdes_extractor import extract_refdes_from_pdf
from bomcheck_toolkit.reports.excel_report import write_check_report, write_match_report
from bomcheck_toolkit.rules.engine import run_rules
from bomcheck_toolkit.utils import load_yaml, save_json

LogFn = Callable[[str], None]


def default_config_path(name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "configs" / name


def _log(logger: LogFn | None, message: str) -> None:
    if logger:
        logger(message)


def _sorted_issues(issues: list[CheckIssue]) -> list[CheckIssue]:
    rank = {"error": 0, "warning": 1, "info": 2, "ignore": 3}
    return sorted(issues, key=lambda issue: (rank[issue.severity], issue.refdes))


def _issue_targets(issues: list[CheckIssue], matches: list[RefMatch]) -> list[dict[str, Any]]:
    match_by_ref = {match.refdes: match for match in matches}
    targets: list[dict[str, Any]] = []
    for issue in _sorted_issues(issues):
        match = match_by_ref.get(issue.refdes)
        pdf_ref = None
        if match and match.pdf_refs:
            if issue.pdf_page is not None:
                pdf_ref = next(
                    (ref for ref in match.pdf_refs if ref.page_index == issue.pdf_page - 1),
                    None,
                )
            pdf_ref = pdf_ref or match.pdf_refs[0]

        target = {
            "severity": issue.severity,
            "rule_id": issue.rule_id,
            "title": issue.title,
            "refdes": issue.refdes,
            "bom_row": issue.bom_row,
            "pdf_page": issue.pdf_page,
            "has_location": pdf_ref is not None,
        }
        if pdf_ref:
            target.update(
                {
                    "page": pdf_ref.page_index + 1,
                    "page_index": pdf_ref.page_index,
                    "bbox": [round(value, 2) for value in pdf_ref.bbox],
                    "raw_text": pdf_ref.raw_text,
                    "context": pdf_ref.context_text[:180],
                }
            )
        targets.append(target)
    return targets


def run_check(
    bom: str | Path,
    pdf: str | Path,
    outdir: str | Path,
    *,
    rules: str | Path | None = None,
    prefixes: str | Path | None = None,
    logger: LogFn | None = None,
) -> dict[str, Any]:
    """Run the full BOM/PDF check pipeline and return a JSON-safe summary."""
    bom_path = Path(bom)
    pdf_path = Path(pdf)
    output_dir = Path(outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _log(logger, "读取规则配置")
    rules_cfg = load_yaml(rules or default_config_path("rules.yaml"))
    prefix_cfg = load_yaml(prefixes or default_config_path("refdes_prefixes.yaml"))
    refdes_prefixes = prefix_cfg.get("prefixes", [])
    nc_keywords = rules_cfg.get("nc_keywords", [])
    column_candidates = rules_cfg.get("bom_columns_candidates")

    _log(logger, "解析 BOM Excel")
    bom_items = parse_bom(bom_path, column_candidates=column_candidates)
    bom_ref_set = {r for item in bom_items for r in item.refdes_list}

    _log(logger, "提取 PDF 位号")
    pdf_refs = extract_refdes_from_pdf(
        pdf_path,
        prefixes=refdes_prefixes,
        bom_refdes_set=bom_ref_set,
        nc_keywords=nc_keywords,
    )

    _log(logger, "运行检查规则")
    matches, issues = run_rules(bom_items, pdf_refs, nc_keywords=nc_keywords)

    _log(logger, "写入 JSON 与 Excel 报告")
    bom_json = output_dir / "bom_parsed.json"
    refdes_json = output_dir / "refdes_extracted.json"
    match_report = output_dir / "refdes_match_report.xlsx"
    check_report = output_dir / "check_report.xlsx"
    annotated_pdf = output_dir / "annotated.pdf"

    save_json(bom_json, [asdict(i) for i in bom_items])
    save_json(refdes_json, [asdict(r) for r in pdf_refs])
    write_match_report(match_report, matches)
    write_check_report(check_report, issues)

    _log(logger, "生成标注 PDF")
    annotate_pdf(pdf_path, annotated_pdf, matches, issues)

    issue_counts = Counter(issue.severity for issue in issues)
    status_counts = Counter(match.status for match in matches)
    summary = {
        "bom_items": len(bom_items),
        "pdf_refs": len(pdf_refs),
        "matches": len(matches),
        "issues": len(issues),
        "issue_counts": dict(issue_counts),
        "match_status_counts": dict(status_counts),
        "issue_targets": _issue_targets(issues, matches),
        "files": {
            "annotated_pdf": str(annotated_pdf),
            "match_report": str(match_report),
            "check_report": str(check_report),
            "bom_json": str(bom_json),
            "refdes_json": str(refdes_json),
        },
    }
    _log(logger, "检查完成")
    return summary
