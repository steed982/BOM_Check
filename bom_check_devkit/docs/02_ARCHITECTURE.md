# 02 架构设计

## 1. 总体架构

```text
BOM Excel/CSV
  ↓
BomParser
  ↓
BomItem / RefDesIndex

Schematic PDF
  ↓
PdfRefdesExtractor
  ↓
PdfRef / PdfTextToken / PageIndex

BomItem + PdfRef
  ↓
RuleEngine
  ↓
CheckIssue[]

PdfRef + CheckIssue
  ↓
PdfAnnotator
  ↓
annotated.pdf

BomItem + PdfRef + CheckIssue
  ↓
ExcelReportWriter
  ↓
refdes_match_report.xlsx / check_report.xlsx
```

## 2. 模块职责

### BomParser

- 读取 Excel/CSV。
- 自动识别位号列、数量列、规格列、料号列、备注列、替代件列。
- 展开位号。
- 生成 `BomItem`。

### PdfRefdesExtractor

- 读取 PDF。
- 提取每页文本 token 和坐标。
- 识别 RefDes。
- 计算附近上下文。
- 过滤标题栏/页脚/图框。
- 输出 `PdfRef`。

### RuleEngine

- 对比 BOM 和 PDF 位号集合。
- 分类 PDF-only：NC、TP、Mark、Suspect。
- 检查 BOM-only。
- 检查重复位号。
- 检查关键参数不一致。

### PdfAnnotator

- 根据匹配结果和异常结果画框。
- 支持不同颜色、透明度、注释。

### ExcelReportWriter

- 输出两个 Excel：
  - 匹配报告。
  - 异常报告。

## 3. 数据模型

核心数据模型定义在 `src/bomcheck_toolkit/models.py`。

关键实体：

- `BomItem`
- `BomRef`
- `PdfTextToken`
- `PdfRef`
- `RefMatch`
- `CheckIssue`

## 4. 推荐技术栈

| 模块 | 技术 |
|---|---|
| Excel | pandas + openpyxl |
| PDF 文本提取 | PyMuPDF |
| PDF 标注 | PyMuPDF |
| 规则配置 | YAML |
| CLI | argparse |
| 测试 | pytest |

## 5. 后续扩展

- Streamlit 内部 Web MVP。
- FastAPI + React + PDF.js。
- 连接 PLM/ERP。
- 接入 EDA 原始数据，例如 KiCad/Altium 导出 BOM、Netlist、PickPlace。
