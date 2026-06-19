# 08 测试计划

## 1. 单元测试

### BOM 位号展开

用例：

| 输入 | 期望 |
|---|---|
| R1 | R1 |
| R1,R2,R3 | R1 R2 R3 |
| R1-R3 | R1 R2 R3 |
| C101~C103 | C101 C102 C103 |
| R1/R2/R3 | R1 R2 R3 |
| U1A,U1B | U1A U1B |

### PDF 位号识别

用例：

| 文本 | 期望 |
|---|---|
| TVS1SMBJ6.5CA | TVS1 |
| C510uF/10V | C5 或 C510，按 BOM 候选判断 |
| R45 | R45 |
| 5,7 | 不识别 |
| SW1 | 识别，但后续上下文评分 |

### NC 上下文

用例：

```text
C38 0.1uF/16V NC => PDF_ONLY_NC
R48 10K NC => PDF_ONLY_NC
TP1 1_0mm-1P => PDF_ONLY_TESTPOINT
ID1 Markpoint NC => PDF_ONLY_MARKPOINT
```

## 2. 集成测试

输入样例：

- BAT MB(1).pdf
- 套打_物料清单_*.xlsx

期望：

1. PDF 大部分 BOM 位号能找到。
2. NC 器件不作为 Error。
3. 测试点/Mark 点不作为 Error。
4. 标准件重复位号报 Error。
5. 标准件/替代件共用位号报 Info。
6. TVS1 型号不一致能报 Error/Warning。

## 3. 人工验收

随机抽查：

- 每页 10 个标注框是否框在正确位号上。
- PDF-only 列表中前 20 个是否分类正确。
- Error/Warning 是否可行动。

## 4. 回归测试

每增加一个项目样例，保存：

```text
tests/fixtures/project_x/bom.xlsx
tests/fixtures/project_x/schematic.pdf
tests/fixtures/project_x/expected_summary.json
```

回归指标：

- BOM_ONLY 数量不能异常上升。
- PDF_ONLY_SUSPECT 数量不能异常上升。
- 关键规则不能漏报。
