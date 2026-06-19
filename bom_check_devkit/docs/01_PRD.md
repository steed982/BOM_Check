# 01 PRD：BOM PDF 检查工具

## 1. 背景

硬件项目中，BOM、原理图 PDF、PCB、PLM/ERP 经常出现信息不同步：

- 原理图已改，BOM 未改。
- BOM 已改，PDF 仍是旧型号。
- NC/DNP 器件误报为漏 BOM。
- 标准件/替代件共用位号，被误判为重复。
- 关键保护器件，例如 TVS、eFuse、充电 IC，型号或参数被改错。

本工具用于在设计评审、BOM release、试产前自动检查这些问题。

## 2. 用户

- 硬件工程师：上传 BOM + 原理图 PDF，快速定位差异。
- 硬件负责人：重点查看 Error/Warning。
- NPI/供应链：确认 BOM 标准件、替代件、NC 物料。
- 测试/质量：追溯某个风险器件是否在原理图和 BOM 中一致。

## 3. 输入

必选：

- BOM Excel/XLSX/CSV。
- 原理图 PDF。

可选：

- EDA BOM。
- Netlist。
- PCB 位号坐标。
- 公司器件库/PLM 导出表。

## 4. 输出

- annotated.pdf：位号标注 PDF。
- refdes_match_report.xlsx：位号匹配报告。
- check_report.xlsx：异常报告。
- refdes_extracted.json：PDF 解析中间数据，用于调试。

## 5. MVP 必须实现

### 5.1 BOM 位号解析

支持以下格式：

```text
R1
R1,R2,R3
R1 R2 R3
R1/R2/R3
R1-R10
C101~C108
U1A / U1B
```

要求：

- 自动展开范围。
- 去重。
- 标准件和替代件识别。
- 保留 BOM 行号和原始文本。

### 5.2 PDF 位号提取

要求：

- 从 PDF 文本层提取 words/chars 和坐标。
- 支持粘连字符串中的位号，例如 `TVS1SMBJ6.5CA`、`C510uF/10V`。
- 过滤标题栏、页眉页脚、图框坐标、页间跳转数字。
- 支持同一位号多处命中。

### 5.3 PDF 标注

要求：

- BOM/PDF 匹配成功：绿色框。
- 关键异常：红色框。
- PDF-only NC：黄色框或不标。
- 重复/多处匹配：紫色框。
- 每个标注可带注释。

### 5.4 异常检查

MVP 检查项：

| ID | 检查 | 等级 |
|---|---|---|
| BOM_ONLY_REFDES | BOM 有但 PDF 找不到 | Error |
| PDF_ONLY_SUSPECT | PDF 有但 BOM 没有，且不是 NC/TP/Mark | Warning |
| PDF_ONLY_NC | PDF 有但 BOM 没有，附近标 NC/DNP | Info |
| PDF_ONLY_TESTPOINT | TP 不在 BOM | Ignore/Info |
| PDF_ONLY_MARKPOINT | ID/Markpoint 不在 BOM | Ignore |
| DUPLICATE_STANDARD_REFDES | 标准件重复位号 | Error |
| ALT_PART_SAME_REFDES | 标准件/替代件共用位号 | Info |
| VALUE_MISMATCH | BOM/PDF 关键值不一致 | Warning |
| CRITICAL_TVS_MISMATCH | TVS 型号/VRWM 不一致 | Error |

## 6. 非目标

MVP 不处理：

- 扫描件 PDF OCR。
- 自动识别原理图拓扑。
- 自动判断所有电源设计是否正确。
- ERP/PLM 在线集成。

## 7. 验收标准

对样例项目：

- BOM 位号匹配率 ≥ 95%。
- PDF-only 中 NC/TP/Mark 过滤准确率 ≥ 90%。
- 标准件重复位号能报 Error。
- 标准件/替代件共用位号不报 Error。
- TVS1 这类 BOM/PDF 型号不一致能报 Error/Warning。
