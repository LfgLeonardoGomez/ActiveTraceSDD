"""Parser del reporte de finalización de actividades del LMS (C-10).

Detecta actividades finalizadas por alumno en el reporte de finalización
exportado desde Moodle. El resultado se cruza con las calificaciones en
FinalizacionService para identificar entregas sin corregir (RN-07, RN-08).

Módulo puro: no tiene dependencias de ORM ni FastAPI.
"""

import csv
import io

from pydantic import BaseModel, ConfigDict

# Valores que Moodle usa para indicar "finalizado"
_VALORES_FINALIZADO = {"completado", "finalizado", "complete", "completed", "sí", "si", "yes", "true", "1"}


class FilaFinalizacion(BaseModel):
    """Fila del reporte: alumno + actividad + estado de finalización."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    apellidos: str
    actividad: str
    finalizado: bool


class FinalizacionResult(BaseModel):
    """Resultado del parseo del reporte de finalización."""

    model_config = ConfigDict(extra="forbid")

    filas: list[FilaFinalizacion]
    advertencias: list[str]


def _parse_csv_finalizacion(content: bytes) -> tuple[list[str], list[list[str]]]:
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


def _parse_xlsx_finalizacion(content: bytes) -> tuple[list[str], list[list[str]]]:
    try:
        import openpyxl  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("openpyxl es requerido para parsear archivos XLSX.") from exc

    wb = openpyxl.load_workbook(filename=io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    if ws is None:
        return [], []
    all_rows = [[str(c) if c is not None else "" for c in row] for row in ws.iter_rows(values_only=True)]
    wb.close()
    if not all_rows:
        return [], []
    return all_rows[0], all_rows[1:]


def parse_finalizacion(file_bytes: bytes, filename: str) -> FinalizacionResult:
    """Parsea el reporte de finalización de actividades del LMS.

    Formato esperado: columnas Nombre, Apellido(s) + una columna por actividad
    con estado de finalización (Completado / Finalizado / etc).

    Returns:
        FinalizacionResult con filas de (alumno, actividad, finalizado).
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "xlsx":
        headers, rows = _parse_xlsx_finalizacion(file_bytes)
    else:
        headers, rows = _parse_csv_finalizacion(file_bytes)

    advertencias: list[str] = []
    filas: list[FilaFinalizacion] = []

    if not headers:
        return FinalizacionResult(filas=[], advertencias=["Archivo vacío."])

    headers_lower = [h.strip().lower() for h in headers]

    col_nombre = next((i for i, h in enumerate(headers_lower) if h == "nombre"), None)
    col_apellidos = next(
        (i for i, h in enumerate(headers_lower) if h in ("apellido(s)", "apellidos")), None
    )

    if col_nombre is None or col_apellidos is None:
        advertencias.append("No se encontraron columnas Nombre / Apellido(s).")
        return FinalizacionResult(filas=[], advertencias=advertencias)

    # Columnas de actividades: cualquier columna que no sea metadata de alumno
    _meta = {"nombre", "apellido(s)", "apellidos", "número de id", "dirección de correo electrónico"}
    actividades_cols = [(i, headers[i].strip()) for i, h in enumerate(headers_lower) if h not in _meta]

    for row in rows:
        if not any(c.strip() for c in row):
            continue

        nombre = row[col_nombre].strip() if col_nombre < len(row) else ""
        apellidos = row[col_apellidos].strip() if col_apellidos < len(row) else ""

        if not nombre and not apellidos:
            continue

        for col_idx, actividad_nombre in actividades_cols:
            valor = row[col_idx].strip().lower() if col_idx < len(row) else ""
            finalizado = valor in _VALORES_FINALIZADO
            filas.append(
                FilaFinalizacion(
                    nombre=nombre,
                    apellidos=apellidos,
                    actividad=actividad_nombre,
                    finalizado=finalizado,
                )
            )

    return FinalizacionResult(filas=filas, advertencias=advertencias)
