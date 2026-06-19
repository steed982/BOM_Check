# BOM Check

Internal BOM/PDF consistency checker.

Source package: `bom_check_devkit/`

## Main Capabilities

- Parse BOM Excel/CSV refdes lists.
- Extract refdes and coordinates from schematic PDF.
- Generate annotated PDF, Excel reports, and JSON diagnostics.
- Run as a Windows LAN web service with FIFO queue.
- Provide a task-center page, standalone detail page, highlighted PDF locator, and packaged downloads.

## Quick Start

```bash
cd bom_check_devkit
pip install -e .
bomcheck-web --host 0.0.0.0 --port 8088
```

Windows deployment scripts are in `bom_check_devkit/scripts/`.
