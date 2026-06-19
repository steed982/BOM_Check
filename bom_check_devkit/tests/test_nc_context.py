from bomcheck_toolkit.models import PdfRef
from bomcheck_toolkit.rules.engine import classify_pdf_only


def pref(ref, context):
    return PdfRef(refdes=ref, page_index=0, bbox=(0, 0, 1, 1), raw_text=ref, context_text=context, is_nc_context="NC" in context)


def test_pdf_only_nc():
    status, severity, _ = classify_pdf_only("C38", [pref("C38", "C38 0.1uF/16V NC")], ["NC", "DNP"])
    assert status == "PDF_ONLY_NC"
    assert severity == "info"


def test_pdf_only_tp():
    status, severity, _ = classify_pdf_only("TP1", [pref("TP1", "TP1 1_0mm-1P")], ["NC"])
    assert status == "PDF_ONLY_TESTPOINT"
    assert severity == "ignore"


def test_pdf_only_markpoint():
    status, severity, _ = classify_pdf_only("ID1", [pref("ID1", "ID1 Markpoint NC")], ["NC"])
    assert status == "PDF_ONLY_MARKPOINT"
    assert severity == "ignore"


def test_pdf_only_suspect():
    status, severity, _ = classify_pdf_only("J9", [pref("J9", "J9 CON_5PIN")], ["NC"])
    assert status == "PDF_ONLY_SUSPECT"
    assert severity == "warning"


def test_nc_keyword_does_not_match_signal_substrings():
    status, severity, _ = classify_pdf_only("BAT1", [pref("BAT1", "BAT1 nCE CON_INT")], ["NC"])
    assert status == "PDF_ONLY_SUSPECT"
    assert severity == "warning"


def test_pdf_only_ic_pin_name_is_ignored():
    status, severity, _ = classify_pdf_only(
        "BAT1",
        [pref("BAT1", "U40 SGM41513YTQF24G VBUS SYS1 SYS2 BAT1 BAT2 SCL SDA")],
        ["NC"],
    )
    assert status == "PDF_ONLY_PIN_NAME"
    assert severity == "ignore"
