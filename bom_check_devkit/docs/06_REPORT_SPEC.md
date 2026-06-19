# 06 报告规格

## 1. 输出文件

```text
annotated.pdf
refdes_match_report.xlsx
check_report.xlsx
refdes_extracted.json
```

## 2. refdes_match_report.xlsx

字段：

| 字段 | 说明 |
|---|---|
| RefDes | 位号 |
| BOM_Row | BOM 行号 |
| BOM_Value | BOM 规格/值 |
| BOM_MPN | BOM 料号/型号 |
| PDF_Page | PDF 页码 |
| PDF_Page_Name | 页名称 |
| PDF_BBox | 坐标 |
| PDF_Context | 附近文本 |
| Match_Count | PDF 命中次数 |
| Status | OK/BOM_ONLY/PDF_ONLY_NC/PDF_ONLY_SUSPECT 等 |
| Confidence | 置信度 |
| Note | 备注 |

## 3. check_report.xlsx

字段：

| 字段 | 说明 |
|---|---|
| Severity | error/warning/info/ignore |
| Rule_ID | 规则 ID |
| RefDes | 位号 |
| BOM_Row | BOM 行号 |
| PDF_Page | 页码 |
| Title | 问题标题 |
| Evidence | 证据 |
| Suggestion | 建议 |
| Status | open/confirmed/ignored/fixed |

## 4. annotated.pdf 标注颜色

| 类别 | 颜色 |
|---|---|
| OK | 绿色 |
| Error | 红色 |
| Warning | 橙色 |
| Info | 黄色 |
| Duplicate | 紫色 |
| Ignored | 灰色或不标 |

## 5. Excel 样式

- Error 行红底。
- Warning 行橙底。
- Info 行淡蓝/淡黄。
- Ignore 行灰色。
- 冻结首行。
- 自动筛选。
- 列宽自适应。
