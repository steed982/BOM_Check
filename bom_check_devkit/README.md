# BOM PDF 检查工具开发包

目标：开发一个内部工具，输入 BOM Excel 和原理图 PDF，输出：

1. 标注后的原理图 PDF：把 BOM 位号标注到对应位置。
2. 位号匹配报告：BOM 位号、PDF 页码、坐标、匹配状态、置信度。
3. 异常检查报告：BOM/PDF 关键信息不一致、重复位号、NC/DNP/测试点/Mark 点过滤结果、关键电源链路风险。

本开发包给 Codex/工程师使用，包含需求文档、架构设计、规则配置、Python MVP 骨架和测试用例。

## 目录

```text
bom_check_devkit/
├── README.md
├── pyproject.toml
├── configs/
│   ├── refdes_prefixes.yaml
│   └── rules.yaml
├── docs/
│   ├── 01_PRD.md
│   ├── 02_ARCHITECTURE.md
│   ├── 03_PDF_REFDES_EXTRACTION.md
│   ├── 04_BOM_PARSER_SPEC.md
│   ├── 05_RULE_ENGINE_SPEC.md
│   ├── 06_REPORT_SPEC.md
│   ├── 07_CODEX_TASKS.md
│   ├── 08_TEST_PLAN.md
│   └── 09_SAMPLE_FINDINGS.md
├── examples/
│   └── sample_usage.md
├── src/bomcheck_toolkit/
│   ├── cli.py
│   ├── models.py
│   ├── utils.py
│   ├── parsers/bom_parser.py
│   ├── pdf/refdes_extractor.py
│   ├── pdf/annotator.py
│   ├── rules/engine.py
│   └── reports/excel_report.py
└── tests/
    ├── test_refdes_parser.py
    ├── test_bom_refdes_expand.py
    └── test_nc_context.py
```

## MVP 命令

```bash
pip install -e .
bomcheck run \
  --bom "套打_物料清单_2026061722223835.XLSX" \
  --pdf "BAT MB.pdf" \
  --outdir ./out
```

输出：

```text
out/annotated.pdf
out/refdes_match_report.xlsx
out/check_report.xlsx
out/refdes_extracted.json
```

## 局域网 Web 服务

Windows 服务器首次部署：

```powershell
cd bom_check_devkit
.\scripts\setup_windows.ps1
```

如果服务器装了 Python launcher，也可以显式指定：

```powershell
.\scripts\setup_windows.ps1 -Python "py -3"
```

启动网页服务：

```powershell
.\scripts\run_web_windows.ps1 -HostAddress 0.0.0.0 -Port 8088
```

设置为登录后自动启动：

```powershell
.\scripts\install_windows_task.ps1 -Port 8088
```

浏览器访问：

```text
http://服务器IP:8088
```

如果其他电脑无法访问，先在 Windows 防火墙放行端口：

```powershell
.\scripts\open_firewall_windows.ps1 -Port 8088
```

Web 端输入与 Mac app 保持一致：

- BOM Excel：`.xlsx/.xlsm/.xltx/.xltm/.csv`
- 原理图 PDF：`.pdf`

Web 端输出：

- 标注后的 `annotated.pdf`，支持下载和明细页打开。
- `check_report.xlsx` / `refdes_match_report.xlsx`，可单独下载或通过 Excel 包下载。
- `report.html` 页面报告，可下载后留档。
- `bundle.zip` 完整包，包含页面报告、PDF、两个 Excel 和两个 JSON。
- `bom_parsed.json` / `refdes_extracted.json`，用于排查解析结果。

多人使用行为：

- 服务端采用 FIFO 队列，默认 `1` 个后台 worker，同一时间只跑一个 BOM/PDF 检查任务。
- 多人同时上传时，任务会进入排队状态，网页显示当前排队位置和前方任务数量。
- 如果服务器性能足够，可以用 `-Workers 2` 启动或安装计划任务，但大 PDF 会明显占用 CPU/内存，默认建议保持 `1`。

网页预览：

- 主页面是任务中心，只显示上传、队列、运行状态和完成任务的下载入口。
- 完成后点击“查看明细”会打开独立明细页面，避免 PDF 和异常列表挤在窄侧栏。
- 明细页点击任一异常会选中该条，并在右侧显示对应 PDF 页面的高亮定位图。
- BOM-only 等没有 PDF 坐标的异常会标记为“无坐标”。

## 第一版范围

必须实现：

- BOM 位号解析、展开、去重。
- PDF 位号文本提取和坐标定位。
- PDF 标注。
- BOM 有但 PDF 找不到。
- PDF 有但 BOM 没有，并区分 NC/DNP、测试点、Mark 点、疑似异常。
- BOM 重复位号，但能识别标准件/替代件。
- 关键器件参数比对：至少支持 TVS、IC、连接器、L/C/R 基础值。

暂不强制实现：

- OCR。
- 原理图图形语义识别。
- Netlist 拓扑检查。
- PLM/ERP 生命周期检查。

## 重要原则

不要把 PDF-only 直接报错。必须先判断：

- 附近是否标了 NC/DNP/OPEN/不贴/预留。
- 是否是 TP 测试点。
- 是否是 ID Markpoint/Badmark。
- 是否是连接器机械脚、IC 引脚名、图框或标题栏文字。

真正要重点报错的是：

- BOM 有位号，但 PDF 找不到。
- 标准 BOM 行重复位号。
- BOM/PDF 关键器件型号或关键参数不一致。
- PDF-only 且没有 NC/DNP/TP/Mark 证据。
