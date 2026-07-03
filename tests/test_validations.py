from utils.validations import normalize_indian_symbol, validate_symbol


def test_normalize_symbol_defaults_to_nse():
    assert normalize_indian_symbol("reliance") == "RELIANCE.NS"


def test_validate_symbol_accepts_nse_and_bse():
    assert validate_symbol("TCS.NS")
    assert validate_symbol("RELIANCE.BO")


def test_validate_symbol_rejects_bad_input():
    assert not validate_symbol("TCS")
    assert not validate_symbol("bad symbol.NS")
