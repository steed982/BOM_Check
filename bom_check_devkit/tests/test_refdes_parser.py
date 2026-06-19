from bomcheck_toolkit.pdf.refdes_extractor import (
    _has_signal_suffix,
    _looks_like_ic_function_pin,
    _looks_like_ic_pin_coordinate,
    _looks_like_note_text_token,
    build_embedded_regex,
    build_refdes_regex,
)


def test_exact_refdes():
    r = build_refdes_regex()
    assert r.search("R45").group(0).upper() == "R45"


def test_no_substring_match():
    r = build_refdes_regex()
    assert r.search("R123AUX") is None


def test_embedded_tvs():
    r = build_embedded_regex()
    m = r.match("TVS1SMBJ6.5CA")
    assert "".join(m.groups()).upper() == "TVS1"


def test_embedded_cap():
    r = build_embedded_regex()
    m = r.match("C510uF/10V")
    assert "".join(m.groups()).upper() == "C510"


def test_signal_suffix_is_not_component_refdes():
    r = build_refdes_regex()
    m = r.search("D1+")
    assert m is not None
    assert _has_signal_suffix("D1+", m)


def test_ic_pin_coordinate_is_not_component_refdes():
    context = "C20 1nF/25V VBAT R26 0.02R/1% C2 C1 U2 CSN CSP C3 VCELL A1 INT_N A3 SCL B1 A2 SDA GND"
    assert _looks_like_ic_pin_coordinate("C1", context)
    assert _looks_like_ic_pin_coordinate("C2", context)
    assert not _looks_like_ic_pin_coordinate("C20", context)


def test_ic_function_pin_is_not_component_refdes():
    charger_context = "U40 SGM41513YTQF24G VBUS VAC SCL SDA SYS2 SYS1 BTST SW2 SW1 BAT1 BAT2"
    key_context = "SW1 1 2 1 2 4 3 4 3 KEY ESD6 ESDBNB5V0B1"

    assert _looks_like_ic_function_pin("SW2", charger_context)
    assert _looks_like_ic_function_pin("BAT1", charger_context)
    assert not _looks_like_ic_function_pin("SW1", key_context)


def test_note_text_refdes_is_not_component_refdes():
    r = build_refdes_regex()
    m = r.search("C40容值0.47uF~2.2uF")
    assert m is not None
    assert _looks_like_note_text_token("C40容值0.47uF~2.2uF", m)
