import pytest

from consulenza.ambiente import VariabileMancante, richiedi


def test_restituisce_il_valore_senza_spazi():
    assert richiedi("SHEET_ID", {"SHEET_ID": "  abc123 \n"}) == "abc123"


@pytest.mark.parametrize("ambiente", [{}, {"SHEET_ID": ""}, {"SHEET_ID": "   "}])
def test_variabile_mancante_o_vuota(ambiente):
    with pytest.raises(VariabileMancante, match="SHEET_ID"):
        richiedi("SHEET_ID", ambiente)
