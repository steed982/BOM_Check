from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from bomcheck_toolkit.pipeline import run_check
from bomcheck_toolkit.parsers.bom_parser import parse_bom
from bomcheck_toolkit.pdf.refdes_extractor import extract_refdes_from_pdf
from bomcheck_toolkit.utils import save_json


def run(args: argparse.Namespace) -> None:
    summary = run_check(args.bom, args.pdf, args.outdir, rules=args.rules, prefixes=args.prefixes)
    print(f"Done. Output: {Path(args.outdir)}")
    print(f"BOM items: {summary['bom_items']}")
    print(f"PDF refs: {summary['pdf_refs']}")
    print(f"Matches: {summary['matches']}")
    print(f"Issues: {summary['issues']}")


def parse_bom_cmd(args: argparse.Namespace) -> None:
    items = parse_bom(args.bom)
    save_json(args.out, [asdict(i) for i in items])
    print(f"Parsed BOM items: {len(items)}")


def extract_pdf_cmd(args: argparse.Namespace) -> None:
    refs = extract_refdes_from_pdf(args.pdf)
    save_json(args.out, [asdict(r) for r in refs])
    print(f"Extracted PDF refs: {len(refs)}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="bomcheck")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run full BOM/PDF check")
    p_run.add_argument("--bom", required=True)
    p_run.add_argument("--pdf", required=True)
    p_run.add_argument("--outdir", required=True)
    p_run.add_argument("--rules")
    p_run.add_argument("--prefixes")
    p_run.set_defaults(func=run)

    p_bom = sub.add_parser("parse-bom", help="Parse BOM only")
    p_bom.add_argument("--bom", required=True)
    p_bom.add_argument("--out", required=True)
    p_bom.set_defaults(func=parse_bom_cmd)

    p_pdf = sub.add_parser("extract-pdf", help="Extract PDF RefDes only")
    p_pdf.add_argument("--pdf", required=True)
    p_pdf.add_argument("--out", required=True)
    p_pdf.set_defaults(func=extract_pdf_cmd)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
