import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation


@dataclass
class ImportedRow:
    raw_date: str
    description: str
    amount: Decimal
    currency: str  # "ARS" | "USD"
    suggested_category_name: str = ""

    @property
    def date_parsed(self) -> date | None:
        try:
            d, m, y = self.raw_date.split(".")
            return date(2000 + int(y), int(m), int(d))
        except Exception:
            return None


_DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{2}$")

# Palabras en x 120-160: comprobante alfanumérico corto
_COMPROBANTE_RE = re.compile(r"^\w{5,10}$")

# Filas que nunca son gastos del usuario
_IGNORE_PATTERNS = [
    r"^SU PAGO EN",
    r"^SALDO ANTERIOR",
    r"^SALDO ACTUAL",
    r"^DEV\.IMP\.",
    r"^Tarjeta \d+ Total",
    r"^PAGO MINIMO",
]

# Filas de impuestos → categoría "Impuestos"
_TAX_PATTERNS = [
    r"^IMPUESTO DE SELLOS",
    r"^IIBB PERCEP",
    r"^IVA RG \d+",
    r"^DB\.RG \d+",
]

# Columnas por coordenada X (basadas en debug del PDF Macro Visa)
_X_COMPROBANTE_MIN = 118
_X_COMPROBANTE_MAX = 160
_X_DESC_MIN = 160
_X_DESC_MAX = 270
_X_USD_MARKER_MAX = 295  # palabra "USD" aparece entre 270-295
_X_AMOUNT_PESOS_MIN = 295  # columna PESOS (incluye el monto duplicado de filas USD)
_X_AMOUNT_ARS_MIN = 390  # columna PESOS principal
_X_AMOUNT_ARS_MAX = 470
_X_AMOUNT_USD_MIN = 490  # columna DOLARES
_X_AMOUNT_USD_MAX = 545

# Patrón para limpiar ruido de descripción:
# - IDs numéricos largos (>= 10 dígitos): ej 64616891726956200, 000020996715876
# - Códigos internos de Macro: mezclan may+min+dígitos, ej in1Te59VBUSD, xMHPdpK3VjuL8BOAEa, P1lY8F6n
#   Se identifican por tener al menos una minúscula Y al menos un dígito (no son palabras reales)
# - Montos que se cuelen en la descripción
_NOISE_RE = re.compile(
    r"\b\d{10,}\b"  # IDs numéricos muy largos
    r"|\b(?=[a-zA-Z0-9]*[a-z])(?=[a-zA-Z0-9]*[A-Z])(?=[a-zA-Z0-9]*\d)[a-zA-Z0-9]{6,}\b"
    # tokens con minúscula+mayúscula+dígito mezclados
    r"|\b\d{1,3}(?:\.\d{3})*,\d{2}\b"  # montos formato argentino
    r"|\b\d+,\d{2}\b"  # montos simples con coma
)


def _parse_amount(text: str) -> Decimal | None:
    """Convierte '25.398,00' o '6,30' a Decimal."""
    cleaned = text.strip().rstrip("-").replace(".", "").replace(",", ".")
    try:
        val = Decimal(cleaned)
        return val if val > 0 else None
    except InvalidOperation:
        return None


def _is_ignored(description: str) -> bool:
    return any(re.search(pattern, description, re.IGNORECASE) for pattern in _IGNORE_PATTERNS)


def _is_tax(description: str) -> bool:
    return any(re.search(pattern, description, re.IGNORECASE) for pattern in _TAX_PATTERNS)


def _group_words_by_row(words: list[dict], y_tolerance: int = 3) -> list[list[dict]]:
    """Agrupa palabras por línea usando proximidad vertical."""
    if not words:
        return []
    sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))
    rows = []
    current_row = [sorted_words[0]]
    for word in sorted_words[1:]:
        if abs(word["top"] - current_row[-1]["top"]) <= y_tolerance:
            current_row.append(word)
        else:
            rows.append(sorted(current_row, key=lambda w: w["x0"]))
            current_row = [word]
    rows.append(sorted(current_row, key=lambda w: w["x0"]))
    return rows


