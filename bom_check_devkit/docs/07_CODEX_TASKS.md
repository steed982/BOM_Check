# 07 给 Codex 的开发任务

## Task 0：准备环境

```bash
pip install -e .[dev]
pytest
```

## Task 1：完善 BOM Parser

文件：`src/bomcheck_toolkit/parsers/bom_parser.py`

要求：

1. 自动识别 BOM 表头。
2. 支持 xlsx/csv。
3. 支持中文列名。
4. 实现 `expand_refdes_text()`。
5. 识别替代件。
6. 输出 `BomItem[]`。

验收：

```bash
pytest tests/test_bom_refdes_expand.py
```

## Task 2：完善 PDF RefDes Extractor

文件：`src/bomcheck_toolkit/pdf/refdes_extractor.py`

要求：

1. 用 PyMuPDF 读取 PDF words。
2. 提取 RefDes + bbox + page。
3. 支持粘连文本：`TVS1SMBJ6.5CA`、`C510uF/10V`。
4. 支持上下文窗口。
5. 过滤标题栏/页脚/图框。
6. 输出 JSON。

验收：

```bash
pytest tests/test_refdes_parser.py
```

## Task 3：完善 NC/TP/Mark 分类

文件：`src/bomcheck_toolkit/rules/engine.py`

要求：

1. PDF-only 不能直接报错。
2. 附近有 NC/DNP/不贴，分类为 `PDF_ONLY_NC`。
3. TP 分类为 `PDF_ONLY_TESTPOINT`。
4. ID + Markpoint/Badmark 分类为 `PDF_ONLY_MARKPOINT`。
5. 剩余 PDF-only 才是 `PDF_ONLY_SUSPECT`。

验收：

```bash
pytest tests/test_nc_context.py
```

## Task 4：实现关键器件比对

要求：

1. TVS 型号比对。
2. IC 型号比对。
3. R/C/L 值比对。
4. 输出 `VALUE_MISMATCH` 或 `CRITICAL_TVS_MISMATCH`。

重点示例：

```text
PDF: TVS1 SMBJ6.5CA
BOM: TVS1 SMBJ13A
=> CRITICAL_TVS_MISMATCH
```

## Task 5：实现 PDF 标注

文件：`src/bomcheck_toolkit/pdf/annotator.py`

要求：

1. 用 PyMuPDF 添加矩形框。
2. 按 issue severity 着色。
3. 支持注释文本。
4. 输出 annotated.pdf。

## Task 6：实现 Excel 报告

文件：`src/bomcheck_toolkit/reports/excel_report.py`

要求：

1. 输出 match report。
2. 输出 check report。
3. 格式化表头、筛选、冻结首行、列宽。

## Task 7：CLI 串起来

文件：`src/bomcheck_toolkit/cli.py`

命令：

```bash
bomcheck run --bom input.xlsx --pdf schematic.pdf --outdir out
```

输出：

```text
out/annotated.pdf
out/refdes_match_report.xlsx
out/check_report.xlsx
out/refdes_extracted.json
```

## Task 8：增加项目规则配置

把 NC 关键词、位号前缀、标题栏过滤区域、关键器件规则都放到 YAML。
