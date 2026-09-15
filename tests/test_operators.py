from app.domain.operators import operator_name


def test_known_operator_code_has_public_name():
    assert operator_name("50") == "CUTCSA"


def test_ambiguous_public_code_preserves_both_labels():
    assert operator_name("20") == "COME / COMESA"


def test_unknown_operator_is_readable():
    assert operator_name("999") == "Empresa 999"
