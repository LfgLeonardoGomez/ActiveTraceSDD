"""Excepciones de dominio del módulo liquidaciones (C-18).

Cada excepción mapea a un HTTP status code específico via exception handler.
"""


class LiquidacionCerradaError(Exception):
    """Intento de mutar una liquidación con estado=Cerrada (D3).

    Mapeado a 409 Conflict por el exception handler del módulo.
    """

    def __init__(self, liquidacion_id=None):
        super().__init__(f"La liquidación {liquidacion_id} está cerrada y es inmutable")
        self.liquidacion_id = liquidacion_id


class VigenciaSolapadaError(Exception):
    """Intento de crear/modificar registro con vigencia solapada (D5).

    Mapeado a 409 Conflict por el exception handler del módulo.
    """

    def __init__(self, tabla: str, registro_id=None):
        super().__init__(
            f"Vigencia se solapa con registro existente {registro_id} en {tabla}"
        )
        self.tabla = tabla
        self.registro_id = registro_id


class PeriodoYaCerradoError(Exception):
    """Intento de cerrar un período que ya tiene liquidaciones Cerradas.

    Mapeado a 409 Conflict.
    """

    def __init__(self, cohorte_id=None, periodo: str = ""):
        super().__init__(f"El período {periodo} de la cohorte {cohorte_id} ya está cerrado")
        self.cohorte_id = cohorte_id
        self.periodo = periodo


class UsuarioNoFacturanteError(Exception):
    """Intento de cargar factura para usuario con facturador=False.

    Mapeado a 422 Unprocessable Entity.
    """

    def __init__(self, usuario_id=None):
        super().__init__(f"El usuario {usuario_id} no está registrado como facturante")
        self.usuario_id = usuario_id


class FacturaYaAbonadaError(Exception):
    """Intento de abonar una factura ya en estado=Abonada.

    Mapeado a 409 Conflict.
    """

    def __init__(self, factura_id=None):
        super().__init__(f"La factura {factura_id} ya fue abonada")
        self.factura_id = factura_id
