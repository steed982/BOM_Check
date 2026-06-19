# 04 BOM Parser 规格

## 1. 目标

把 BOM Excel/CSV 解析成标准数据结构，重点是位号、规格、料号、数量、替代件关系。

## 2. 自动识别列

候选列名在 `configs/rules.yaml` 中配置。

常见列：

- 位号 / 位置号 / RefDes / Designator
- 规格型号 / 规格 / 参数 / Value / Description
- 物料编码 / 料号 / MPN
- 数量 / Qty
- 替代 / 替代料 / Substitute / ALT
- 备注 / Remark

## 3. 位号展开

支持：

```text
R1
R1,R2,R3
R1，R2，R3
R1 R2 R3
R1/R2/R3
R1-R10
R1~R10
C101-C108
U1A,U1B
```

范围展开规则：

- 前缀必须相同。
- 数字部分递增。
- 不支持跨前缀范围，例如 R1-C3。
- 带后缀范围，例如 U1A-U1D，MVP 可不展开，直接保留。

## 4. 数量校验

如果 BOM 数量列存在：

- `qty == expanded_refdes_count`：OK。
- 不一致：Warning。
- 替代件行可跳过数量校验，或单独标注。

## 5. 替代件识别

优先判断：

- 替代列中含 是/替代/ALT/Y。
- 备注中含 替代/代用/second source/alternate。
- 同一位号重复，但其中一行明确替代，则归类 `ALT_PART_SAME_REFDES`。

## 6. 标准件重复

如果同一 RefDes 出现在多个 BOM 行，且这些行都不是替代件：

- 报 `DUPLICATE_STANDARD_REFDES`。

## 7. 输出结构

```json
{
  "row_index": 24,
  "raw_refdes": "L1,L5",
  "refdes_list": ["L1", "L5"],
  "qty": 2,
  "value": "1uH-2520",
  "mpn": "MWTC252010S1R0MT",
  "is_substitute": false,
  "remark": ""
}
```
