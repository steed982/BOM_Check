# 05 Rule Engine 规格

## 1. 规则引擎目标

规则引擎负责把 BOM 数据、PDF 位号数据和上下文文本转成可行动的问题列表。

## 2. 输入

- `BomItem[]`
- `PdfRef[]`
- `rules.yaml`

## 3. 输出

- `CheckIssue[]`

## 4. 核心规则

### 4.1 BOM_ONLY_REFDES

条件：

```text
RefDes in BOM and RefDes not in PDF
```

等级：Error。

说明：BOM 下单了，但原理图 PDF 找不到该位号。

### 4.2 PDF_ONLY_NC

条件：

```text
RefDes in PDF and RefDes not in BOM
and nearby context contains NC/DNP/DNI/OPEN/不贴/预留
```

等级：Info。

说明：原理图有该器件，但标了不贴，BOM 没有是合理的。

### 4.3 PDF_ONLY_TESTPOINT

条件：

```text
RefDes startswith TP and RefDes not in BOM
```

等级：Ignore/Info。

### 4.4 PDF_ONLY_MARKPOINT

条件：

```text
RefDes startswith ID and RefDes not in BOM
and nearby context contains Markpoint/Badmark/Mark 点
```

等级：Ignore。

### 4.5 PDF_ONLY_SUSPECT

条件：

```text
RefDes in PDF and RefDes not in BOM
and not NC/DNP
and not TP
and not Markpoint
```

等级：Warning。

### 4.6 DUPLICATE_STANDARD_REFDES

条件：

```text
same RefDes appears in multiple BOM rows
and all rows are standard part rows
```

等级：Error。

### 4.7 ALT_PART_SAME_REFDES

条件：

```text
same RefDes appears in multiple BOM rows
and at least one row is substitute part row
```

等级：Info。

### 4.8 VALUE_MISMATCH

条件：

```text
BOM value / MPN and PDF nearby value conflict
```

等级：Warning。

MVP 只实现简单字符串包含：

- 如果 BOM value 中的关键 token 在 PDF 上下文完全找不到，报 Warning。
- 忽略单位大小写和常见变体：uF/µF，ohm/R，K/k。

### 4.9 CRITICAL_TVS_MISMATCH

条件：

```text
RefDes prefix == TVS
and BOM value/mpn contains one TVS model
and PDF context contains another TVS model
```

等级：Error。

示例：

```text
PDF: TVS1 SMBJ6.5CA
BOM: TVS1 SMBJ13A
```

### 4.10 VBUS_TVS_REVIEW

条件：

```text
PDF context contains Type-C / VBUS / +5.0V_VIN
and nearby TVS model exists
```

输出 Info/Warning，让工程师复核 TVS VRWM、VC、后级耐压。

## 5. Issue 字段

```json
{
  "severity": "error",
  "rule_id": "CRITICAL_TVS_MISMATCH",
  "refdes": "TVS1",
  "page": 5,
  "title": "TVS 型号或 VRWM 与 PDF 不一致",
  "evidence": "PDF=SMBJ6.5CA, BOM=SMBJ13A",
  "suggestion": "确认原理图是否未更新，或 BOM 是否误改。",
  "status": "open"
}
```
