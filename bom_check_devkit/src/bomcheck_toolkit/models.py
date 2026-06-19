from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Severity = Literal["error", "warning", "info", "ignore"]


@dataclass(slots=True)
class BomItem:
    row_index: int
    raw_refdes: str
    refdes_list: list[str]
    qty: float | None = None
    value: str = ""
    mpn: str = ""
    is_substitute: bool = False
    remark: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PdfTextToken:
    page_index: int
    text: str
    bbox: tuple[float, float, float, float]


@dataclass(slots=True)
class PdfRef:
    refdes: str
    page_index: int
    bbox: tuple[float, float, float, float]
    raw_text: str
    context_text: str = ""
    page_name: str = ""
    is_nc_context: bool = False
    confidence: float = 1.0


@dataclass(slots=True)
class RefMatch:
    refdes: str
    bom_items: list[BomItem] = field(default_factory=list)
    pdf_refs: list[PdfRef] = field(default_factory=list)
    status: str = "UNKNOWN"
    confidence: float = 0.0


@dataclass(slots=True)
class CheckIssue:
    severity: Severity
    rule_id: str
    title: str
    refdes: str = ""
    bom_row: int | None = None
    pdf_page: int | None = None
    evidence: str = ""
    suggestion: str = ""
    status: str = "open"