def parse_macro_visa(pdf_path: str) -> list[ImportedRow]:
    """
    Parsea un resumen Visa Macro usando coordenadas X de columnas.
    Retorna solo las filas de consumos — excluye pagos, saldos y subtotales.
    """
    import pdfplumber

    results: list[ImportedRow] = []
    in_transactions = False

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(x_tolerance=3, y_tolerance=3)
            if not words:
                continue

            # Detectar inicio y fin del bloque de transacciones por texto
            page_text = page.extract_text() or ""
            if "DETALLE DE TRANSACCION" not in page_text and not in_transactions:
                continue

            rows = _group_words_by_row(words)

            for row_words in rows:
                texts = [w["text"] for w in row_words]
                line_text = " ".join(texts)

                # Detectar inicio del bloque
                if "DETALLE DE TRANSACCION" in line_text:
                    in_transactions = True
                    continue

                # Detectar fin del bloque
                if in_transactions and any(
                    marker in line_text
                    for marker in ["OPCIONES DE PAGO", "USTED DISPONE DE", "Para consultas"]
                ):
                    in_transactions = False
                    continue

                if not in_transactions:
                    continue

                # La primera palabra debe ser fecha DD.MM.AA
                if not _DATE_RE.match(row_words[0]["text"]):
                    continue

                raw_date = row_words[0]["text"]

                # Clasificar palabras por columna X
                desc_words = []
                has_usd_marker = False
                amount_ars: Decimal | None = None
                amount_usd: Decimal | None = None

                for w in row_words[1:]:
                    x = w["x0"]
                    text = w["text"]

                    if _X_COMPROBANTE_MIN <= x <= _X_COMPROBANTE_MAX and _COMPROBANTE_RE.match(
                        text
                    ):
                        # Comprobante — ignorar
                        continue
                    elif _X_DESC_MIN <= x < _X_USD_MARKER_MAX:
                        if text.upper() == "USD":
                            has_usd_marker = True
                        else:
                            desc_words.append(text)
                    elif _X_USD_MARKER_MAX <= x < _X_AMOUNT_PESOS_MIN:
                        # Zona "USD" explícito antes de montos
                        if text.upper() == "USD":
                            has_usd_marker = True
                        elif text not in ("_",):
                            desc_words.append(text)
                    elif _X_AMOUNT_PESOS_MIN <= x < _X_AMOUNT_ARS_MIN:
                        # Monto en zona intermedia: primer monto de filas USD (se ignora,
                        # el valor real está en columna DOLARES) o "Cuota X/Y"
                        if re.match(r"^\d+/\d+$", text):
                            # "03/06" — número de cuota, va a descripción
                            desc_words.append(text)
                        elif text not in ("_", "TC" + text[2:]) and not text.startswith("TC"):
                            pass  # monto duplicado USD — ignorar
                    elif _X_AMOUNT_ARS_MIN <= x <= _X_AMOUNT_ARS_MAX:
                        amount_ars = _parse_amount(text)
                    elif _X_AMOUNT_USD_MIN <= x <= _X_AMOUNT_USD_MAX:
                        amount_usd = _parse_amount(text)

                description = " ".join(desc_words).strip()
                # Limpiar IDs de transacción largos y montos residuales
                description = _NOISE_RE.sub("", description).strip()
                description = re.sub(r"\s{2,}", " ", description).strip()
                # Quitar "$" y "P $" solos al final (residuo de impuesto de sellos)
                description = re.sub(r"\s*P?\s*\$\s*$", "", description).strip()
                # Quitar paréntesis vacíos y porcentajes con paréntesis vacíos
                description = re.sub(r"\s*%?\s*\(\s*\)", "", description).strip()
                description = re.sub(r"\s*\(\s*\)", "", description).strip()

                if not description:
                    continue

                # Determinar moneda y monto final
                # Filas USD: tienen monto en columna DOLARES (amount_usd)
                # Algunas filas USD también tienen monto en columna PESOS (amount_ars) — ignorar ese
                if has_usd_marker and amount_usd:
                    currency = "USD"
                    amount = amount_usd
                elif not has_usd_marker and amount_usd and not amount_ars:
                    # USD sin marker explícito pero solo tiene monto en col DOLARES
                    currency = "USD"
                    amount = amount_usd
                elif amount_ars:
                    currency = "ARS"
                    amount = amount_ars
                else:
                    continue

                if not amount or amount <= 0:
                    continue

                if _is_ignored(description):
                    continue

                suggested = "Impuestos" if _is_tax(description) else ""

                results.append(
                    ImportedRow(
                        raw_date=raw_date,
                        description=description,
                        amount=amount,
                        currency=currency,
                        suggested_category_name=suggested,
                    )
                )

    return results
