# 03 PDF 位号提取算法

## 1. 目标

从原理图 PDF 中提取位号和坐标，用于：

- 与 BOM 位号对比。
- 在 PDF 上标注器件位置。
- 根据附近文字判断 NC/DNP/参数。

## 2. 基本流程

```text
打开 PDF
  ↓
逐页提取 words
  ↓
过滤无效区域
  ↓
对每个 word 做 RefDes 正则识别
  ↓
处理粘连文本
  ↓
合并重复 token
  ↓
为每个 RefDes 建索引
```

## 3. 位号识别

### 3.1 前缀白名单

第一版支持：

```text
TVS, ESD, ANT, LED, BAT, NTC, FUSE, FB, TP, SW, ID, JP, CN,
J, U, R, C, L, Q, D, Y, X
```

### 3.2 精确匹配

用于普通 token：

```regex
(?<![A-Za-z0-9_])(TVS|ESD|ANT|LED|BAT|NTC|FUSE|FB|TP|SW|ID|JP|CN|J|U|R|C|L|Q|D|Y|X)([0-9]+[A-Za-z]?)(?![A-Za-z0-9_])
```

### 3.3 粘连匹配

用于 `TVS1SMBJ6.5CA`、`C510uF/10V` 等：

```regex
(TVS|ESD|ANT|LED|BAT|NTC|FUSE|FB|TP|SW|ID|JP|CN|J|U|R|C|L|Q|D|Y|X)([0-9]+[A-Za-z]?)
```

注意：

- 只从 token 开头提取时更安全。
- `C510uF/10V` 有歧义：可能是 C5 + 10uF，也可能 C510 + uF。必须结合 BOM 位号集合判断。
- 如果 BOM 中有 C5 且无 C510，则优先 C5。
- 如果 BOM 中有 C510，则优先 C510。
- 如果两者都有，标为 ambiguous。

## 4. 上下文窗口

对每个 RefDes 提取附近文字：

```text
x_margin = 80 pt
y_margin = 60 pt
```

用于判断：

- NC/DNP/OPEN/不贴/预留。
- 器件值：10k、0.1uF、SMBJ6.5CA。
- 是否在 IC pin list 内。
- 是否靠近标题栏。

## 5. 无效区域过滤

第一版使用启发式：

- 右下角标题栏区域：`x > page_width * 0.72 and y > page_height * 0.82`。
- 页眉/页脚：`y < 15` 或 `y > page_height - 15`。
- 图框坐标：单个数字 1~5、单个字母 A~D。
- Sheet/Page 信息行。

后续可以支持项目模板配置。

## 6. 多处匹配评分

同一个位号可能出现多次，例如：

- 真正器件位号。
- IC 引脚名，如 SW1。
- 注释文字。
- 页间引用。

评分建议：

| 条件 | 分数 |
|---|---:|
| 附近有值/型号 | +30 |
| 附近有元件图形线条/矩形 | +20 |
| 附近有 NC/DNP | +10 |
| 位于 IC 方框内部 | -40 |
| 位于标题栏 | -100 |
| 是页间引用数字附近 | -30 |

MVP 可先记录全部匹配，报告 `match_count > 1`，由人工确认。

## 7. 输出字段

```json
{
  "refdes": "C38",
  "page_index": 5,
  "page_label": "06: MCU",
  "bbox": [x0, y0, x1, y1],
  "raw_text": "C38",
  "context_text": "C38 0.1uF/16V NC",
  "is_nc_context": true,
  "confidence": 0.92
}
```
