"""STM operator labels observed in the official public map on 2026-09-14."""

OPERATOR_NAMES = {
    "10": "COETC",
    "13": "Empresa Casanova",
    "18": "COPSA",
    "20": "COME / COMESA",  # The official selector publishes both labels for code 20.
    "29": "CITA",
    "32": "San Antonio Transporte y Turismo",
    "33": "C.O. del Este",
    "35": "Tala - Pando - Montevideo",
    "36": "Solfy",
    "37": "Turil",
    "39": "Zeballos Hermanos",
    "41": "Rutas del Norte",
    "50": "CUTCSA",
    "70": "UCOT",
    "80": "COIT",
}


def operator_name(code: str) -> str:
    return OPERATOR_NAMES.get(code, f"Empresa {code}")
