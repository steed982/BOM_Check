from bomcheck_toolkit.parsers.bom_parser import expand_refdes_text


def test_simple_list():
    assert expand_refdes_text("R1,R2,R3") == ["R1", "R2", "R3"]


def test_chinese_comma_and_space():
    assert expand_refdes_text("C1， C2 C3") == ["C1", "C2", "C3"]


def test_dash_range():
    assert expand_refdes_text("R1-R3") == ["R1", "R2", "R3"]


def test_tilde_range():
    assert expand_refdes_text("C101~C103") == ["C101", "C102", "C103"]


def test_suffix_refs():
    assert expand_refdes_text("U1A,U1B") == ["U1A", "U1B"]
