# 使用示例

## 1. 安装

```bash
cd bom_check_devkit
pip install -e .[dev]
```

## 2. 运行

```bash
bomcheck run \
  --bom "套打_物料清单_2026061722223835.XLSX" \
  --pdf "BAT MB.pdf" \
  --outdir ./out
```

## 3. 查看输出

```text
out/annotated.pdf
out/refdes_match_report.xlsx
out/check_report.xlsx
out/refdes_extracted.json
```

## 4. 只提取 PDF 位号

```bash
bomcheck extract-pdf --pdf "BAT MB(1).pdf" --out out/refdes_extracted.json
```

## 5. 只解析 BOM

```bash
bomcheck parse-bom --bom "套打_物料清单_2026061722223835.XLSX" --out out/bom_parsed.json
```
