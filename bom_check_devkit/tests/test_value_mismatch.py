from bomcheck_toolkit.models import BomItem, PdfRef
from bomcheck_toolkit.rules.engine import check_value_mismatch


def bom(refdes, value):
    return BomItem(row_index=2, raw_refdes=refdes, refdes_list=[refdes], value=value)


def pdf(refdes, context):
    return PdfRef(refdes=refdes, page_index=0, bbox=(0, 0, 1, 1), raw_text=refdes, context_text=context)


def test_tvs_model_mismatch_is_error():
    issues = check_value_mismatch(
        "TVS1",
        [bom("TVS1", "TVS，SMBJ13A，Vr-13V")],
        [pdf("TVS1", "TVS1 SMBJ6.5CA Type-C VBUS")],
    )

    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert issues[0].rule_id == "CRITICAL_TVS_MISMATCH"


def test_passive_value_mismatch_is_warning():
    issues = check_value_mismatch(
        "R1",
        [bom("R1", "电阻，10KΩ，1%")],
        [pdf("R1", "R1 100R/5%")],
    )

    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert issues[0].rule_id == "VALUE_MISMATCH"


def test_non_passive_description_does_not_create_generic_warning():
    issues = check_value_mismatch(
        "ANT1",
        [bom("ANT1", "侧接弹片，单触点，H=0.95mm,2.95x1.25mm")],
        [pdf("ANT1", "ANT1 SP-1 +3.3V_MCU")],
    )

    assert issues == []
