# 09 样例项目发现项

基于样例 BAT MB 原理图 PDF 和对应 BOM 的开发验证，以下问题适合作为 Demo：

## 1. PDF-only 不能直接报错

样例中初步提取到一批 PDF-only 位号，例如：

```text
C7, C29, C38, C39, C56, C148, C156, D1, ID1, ID2, ID3, ID4,
R1, R12, R14, R15, R34, R38, R39, R48, R55, TP1, TP2
```

其中很多在 PDF 附近标了 `NC`，例如：

```text
C38 0.1uF/16V NC
C39 0.1uF/16V NC
```

这类应分类为 `PDF_ONLY_NC`，不是 Error。

## 2. 测试点默认不报错

```text
TP1, TP2, TP3...
```

如果公司不要求测试点进 BOM，则分类为 `PDF_ONLY_TESTPOINT`。

## 3. Markpoint/Badmark 默认忽略

```text
ID1, ID2, ID3...
```

如果上下文包含 Markpoint/Badmark，则分类为 `PDF_ONLY_MARKPOINT`。

## 4. TVS1 是高价值异常

原理图 PDF 中 Type-C VBUS 附近有 `TVS1 SMBJ6.5CA`，但 BOM 中可能是 `SMBJ13A`。这类是 BOM/PDF 关键参数不一致，应报：

```text
CRITICAL_TVS_MISMATCH
```

建议：确认是原理图未更新，还是 BOM 错改。

## 5. 标准件/替代件共用位号不应误报

例如电感 L1/L5 可能同时存在标准件和替代件。应分类为：

```text
ALT_PART_SAME_REFDES
```

不应报标准件重复 Error。
