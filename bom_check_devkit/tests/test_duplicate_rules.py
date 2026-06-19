from bomcheck_toolkit.models import BomItem
from bomcheck_toolkit.rules.engine import run_rules


def item(row, refdes, *, substitute=False):
    return BomItem(
        row_index=row,
        raw_refdes=refdes,
        refdes_list=[refdes],
        value=f"value-{row}",
        mpn=f"mpn-{row}",
        is_substitute=substitute,
    )


def test_duplicate_standard_refdes_is_error():
    _, issues = run_rules([item(1, "L1"), item(2, "L1")], [])

    assert [issue.rule_id for issue in issues] == ["DUPLICATE_STANDARD_REFDES", "BOM_ONLY_REFDES"]


def test_standard_and_substitute_same_refdes_is_not_issue():
    _, issues = run_rules([item(1, "L1"), item(2, "L1", substitute=True)], [])

    assert [issue.rule_id for issue in issues] == ["BOM_ONLY_REFDES"]
