from openpyxl import Workbook

from bomcheck_toolkit.parsers.bom_parser import parse_bom


def test_skip_repeated_header_and_detect_substitute(tmp_path):
    path = tmp_path / "bom.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["位置号", "子项规格型号", "厂商规格型号", "子项类型", "物料备注"])
    ws.append(["L1,L5", "合金电感，1uH±20%，2520", "MPN-A", "标准件", ""])
    ws.append(["位置号", "子项规格型号", "厂商规格型号", "子项类型", "物料备注"])
    ws.append(["L1,L5", "合金电感，1uH±20%，2520", "MPN-B", "替代件", ""])
    wb.save(path)

    items = parse_bom(path)

    assert len(items) == 2
    assert items[0].refdes_list == ["L1", "L5"]
    assert items[0].mpn == "MPN-A"
    assert items[0].is_substitute is False
    assert items[1].mpn == "MPN-B"
    assert items[1].is_substitute is True
