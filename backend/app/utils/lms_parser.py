"""Parser de archivos de calificaciones exportados del LMS (C-10).

Reglas aplicadas:
- RN-01: columnas numéricas detectadas por sufijo `(Real)`.
- RN-02: columnas textuales detectadas por presencia de valores del conjunto
  aprobatorio/no aprobatorio en sus celdas.

Módulo puro: no tiene dependencias de ORM ni FastAPI.
Entrada: bytes + nombre de archivo.
Salida: ParseResult (Pydantic).

Soporta CSV (utf-8 y latin-1) y XLSX.
"""

import csv
import io
from typing import Any

from pydantic import BaseModel, ConfigDict

# Sufijo que identifica columnas de nota numérica (RN-01)
_SUFIJO_NUMERICO = "(Real)"

# Valores que indican escala textual (RN-02) — usados para detectar el tipo de columna
_VALORES_ESCALA_TEXTUAL = {
    "satisfactorio",
    "supera lo esperado",
    "no satisfactorio",
    "no alcanzado",
    "competente",
    "en proceso",
}

# Columnas de metadata del LMS que NO son actividades
_COLUMNAS_META = {
    "apellido(s)",
    "nombre",
    "dirección de correo electrónico",
    "número de id",
    "estado",
    "institución",
    "departamento",
    "ciudad/pueblo",
    "país",
    "último acceso al curso",
    "calificación del curso",
    "calificación de los ítems de retroalimentación del curso",
    "fecha de inicio",
    "fecha de finalización",
    "tiempo en el curso (hh:mm:ss)",
}


class ActividadParseada(BaseModel):
    """Actividad detectada durante el parseo."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    tipo: str  # "numerica" | "textual"
    col_index: int


class FilaAlumno(BaseModel):
    """Fila de alumno con sus valores por actividad."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    apellidos: str
    # actividad -> valor raw (str) o None
    valores: dict[str, str | None]


class ParseResult(BaseModel):
    """Resultado del parseo del archivo LMS."""

    model_config = ConfigDict(extra="forbid")

    actividades: list[ActividadParseada]
    filas: list[FilaAlumno]
    advertencias: list[str]


def _es_numerico(valor: str) -> bool:
    """True si el string representa un número."""
    try:
        float(valor.replace(",", "."))
        return True
    except (ValueError, AttributeError):
        return False


def _detectar_tipo_columna(col_nombre: str, valores_columna: list[str]) -> str | None:
    """Determina si una columna es 'numerica', 'textual' o None (ignorar).

    Prioridad: sufijo (Real) → numérica, presencia de valores textuales → textual.
    """
    if col_nombre.strip().endswith(_SUFIJO_NUMERICO):
        return "numerica"

    valores_lower = {v.strip().lower() for v in valores_columna if v.strip()}
    if valores_lower & _VALORES_ESCALA_TEXTUAL:
        return "textual"

    return None


def _parse_filas(
    headers: list[str],
    rows: list[list[str]],
) -> ParseResult:
    """Lógica central de parseo compartida entre CSV y XLSX."""
    advertencias: list[str] = []

    # Detectar columnas de alumnos (nombre, apellidos)
    col_nombre_idx: int | None = None
    col_apellidos_idx: int | None = None

    for i, h in enumerate(headers):
        h_lower = h.strip().lower()
        if h_lower == "nombre":
            col_nombre_idx = i
        elif h_lower in ("apellido(s)", "apellidos"):
            col_apellidos_idx = i

    if col_nombre_idx is None:
        advertencias.append("No se encontró columna 'Nombre' en el archivo.")
    if col_apellidos_idx is None:
        advertencias.append("No se encontró columna 'Apellido(s)' en el archivo.")

    # Detectar actividades (columnas no-meta)
    actividades: list[ActividadParseada] = []
    for i, h in enumerate(headers):
        if h.strip().lower() in _COLUMNAS_META:
            continue
        # Recopilar valores de la columna para inferir tipo
        valores_col = [
            row[i].strip() for row in rows if i < len(row) and row[i].strip()
        ]
        tipo = _detectar_tipo_columna(h, valores_col)
        if tipo:
            actividades.append(ActividadParseada(nombre=h.strip(), tipo=tipo, col_index=i))

    if not actividades:
        advertencias.append(
            "No se detectaron actividades válidas. "
            "Verificá que las columnas numéricas terminen en '(Real)'."
        )

    # Construir filas de alumnos
    filas: list[FilaAlumno] = []
    for row in rows:
        if not any(c.strip() for c in row):
            continue  # fila vacía

        nombre = row[col_nombre_idx].strip() if col_nombre_idx is not None and col_nombre_idx < len(row) else ""
        apellidos = row[col_apellidos_idx].strip() if col_apellidos_idx is not None and col_apellidos_idx < len(row) else ""

        if not nombre and not apellidos:
            continue

        valores: dict[str, str | None] = {}
        for act in actividades:
            raw = row[act.col_index].strip() if act.col_index < len(row) else ""
            valores[act.nombre] = raw if raw else None

        filas.append(FilaAlumno(nombre=nombre, apellidos=apellidos, valores=valores))

    return ParseResult(actividades=actividades, filas=filas, advertencias=advertencias)


def _parse_csv(content: bytes) -> tuple[list[str], list[list[str]]]:
    """Parsea CSV intentando utf-8, luego latin-1."""
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            text = content.decode(encoding)
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
            if not rows:
                return [], []
            return rows[0], rows[1:]
        except UnicodeDecodeError:
            continue
    raise ValueError("No se pudo decodificar el archivo CSV.")


def _parse_xlsx(content: bytes) -> tuple[list[str], list[list[str]]]:
    """Parsea XLSX usando openpyxl."""
    try:
        import openpyxl  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("openpyxl es requerido para parsear archivos XLSX.") from exc

    wb = openpyxl.load_workbook(filename=io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    if ws is None:
        return [], []

    all_rows: list[list[str]] = []
    for row in ws.iter_rows(values_only=True):
        all_rows.append([str(cell) if cell is not None else "" for cell in row])

    wb.close()
    if not all_rows:
        return [], []
    return all_rows[0], all_rows[1:]


def parse_calificaciones(file_bytes: bytes, filename: str) -> ParseResult:
    """Parsea un archivo de calificaciones del LMS (CSV o XLSX).

    Args:
        file_bytes: contenido del archivo.
        filename: nombre del archivo para detectar extensión.

    Returns:
        ParseResult con actividades detectadas y filas de alumnos.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "xlsx":
        headers, rows = _parse_xlsx(file_bytes)
    else:
        headers, rows = _parse_csv(file_bytes)

    return _parse_filas(headers, rows)
