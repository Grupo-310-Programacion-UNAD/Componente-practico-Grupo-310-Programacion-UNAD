"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        SISTEMA INTEGRAL DE GESTIÓN DE CLIENTES, SERVICIOS Y RESERVAS        ║
║                     Empresa: Software FJ — Fase 4                           ║
║             Curso: Programación 213023 — UNAD                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

Descripción:
    Sistema orientado a objetos para gestionar clientes, servicios y reservas
    de la empresa Software FJ, sin uso de base de datos. Implementa:
      • Abstracción     → clases abstractas EntidadSistema y Servicio
      • Herencia        → Cliente, ReservaSala, AlquilerEquipo, AsesoriaEspecializada
      • Polimorfismo    → calcular_costo() y describir() redefinidos en cada servicio
      • Encapsulación   → atributos privados con propiedades y setters validados
      • Excepciones     → jerarquía propia, try/except/else/finally, encadenamiento
      • Logs            → registro de todos los eventos en archivo .log
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTACIONES
# ─────────────────────────────────────────────────────────────────────────────
import re                            # Validaciones con expresiones regulares
import logging                       # Registro de eventos en archivo
import uuid                          # Generación de IDs únicos
import datetime                      # Fechas y horas
from abc import ABC, abstractmethod  # Clases y métodos abstractos
from typing import Optional          # Tipado opcional


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — CONFIGURACIÓN DEL SISTEMA DE LOGS
# ═════════════════════════════════════════════════════════════════════════════

LOG_FILE = "softwarefj_eventos.log"

def configurar_logger() -> logging.Logger:
    """
    Configura el logger con dos destinos:
      - Archivo .log : guarda TODOS los niveles (DEBUG en adelante)
      - Consola      : muestra solo WARNING en adelante

    Returns:
        logging.Logger: instancia configurada y lista para usar.
    """
    logger = logging.getLogger("SistemaFJ")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:          # Evita duplicar manejadores en reinicios
        return logger

    # Manejador 1 — archivo
    mh_archivo = logging.FileHandler(LOG_FILE, encoding="utf-8")
    mh_archivo.setLevel(logging.DEBUG)

    # Manejador 2 — consola
    mh_consola = logging.StreamHandler()
    mh_consola.setLevel(logging.WARNING)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    mh_archivo.setFormatter(fmt)
    mh_consola.setFormatter(fmt)

    logger.addHandler(mh_archivo)
    logger.addHandler(mh_consola)
    return logger


logger = configurar_logger()   # Logger global del sistema


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — EXCEPCIONES PERSONALIZADAS
# ═════════════════════════════════════════════════════════════════════════════

class ErrorSistemaFJ(Exception):
    """
    Excepción base del sistema Software FJ.
    Todas las excepciones propias heredan de esta clase.
    Incluye código numérico y timestamp para trazabilidad.
    """
    def __init__(self, mensaje: str, codigo: int = 0):
        super().__init__(mensaje)
        self.mensaje   = mensaje
        self.codigo    = codigo
        self.timestamp = datetime.datetime.now()

    def __str__(self):
        return (
            f"[Error {self.codigo}] {self.mensaje} "
            f"(ocurrido: {self.timestamp.strftime('%H:%M:%S')})"
        )


class ErrorClienteInvalido(ErrorSistemaFJ):
    """Datos del cliente no superan las validaciones (código 100)."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo=100)


class ErrorServicioInvalido(ErrorSistemaFJ):
    """Parámetros del servicio incorrectos o servicio inactivo (código 200)."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo=200)


class ErrorReservaInvalida(ErrorSistemaFJ):
    """Reserva con datos incorrectos o en estado no permitido (código 300)."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo=300)


class ErrorOperacionNoPermitida(ErrorSistemaFJ):
    """Operación inválida para el estado actual de la entidad (código 400)."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo=400)


class ErrorCalculoCosto(ErrorSistemaFJ):
    """Cálculo de costo produce resultado incoherente (código 500)."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo=500)


class ErrorParametroFaltante(ErrorSistemaFJ):
    """Parámetro obligatorio ausente o vacío (código 600)."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo=600)


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — UTILIDADES DE PRESENTACIÓN EN CONSOLA
# ═════════════════════════════════════════════════════════════════════════════

def separador(titulo: str = "", ancho: int = 62) -> None:
    """Imprime una línea separadora con título opcional centrado."""
    if titulo:
        print(f"\n  ┌{'─' * (ancho - 4)}┐")
        print(f"  │{titulo.center(ancho - 4)}│")
        print(f"  └{'─' * (ancho - 4)}┘")
    else:
        print(f"  {'─' * (ancho - 2)}")


def fila_resultado(op: str, descripcion: str, estado: str, detalle: str = "") -> None:
    """
    Imprime una fila formateada de resultado de operación.

    Args:
        op          : número u etiqueta de la operación.
        descripcion : qué se intentó hacer.
        estado      : '✔ OK' o '✗ ERROR'.
        detalle     : información adicional (costo, mensaje de error, etc.).
    """
    icono = "✔" if "OK" in estado else "✗"
    color_estado = estado.replace("✔ ", "").replace("✗ ", "")
    print(f"  │ {op:<5} │ {descripcion:<28} │ {icono} {color_estado:<10} │ {detalle:<18} │")


def encabezado_tabla(col1="Op.", col2="Descripción", col3="Estado", col4="Detalle") -> None:
    """Imprime el encabezado de una tabla de resultados."""
    print(f"\n  ┌{'─'*7}┬{'─'*30}┬{'─'*13}┬{'─'*20}┐")
    print(f"  │ {col1:<5} │ {col2:<28} │ {col3:<11} │ {col4:<18} │")
    print(f"  ├{'─'*7}┼{'─'*30}┼{'─'*13}┼{'─'*20}┤")


def pie_tabla() -> None:
    """Imprime el cierre de una tabla."""
    print(f"  └{'─'*7}┴{'─'*30}┴{'─'*13}┴{'─'*20}┘")


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — CLASE ABSTRACTA BASE: EntidadSistema
# ═════════════════════════════════════════════════════════════════════════════

class EntidadSistema(ABC):
    """
    Clase abstracta raíz de la jerarquía del sistema.
    Toda entidad (cliente, servicio, reserva) hereda de aquí.

    Atributos protegidos:
        _id             (str)      : identificador único (UUID corto).
        _fecha_registro (datetime) : timestamp de creación.
        _activo         (bool)     : estado activo/inactivo.
    """

    def __init__(self) -> None:
        self._id             = str(uuid.uuid4())[:8].upper()
        self._fecha_registro = datetime.datetime.now()
        self._activo         = True

    # ── Propiedades de solo lectura ──────────────────────────────────────────

    @property
    def id(self) -> str:
        """ID único de la entidad."""
        return self._id

    @property
    def fecha_registro(self) -> datetime.datetime:
        """Fecha y hora de creación."""
        return self._fecha_registro

    @property
    def activo(self) -> bool:
        """True si la entidad está activa."""
        return self._activo

    @activo.setter
    def activo(self, valor: bool) -> None:
        if not isinstance(valor, bool):
            raise ErrorSistemaFJ("El estado activo debe ser True o False.", codigo=1)
        self._activo = valor

    # ── Métodos abstractos obligatorios ─────────────────────────────────────

    @abstractmethod
    def obtener_info(self) -> str:
        """Descripción completa de la entidad."""
        pass

    @abstractmethod
    def validar(self) -> bool:
        """Valida integridad interna de la entidad."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id}, activo={self._activo})"


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — CLASE CLIENTE
# ═════════════════════════════════════════════════════════════════════════════

class Cliente(EntidadSistema):
    """
    Representa un cliente de Software FJ.
    Encapsula datos personales con validación en cada setter.

    Atributos privados:
        __nombre    (str) : nombre completo.
        __email     (str) : correo electrónico.
        __telefono  (str) : número telefónico (solo dígitos).
        __documento (str) : número de documento de identidad.
        __reservas  (list): historial de reservas.
    """

    _PATRON_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$")

    def __init__(
        self, nombre: str, email: str, telefono: str, documento: str
    ) -> None:
        """
        Crea un cliente validando todos los campos.

        Raises:
            ErrorParametroFaltante: campo vacío o None.
            ErrorClienteInvalido:   formato incorrecto en email o teléfono.
        """
        super().__init__()
        self.nombre    = nombre     # Llama al setter con validación
        self.email     = email
        self.telefono  = telefono
        self.documento = documento
        self.__reservas: list = []
        logger.info(f"Cliente creado: {nombre} | Doc: {documento} | ID: {self._id}")

    # ── Setters con validación (encapsulación) ───────────────────────────────

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not valor or not str(valor).strip():
            raise ErrorParametroFaltante("El nombre del cliente no puede estar vacío.")
        valor = valor.strip()
        if len(valor) < 3:
            raise ErrorClienteInvalido(
                f"El nombre '{valor}' es demasiado corto (mínimo 3 caracteres)."
            )
        if not re.match(r"^[A-Za-záéíóúÁÉÍÓÚüÜñÑ\s]+$", valor):
            raise ErrorClienteInvalido(
                f"El nombre '{valor}' contiene caracteres no permitidos."
            )
        self.__nombre = valor

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, valor: str) -> None:
        if not valor or not str(valor).strip():
            raise ErrorParametroFaltante("El email no puede estar vacío.")
        if not self._PATRON_EMAIL.match(valor.strip()):
            raise ErrorClienteInvalido(f"El email '{valor}' no tiene formato válido.")
        self.__email = valor.strip().lower()

    @property
    def telefono(self) -> str:
        return self.__telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        if not valor or not str(valor).strip():
            raise ErrorParametroFaltante("El teléfono no puede estar vacío.")
        valor = valor.strip().replace(" ", "").replace("-", "")
        if not valor.isdigit():
            raise ErrorClienteInvalido(
                f"El teléfono '{valor}' debe contener solo dígitos."
            )
        if not (7 <= len(valor) <= 15):
            raise ErrorClienteInvalido(
                f"El teléfono debe tener entre 7 y 15 dígitos. Recibido: {len(valor)}."
            )
        self.__telefono = valor

    @property
    def documento(self) -> str:
        return self.__documento

    @documento.setter
    def documento(self, valor: str) -> None:
        if not valor or not str(valor).strip():
            raise ErrorParametroFaltante("El documento no puede estar vacío.")
        valor = valor.strip()
        if not (6 <= len(valor) <= 12):
            raise ErrorClienteInvalido(
                f"El documento debe tener entre 6 y 12 caracteres. Recibido: '{valor}'."
            )
        self.__documento = valor

    @property
    def reservas(self) -> list:
        """Copia de la lista interna de reservas (protección del original)."""
        return list(self.__reservas)

    # ── Métodos de negocio ───────────────────────────────────────────────────

    def agregar_reserva(self, reserva: "Reserva") -> None:
        """Vincula una reserva al historial del cliente."""
        if reserva is None:
            raise ErrorParametroFaltante("La reserva no puede ser None.")
        self.__reservas.append(reserva)
        logger.debug(f"Reserva {reserva.id} agregada al cliente {self.__nombre}.")

    def total_reservas(self) -> int:
        return len(self.__reservas)

    # ── Métodos abstractos implementados ────────────────────────────────────

    def obtener_info(self) -> str:
        return (
            f"\n  {'═'*48}\n"
            f"  CLIENTE | ID: {self._id}\n"
            f"  {'─'*48}\n"
            f"  Nombre    : {self.__nombre}\n"
            f"  Email     : {self.__email}\n"
            f"  Teléfono  : {self.__telefono}\n"
            f"  Documento : {self.__documento}\n"
            f"  Reservas  : {len(self.__reservas)}\n"
            f"  Activo    : {'Sí' if self._activo else 'No'}\n"
            f"  {'═'*48}"
        )

    def validar(self) -> bool:
        try:
            assert self.__nombre and len(self.__nombre) >= 3
            assert "@" in self.__email
            assert self.__telefono.isdigit()
            assert len(self.__documento) >= 6
            return True
        except AssertionError:
            return False


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — CLASE ABSTRACTA SERVICIO + TRES SERVICIOS ESPECIALIZADOS
# ═════════════════════════════════════════════════════════════════════════════

class Servicio(EntidadSistema, ABC):
    """
    Clase abstracta que define la interfaz común de todos los servicios.
    Implementa HERENCIA y establece el contrato para POLIMORFISMO.
    """

    IVA = 0.19   # IVA colombiano del 19 % aplicado a todos los servicios

    def __init__(
        self, nombre: str, descripcion: str, precio_hora: float, capacidad: int
    ) -> None:
        """
        Raises:
            ErrorParametroFaltante: campo vacío.
            ErrorServicioInvalido:  precio o capacidad inválidos.
        """
        super().__init__()
        self.nombre      = nombre
        self.descripcion = descripcion
        self.precio_hora = precio_hora
        self.capacidad   = capacidad
        self._disponible = True
        logger.info(
            f"Servicio creado: {nombre} | ${precio_hora:,.0f}/h | ID: {self._id}"
        )

    # ── Propiedades ──────────────────────────────────────────────────────────

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not valor or len(str(valor).strip()) < 3:
            raise ErrorParametroFaltante(
                "El nombre del servicio debe tener al menos 3 caracteres."
            )
        self.__nombre = valor.strip()

    @property
    def descripcion(self) -> str:
        return self.__descripcion

    @descripcion.setter
    def descripcion(self, valor: str) -> None:
        if not valor or not str(valor).strip():
            raise ErrorParametroFaltante("La descripción no puede estar vacía.")
        self.__descripcion = valor.strip()

    @property
    def precio_hora(self) -> float:
        return self.__precio_hora

    @precio_hora.setter
    def precio_hora(self, valor) -> None:
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            raise ErrorServicioInvalido(f"El precio '{valor}' no es un número válido.")
        if valor <= 0:
            raise ErrorServicioInvalido(
                f"El precio por hora debe ser mayor a cero. Recibido: {valor}"
            )
        self.__precio_hora = valor

    @property
    def capacidad(self) -> int:
        return self.__capacidad

    @capacidad.setter
    def capacidad(self, valor) -> None:
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            raise ErrorServicioInvalido(f"La capacidad '{valor}' no es un entero válido.")
        if valor <= 0:
            raise ErrorServicioInvalido(
                f"La capacidad debe ser mayor a cero. Recibido: {valor}"
            )
        self.__capacidad = valor

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, valor: bool) -> None:
        self._disponible = bool(valor)
        estado = "activado" if self._disponible else "desactivado"
        logger.info(f"Servicio '{self.__nombre}' {estado}.")

    # ── Métodos protegidos reutilizables por subclases ───────────────────────

    def _validar_horas(self, horas) -> float:
        """Valida que las horas sean un número positivo."""
        try:
            horas = float(horas)
        except (TypeError, ValueError):
            raise ErrorCalculoCosto(f"Las horas '{horas}' no son un valor numérico.")
        if horas <= 0:
            raise ErrorCalculoCosto(
                f"Las horas deben ser mayores a cero. Recibido: {horas}"
            )
        return horas

    def _validar_descuento(self, descuento) -> float:
        """Valida que el descuento esté en el rango [0.0, 1.0]."""
        try:
            descuento = float(descuento)
        except (TypeError, ValueError):
            raise ErrorCalculoCosto(f"El descuento '{descuento}' no es numérico.")
        if not (0.0 <= descuento <= 1.0):
            raise ErrorCalculoCosto(
                f"El descuento debe estar entre 0.0 y 1.0. Recibido: {descuento}"
            )
        return descuento

    def verificar_disponibilidad(self) -> None:
        """Lanza excepción si el servicio no está disponible."""
        if not self._disponible:
            raise ErrorServicioInvalido(
                f"El servicio '{self.__nombre}' no está disponible en este momento."
            )

    # ── Métodos abstractos (POLIMORFISMO) ────────────────────────────────────

    @abstractmethod
    def calcular_costo(
        self, horas: float, descuento: float = 0.0, con_iva: bool = True
    ) -> float:
        """Calcula el costo del servicio. Cada subclase tiene su propia lógica."""
        pass

    @abstractmethod
    def describir(self) -> str:
        """Descripción detallada y específica del servicio."""
        pass

    @abstractmethod
    def validar_parametros(self, horas: float, personas: int) -> bool:
        """Valida que los parámetros de uso sean compatibles con el servicio."""
        pass

    # ── Métodos concretos de EntidadSistema ──────────────────────────────────

    def obtener_info(self) -> str:
        return self.describir()

    def validar(self) -> bool:
        return (
            bool(self.__nombre)
            and self.__precio_hora > 0
            and self.__capacidad > 0
            and self._activo
        )


# ─────────────────────────────────────────────────────────────────────────────
# 6.1 — ReservaSala
# ─────────────────────────────────────────────────────────────────────────────

class ReservaSala(Servicio):
    """
    Servicio de reserva de salas de reuniones o conferencias.

    Sobrecarga simulada:
      - calcular_costo()          → tarifa base + IVA opcional + descuento.
      - calcular_costo_extendido()→ agrega cargo por audiovisual y horas extra.
    """

    CARGO_AUDIOVISUAL = 50_000.0   # Cargo fijo por hora cuando hay audiovisual

    def __init__(
        self,
        nombre: str,
        capacidad: int,
        precio_hora: float,
        tiene_audiovisual: bool = False,
    ) -> None:
        descripcion = f"Sala de reuniones — capacidad {capacidad} personas"
        super().__init__(nombre, descripcion, precio_hora, capacidad)
        self.__tiene_audiovisual = bool(tiene_audiovisual)

    @property
    def tiene_audiovisual(self) -> bool:
        return self.__tiene_audiovisual

    # ── calcular_costo (método base — POLIMORFISMO) ──────────────────────────

    def calcular_costo(
        self, horas: float, descuento: float = 0.0, con_iva: bool = True
    ) -> float:
        """
        Costo base de la sala.
        Fórmula: precio_hora * horas * (1 - descuento) [* 1.19 si con_iva]
        """
        horas     = self._validar_horas(horas)
        descuento = self._validar_descuento(descuento)
        self.verificar_disponibilidad()

        subtotal = self.precio_hora * horas * (1 - descuento)
        total    = subtotal * (1 + self.IVA) if con_iva else subtotal

        logger.debug(
            f"[ReservaSala '{self.nombre}'] Costo: ${total:,.0f} "
            f"({horas}h | desc={descuento*100:.0f}% | IVA={'Sí' if con_iva else 'No'})"
        )
        return round(total, 2)

    # ── calcular_costo_extendido (SOBRECARGA SIMULADA) ───────────────────────

    def calcular_costo_extendido(
        self,
        horas: float,
        descuento: float = 0.0,
        con_iva: bool = True,
        horas_extra: float = 0.0,
    ) -> float:
        """
        Variante extendida: agrega cargo audiovisual y recargo por horas extra.

        Args:
            horas_extra (float): horas adicionales con recargo del 30 %.
        """
        horas       = self._validar_horas(horas)
        descuento   = self._validar_descuento(descuento)
        horas_extra = max(0.0, float(horas_extra))
        self.verificar_disponibilidad()

        precio_base = self.precio_hora
        if self.__tiene_audiovisual:
            precio_base += self.CARGO_AUDIOVISUAL

        subtotal  = precio_base * horas * (1 - descuento)
        subtotal += precio_base * horas_extra * 1.30   # Recargo 30 % por extra
        total     = subtotal * (1 + self.IVA) if con_iva else subtotal

        logger.debug(
            f"[ReservaSala '{self.nombre}'] Costo extendido: ${total:,.0f} "
            f"({horas}h + {horas_extra}h extra | audio={'Sí' if self.__tiene_audiovisual else 'No'})"
        )
        return round(total, 2)

    def describir(self) -> str:
        audio = "Sí (+ $50,000/h)" if self.__tiene_audiovisual else "No"
        return (
            f"\n  {'─'*48}\n"
            f"  SALA DE REUNIONES | ID: {self.id}\n"
            f"  {'─'*48}\n"
            f"  Nombre       : {self.nombre}\n"
            f"  Capacidad    : {self.capacidad} personas\n"
            f"  Precio/hora  : ${self.precio_hora:,.0f}\n"
            f"  Audiovisual  : {audio}\n"
            f"  Disponible   : {'Sí' if self.disponible else 'No'}\n"
            f"  {'─'*48}"
        )

    def validar_parametros(self, horas: float, personas: int) -> bool:
        horas = self._validar_horas(horas)
        if personas <= 0:
            raise ErrorReservaInvalida("El número de personas debe ser mayor a cero.")
        if personas > self.capacidad:
            raise ErrorReservaInvalida(
                f"La sala '{self.nombre}' tiene capacidad para {self.capacidad} personas. "
                f"Solicitadas: {personas}."
            )
        return True


# ─────────────────────────────────────────────────────────────────────────────
# 6.2 — AlquilerEquipo
# ─────────────────────────────────────────────────────────────────────────────

class AlquilerEquipo(Servicio):
    """
    Servicio de alquiler de equipos tecnológicos.

    Sobrecarga simulada:
      - calcular_costo()          → costo por 1 equipo.
      - calcular_costo_multiple() → costo para N equipos con descuento por volumen.
    """

    def __init__(
        self,
        nombre: str,
        tipo_equipo: str,
        cantidad_disponible: int,
        precio_hora: float,
    ) -> None:
        if not tipo_equipo or not str(tipo_equipo).strip():
            raise ErrorParametroFaltante("El tipo de equipo no puede estar vacío.")
        descripcion = f"Alquiler de {tipo_equipo} — {cantidad_disponible} unidades"
        super().__init__(nombre, descripcion, precio_hora, cantidad_disponible)
        self.__tipo_equipo = tipo_equipo.strip()

    @property
    def tipo_equipo(self) -> str:
        return self.__tipo_equipo

    def calcular_costo(
        self, horas: float, descuento: float = 0.0, con_iva: bool = True
    ) -> float:
        """
        Costo por 1 equipo.
        Fórmula: precio_hora * horas * (1 - descuento) [* 1.19 si con_iva]
        """
        horas     = self._validar_horas(horas)
        descuento = self._validar_descuento(descuento)
        self.verificar_disponibilidad()

        subtotal = self.precio_hora * horas * (1 - descuento)
        total    = subtotal * (1 + self.IVA) if con_iva else subtotal

        logger.debug(
            f"[AlquilerEquipo '{self.nombre}'] Costo 1 equipo: ${total:,.0f} ({horas}h)"
        )
        return round(total, 2)

    def calcular_costo_multiple(
        self,
        horas: float,
        cantidad: int,
        descuento: float = 0.0,
        con_iva: bool = True,
    ) -> float:
        """
        SOBRECARGA SIMULADA: costo para múltiples equipos.
        Aplica descuento automático por volumen (5 % adicional por cada 3 equipos).

        Args:
            cantidad (int): número de equipos a alquilar.
        """
        horas     = self._validar_horas(horas)
        descuento = self._validar_descuento(descuento)
        self.verificar_disponibilidad()

        if cantidad <= 0:
            raise ErrorCalculoCosto(
                f"La cantidad debe ser mayor a cero. Recibido: {cantidad}"
            )
        if cantidad > self.capacidad:
            raise ErrorCalculoCosto(
                f"Solo hay {self.capacidad} equipos disponibles. "
                f"Solicitados: {cantidad}."
            )

        # Descuento adicional por volumen: 5 % por cada bloque de 3 equipos
        desc_volumen = (cantidad // 3) * 0.05
        desc_total   = min(descuento + desc_volumen, 0.50)  # Máximo 50 %

        subtotal = self.precio_hora * horas * cantidad * (1 - desc_total)
        total    = subtotal * (1 + self.IVA) if con_iva else subtotal

        logger.debug(
            f"[AlquilerEquipo '{self.nombre}'] Costo múltiple: ${total:,.0f} "
            f"({cantidad} equipos × {horas}h | desc_total={desc_total*100:.0f}%)"
        )
        return round(total, 2)

    def describir(self) -> str:
        return (
            f"\n  {'─'*48}\n"
            f"  ALQUILER DE EQUIPO | ID: {self.id}\n"
            f"  {'─'*48}\n"
            f"  Servicio      : {self.nombre}\n"
            f"  Tipo equipo   : {self.__tipo_equipo}\n"
            f"  Unidades disp.: {self.capacidad}\n"
            f"  Precio/equipo/h: ${self.precio_hora:,.0f}\n"
            f"  Disponible    : {'Sí' if self.disponible else 'No'}\n"
            f"  {'─'*48}"
        )

    def validar_parametros(self, horas: float, personas: int) -> bool:
        horas = self._validar_horas(horas)
        if personas > self.capacidad:
            raise ErrorReservaInvalida(
                f"Solo hay {self.capacidad} equipos disponibles. "
                f"Solicitados: {personas}."
            )
        return True


# ─────────────────────────────────────────────────────────────────────────────
# 6.3 — AsesoriaEspecializada
# ─────────────────────────────────────────────────────────────────────────────

class AsesoriaEspecializada(Servicio):
    """
    Servicio de asesoría técnica o legal por expertos.

    Sobrecarga simulada:
      - calcular_costo()         → tarifa según nivel del asesor.
      - calcular_costo_paquete() → varias sesiones con descuento adicional del 5 %.
    """

    NIVELES = {"junior": 1.0, "senior": 1.5, "experto": 2.0}

    def __init__(
        self,
        nombre: str,
        area: str,
        nivel_asesor: str,
        precio_hora: float,
        horas_minimas: float = 1.0,
    ) -> None:
        nivel = str(nivel_asesor).lower().strip()
        if nivel not in self.NIVELES:
            raise ErrorServicioInvalido(
                f"Nivel '{nivel_asesor}' no válido. Use: junior, senior o experto."
            )
        if not area or not str(area).strip():
            raise ErrorParametroFaltante("El área de la asesoría no puede estar vacía.")

        descripcion = f"Asesoría en {area} — nivel {nivel}"
        super().__init__(nombre, descripcion, precio_hora, 1)

        self.__area          = area.strip()
        self.__nivel_asesor  = nivel
        self.__horas_minimas = float(horas_minimas)
        self.__multiplicador = self.NIVELES[nivel]

    @property
    def nivel_asesor(self) -> str:
        return self.__nivel_asesor

    @property
    def area(self) -> str:
        return self.__area

    def calcular_costo(
        self, horas: float, descuento: float = 0.0, con_iva: bool = True
    ) -> float:
        """
        Costo con multiplicador según nivel del asesor.
        Fórmula: precio_hora * multiplicador * horas * (1 - descuento) [* 1.19]
        """
        horas     = self._validar_horas(horas)
        descuento = self._validar_descuento(descuento)
        self.verificar_disponibilidad()

        if horas < self.__horas_minimas:
            raise ErrorCalculoCosto(
                f"La asesoría '{self.nombre}' requiere mínimo "
                f"{self.__horas_minimas}h. Solicitadas: {horas}."
            )

        precio_real = self.precio_hora * self.__multiplicador
        subtotal    = precio_real * horas * (1 - descuento)
        total       = subtotal * (1 + self.IVA) if con_iva else subtotal

        logger.debug(
            f"[Asesoria '{self.nombre}'] Costo: ${total:,.0f} "
            f"(nivel={self.__nivel_asesor} × {self.__multiplicador} | {horas}h)"
        )
        return round(total, 2)

    def calcular_costo_paquete(
        self,
        sesiones: int,
        horas_por_sesion: float,
        descuento: float = 0.0,
    ) -> float:
        """
        SOBRECARGA SIMULADA: paquete de varias sesiones.
        Aplica 5 % de descuento adicional por ser paquete.

        Args:
            sesiones        (int):   número de sesiones.
            horas_por_sesion(float): horas por sesión.
        """
        if sesiones <= 0:
            raise ErrorCalculoCosto(
                f"El número de sesiones debe ser mayor a cero. Recibido: {sesiones}"
            )
        # 5 % adicional por paquete
        desc_paquete = min(float(descuento) + 0.05, 1.0)
        costo_sesion = self.calcular_costo(horas_por_sesion, desc_paquete, con_iva=True)
        total        = round(costo_sesion * sesiones, 2)

        logger.debug(
            f"[Asesoria '{self.nombre}'] Paquete: ${total:,.0f} "
            f"({sesiones} sesiones × {horas_por_sesion}h)"
        )
        return total

    def describir(self) -> str:
        precio_real = self.precio_hora * self.__multiplicador
        return (
            f"\n  {'─'*48}\n"
            f"  ASESORÍA ESPECIALIZADA | ID: {self.id}\n"
            f"  {'─'*48}\n"
            f"  Servicio      : {self.nombre}\n"
            f"  Área          : {self.__area}\n"
            f"  Nivel asesor  : {self.__nivel_asesor.capitalize()}\n"
            f"  Precio base/h : ${self.precio_hora:,.0f}\n"
            f"  Precio real/h : ${precio_real:,.0f} (× {self.__multiplicador})\n"
            f"  Horas mínimas : {self.__horas_minimas}h\n"
            f"  Disponible    : {'Sí' if self.disponible else 'No'}\n"
            f"  {'─'*48}"
        )

    def validar_parametros(self, horas: float, personas: int) -> bool:
        horas = self._validar_horas(horas)
        if horas < self.__horas_minimas:
            raise ErrorReservaInvalida(
                f"La asesoría requiere mínimo {self.__horas_minimas}h. "
                f"Solicitadas: {horas}."
            )
        return True


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — CLASE RESERVA
# ═════════════════════════════════════════════════════════════════════════════

class Reserva(EntidadSistema):
    """
    Integra Cliente + Servicio + duración + estado.
    Ciclo de vida: PENDIENTE → CONFIRMADA → PROCESADA
                   PENDIENTE → CANCELADA
                   CONFIRMADA → CANCELADA

    Demuestra:
      - try/except/else/finally en confirmar() y crear reserva
      - Encadenamiento de excepciones (raise X from e)
      - Estados controlados con ErrorOperacionNoPermitida
    """

    ESTADOS = {
        "PENDIENTE"  : "Esperando confirmación",
        "CONFIRMADA" : "Lista para ejecutarse",
        "PROCESADA"  : "Ejecutada exitosamente",
        "CANCELADA"  : "Cancelada",
    }

    def __init__(
        self,
        cliente: Cliente,
        servicio: Servicio,
        horas: float,
        personas: int = 1,
        descuento: float = 0.0,
    ) -> None:
        """
        Raises:
            ErrorParametroFaltante: cliente o servicio son None.
            ErrorReservaInvalida:   parámetros inválidos.
            ErrorServicioInvalido:  servicio inactivo.
        """
        super().__init__()

        # Validaciones de entrada
        if not isinstance(cliente, Cliente):
            raise ErrorParametroFaltante("Se requiere un objeto Cliente válido.")
        if not cliente.activo:
            raise ErrorReservaInvalida(
                f"El cliente '{cliente.nombre}' no está activo."
            )
        if not isinstance(servicio, Servicio):
            raise ErrorParametroFaltante("Se requiere un objeto Servicio válido.")
        if not servicio.disponible:
            raise ErrorServicioInvalido(
                f"El servicio '{servicio.nombre}' no está disponible."
            )

        # Delegar validación específica al servicio (polimorfismo)
        servicio.validar_parametros(horas, personas)

        self.__cliente   = cliente
        self.__servicio  = servicio
        self.__horas     = float(horas)
        self.__personas  = int(personas)
        self.__descuento = float(descuento)
        self.__estado    = "PENDIENTE"
        self.__costo_total        = 0.0
        self.__fecha_confirmacion: Optional[datetime.datetime] = None
        self.__notas     = ""

        cliente.agregar_reserva(self)
        logger.info(
            f"Reserva {self._id} CREADA | "
            f"Cliente: {cliente.nombre} | Servicio: {servicio.nombre} | "
            f"{horas}h | {personas} persona(s)"
        )

    # ── Propiedades de solo lectura ──────────────────────────────────────────

    @property
    def cliente(self)     -> Cliente:  return self.__cliente
    @property
    def servicio(self)    -> Servicio: return self.__servicio
    @property
    def horas(self)       -> float:    return self.__horas
    @property
    def personas(self)    -> int:      return self.__personas
    @property
    def estado(self)      -> str:      return self.__estado
    @property
    def costo_total(self) -> float:    return self.__costo_total

    @property
    def notas(self) -> str:
        return self.__notas

    @notas.setter
    def notas(self, valor: str) -> None:
        self.__notas = str(valor).strip()

    # ── Métodos de ciclo de vida ─────────────────────────────────────────────

    def confirmar(self, con_iva: bool = True) -> float:
        """
        Calcula el costo y cambia el estado a CONFIRMADA.

        Demuestra: try/except/finally + encadenamiento de excepciones.

        Returns:
            float: costo total confirmado.
        """
        try:
            if self.__estado != "PENDIENTE":
                raise ErrorOperacionNoPermitida(
                    f"Solo se confirman reservas PENDIENTES. "
                    f"Estado actual: '{self.__estado}'."
                )

            # calcular_costo usa polimorfismo (cada servicio tiene su versión)
            self.__costo_total = self.__servicio.calcular_costo(
                self.__horas, self.__descuento, con_iva
            )
            self.__estado             = "CONFIRMADA"
            self.__fecha_confirmacion = datetime.datetime.now()

            logger.info(
                f"Reserva {self._id} CONFIRMADA | "
                f"Costo: ${self.__costo_total:,.0f} | "
                f"Cliente: {self.__cliente.nombre}"
            )
            return self.__costo_total

        except ErrorSistemaFJ:
            raise   # Re-lanza excepciones propias sin modificar

        except Exception as e:
            # Encadenamiento: cualquier error inesperado se convierte en ErrorReservaInvalida
            logger.error(f"Error inesperado al confirmar {self._id}: {e}")
            raise ErrorReservaInvalida(
                f"Error inesperado al confirmar la reserva: {e}"
            ) from e   # 'from e' encadena la excepción original

        finally:
            # SIEMPRE se ejecuta, haya error o no
            logger.debug(f"Intento de confirmación de reserva {self._id} finalizado.")

    def cancelar(self, motivo: str = "Sin motivo especificado") -> bool:
        """
        Cancela la reserva. Solo es posible si no está PROCESADA ni ya CANCELADA.

        Raises:
            ErrorOperacionNoPermitida: estado no permite cancelación.
        """
        try:
            if self.__estado in ("PROCESADA", "CANCELADA"):
                raise ErrorOperacionNoPermitida(
                    f"No se puede cancelar una reserva en estado '{self.__estado}'."
                )
            self.__estado = "CANCELADA"
            self.__notas  = f"CANCELADA: {motivo}"
            logger.warning(
                f"Reserva {self._id} CANCELADA | Motivo: {motivo} | "
                f"Cliente: {self.__cliente.nombre}"
            )
            return True

        except ErrorOperacionNoPermitida:
            raise

        except Exception as e:
            logger.error(f"Error al cancelar reserva {self._id}: {e}")
            raise ErrorReservaInvalida(
                f"No se pudo cancelar la reserva: {e}"
            ) from e

    def procesar(self) -> bool:
        """
        Marca la reserva como PROCESADA (servicio ejecutado).
        Solo disponible si está CONFIRMADA.

        Demuestra: try/except/finally.
        """
        try:
            if self.__estado != "CONFIRMADA":
                raise ErrorOperacionNoPermitida(
                    f"Solo se procesan reservas CONFIRMADAS. "
                    f"Estado actual: '{self.__estado}'."
                )
            self.__estado = "PROCESADA"
            logger.info(
                f"Reserva {self._id} PROCESADA | "
                f"Servicio: {self.__servicio.nombre}"
            )
            return True

        except ErrorSistemaFJ:
            raise

        except Exception as e:
            logger.error(f"Error al procesar reserva {self._id}: {e}")
            raise ErrorReservaInvalida(
                f"No se pudo procesar la reserva: {e}"
            ) from e

        finally:
            logger.debug(f"Operación de procesamiento de reserva {self._id} finalizada.")

    # ── Métodos abstractos implementados ────────────────────────────────────

    def obtener_info(self) -> str:
        costo_str = f"${self.__costo_total:,.0f}" if self.__costo_total > 0 else "Pendiente"
        return (
            f"\n  {'═'*48}\n"
            f"  RESERVA | ID: {self._id}\n"
            f"  {'─'*48}\n"
            f"  Cliente   : {self.__cliente.nombre}\n"
            f"  Servicio  : {self.__servicio.nombre}\n"
            f"  Horas     : {self.__horas}h\n"
            f"  Personas  : {self.__personas}\n"
            f"  Descuento : {self.__descuento*100:.0f}%\n"
            f"  Costo     : {costo_str}\n"
            f"  Estado    : {self.__estado} — {self.ESTADOS[self.__estado]}\n"
            f"  Notas     : {self.__notas if self.__notas else 'Ninguna'}\n"
            f"  {'═'*48}"
        )

    def validar(self) -> bool:
        return (
            self.__cliente  is not None
            and self.__servicio is not None
            and self.__horas > 0
            and self.__estado in self.ESTADOS
        )


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — GESTOR CENTRAL DEL SISTEMA
# ═════════════════════════════════════════════════════════════════════════════

class GestorSistema:
    """
    Controlador principal de Software FJ.
    Gestiona listas en memoria de clientes, servicios y reservas.
    Expone métodos con manejo de excepciones para cada operación.
    """

    def __init__(self) -> None:
        self.__clientes:  list[Cliente]  = []
        self.__servicios: list[Servicio] = []
        self.__reservas:  list[Reserva]  = []
        logger.info("Sistema Software FJ iniciado.")

    # ── Clientes ─────────────────────────────────────────────────────────────

    def registrar_cliente(
        self, nombre: str, email: str, telefono: str, documento: str
    ) -> Optional[Cliente]:
        """
        Registra un cliente. Demuestra try/except/else.

        Returns:
            Cliente si fue exitoso, None si hubo error.
        """
        try:
            # Verificar documento duplicado
            for c in self.__clientes:
                if c.documento == str(documento).strip():
                    raise ErrorClienteInvalido(
                        f"Ya existe un cliente con el documento '{documento}'."
                    )
            cliente = Cliente(nombre, email, telefono, documento)

        except (ErrorClienteInvalido, ErrorParametroFaltante) as e:
            logger.error(f"Error al registrar cliente '{nombre}': {e}")
            return None

        except Exception as e:
            logger.critical(f"Error crítico al registrar cliente '{nombre}': {e}")
            return None

        else:
            # Solo se ejecuta si NO hubo excepción
            self.__clientes.append(cliente)
            return cliente

    # ── Servicios ─────────────────────────────────────────────────────────────

    def agregar_servicio(self, servicio: Servicio) -> bool:
        """Agrega un servicio al catálogo."""
        try:
            if not isinstance(servicio, Servicio):
                raise ErrorServicioInvalido("El objeto no es un Servicio válido.")
            if not servicio.validar():
                raise ErrorServicioInvalido("El servicio no pasó la validación interna.")
            self.__servicios.append(servicio)
            return True

        except ErrorServicioInvalido as e:
            logger.error(f"Error al agregar servicio: {e}")
            return False

    # ── Reservas ──────────────────────────────────────────────────────────────

    def crear_reserva(
        self,
        cliente: Cliente,
        servicio: Servicio,
        horas: float,
        personas: int = 1,
        descuento: float = 0.0,
    ) -> Optional[Reserva]:
        """Crea una reserva. Demuestra try/except/finally."""
        reserva = None
        try:
            reserva = Reserva(cliente, servicio, horas, personas, descuento)
            self.__reservas.append(reserva)

        except (ErrorReservaInvalida, ErrorServicioInvalido,
                ErrorClienteInvalido, ErrorParametroFaltante) as e:
            logger.error(f"Error al crear reserva: {e}")

        except Exception as e:
            logger.critical(f"Error crítico al crear reserva: {e}")

        finally:
            estado = f"ID:{reserva.id}" if reserva else "FALLIDA"
            logger.debug(f"Intento de creación de reserva finalizado. Resultado: {estado}")

        return reserva

    def confirmar_reserva(
        self, reserva: Optional[Reserva], con_iva: bool = True
    ) -> float:
        """Confirma una reserva y retorna el costo."""
        try:
            if reserva is None:
                raise ErrorParametroFaltante("No se proporcionó una reserva válida.")
            return reserva.confirmar(con_iva)

        except (ErrorOperacionNoPermitida, ErrorReservaInvalida,
                ErrorCalculoCosto, ErrorParametroFaltante) as e:
            logger.error(f"Error al confirmar reserva: {e}")
            return 0.0

    def cancelar_reserva(
        self, reserva: Optional[Reserva], motivo: str = ""
    ) -> bool:
        """Cancela una reserva existente."""
        try:
            if reserva is None:
                raise ErrorParametroFaltante("No se proporcionó una reserva válida.")
            return reserva.cancelar(motivo)

        except (ErrorOperacionNoPermitida, ErrorReservaInvalida,
                ErrorParametroFaltante) as e:
            logger.error(f"Error al cancelar reserva: {e}")
            return False

    def procesar_reserva(self, reserva: Optional[Reserva]) -> bool:
        """Procesa (ejecuta) una reserva confirmada."""
        try:
            if reserva is None:
                raise ErrorParametroFaltante("No se proporcionó una reserva válida.")
            return reserva.procesar()

        except (ErrorOperacionNoPermitida, ErrorReservaInvalida,
                ErrorParametroFaltante) as e:
            logger.error(f"Error al procesar reserva: {e}")
            return False

    def obtener_servicios(self) -> list:
        return list(self.__servicios)

    def mostrar_resumen_final(self) -> None:
        """Imprime el resumen estadístico del sistema."""
        total      = len(self.__reservas)
        confirmadas = sum(1 for r in self.__reservas if r.estado == "CONFIRMADA")
        procesadas  = sum(1 for r in self.__reservas if r.estado == "PROCESADA")
        canceladas  = sum(1 for r in self.__reservas if r.estado == "CANCELADA")
        pendientes  = sum(1 for r in self.__reservas if r.estado == "PENDIENTE")
        ingresos    = sum(
            r.costo_total for r in self.__reservas
            if r.estado in ("CONFIRMADA", "PROCESADA")
        )

        print(f"\n  ╔{'═'*56}╗")
        print(f"  ║{'RESUMEN FINAL — SISTEMA SOFTWARE FJ'.center(56)}║")
        print(f"  ╠{'═'*56}╣")
        print(f"  ║  {'Clientes registrados':<30}: {len(self.__clientes):<22}║")
        print(f"  ║  {'Servicios en catálogo':<30}: {len(self.__servicios):<22}║")
        print(f"  ║  {'Total de reservas':<30}: {total:<22}║")
        print(f"  ║  {'  → Pendientes':<30}: {pendientes:<22}║")
        print(f"  ║  {'  → Confirmadas':<30}: {confirmadas:<22}║")
        print(f"  ║  {'  → Procesadas':<30}: {procesadas:<22}║")
        print(f"  ║  {'  → Canceladas':<30}: {canceladas:<22}║")
        print(f"  ║  {'Ingresos generados':<30}: {'$'+f'{ingresos:,.0f}':<22}║")
        print(f"  ╚{'═'*56}╝")


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 9 — SIMULACIÓN PRINCIPAL (12 OPERACIONES)
# ═════════════════════════════════════════════════════════════════════════════

def main():
    """
    Simula 12 operaciones completas del sistema, incluyendo casos válidos
    e inválidos, para demostrar robustez y manejo de excepciones.
    """

    print("\n  ╔══════════════════════════════════════════════════════════╗")
    print("  ║      SISTEMA DE GESTIÓN SOFTWARE FJ — FASE 4            ║")
    print("  ║      Programación 213023 — UNAD                         ║")
    print("  ╚══════════════════════════════════════════════════════════╝")

    gestor = GestorSistema()

    # =========================================================================
    # BLOQUE A — REGISTRO DE CLIENTES
    # =========================================================================
    separador(" BLOQUE A: REGISTRO DE CLIENTES ")
    encabezado_tabla("Op.", "Descripción", "Estado", "Detalle")

    c1 = gestor.registrar_cliente("Ana María López",    "ana.lopez@email.com",   "3001234567", "1020345678")
    fila_resultado("A-01", "Cliente válido — Ana López",    "✔ OK",    f"ID: {c1.id}" if c1 else "—")

    c2 = gestor.registrar_cliente("Carlos Rodríguez",   "carlos.r@empresa.co",  "3159876543", "79856321")
    fila_resultado("A-02", "Cliente válido — Carlos R.",    "✔ OK",    f"ID: {c2.id}" if c2 else "—")

    c3 = gestor.registrar_cliente("Sofía Herrera",      "sofia.h@correo.org",   "6017654321", "52341098")
    fila_resultado("A-03", "Cliente válido — Sofía H.",     "✔ OK",    f"ID: {c3.id}" if c3 else "—")

    cx = gestor.registrar_cliente("Pedro Inválido",     "correo-sin-arroba",    "3001234567", "9988776655")
    fila_resultado("A-04", "Email sin @ (inválido)",        "✗ ERROR", "Cod. 100")

    cx = gestor.registrar_cliente("María Error",        "maria@ok.com",         "telefono-abc","5544332211")
    fila_resultado("A-05", "Teléfono con letras (inválido)","✗ ERROR", "Cod. 100")

    cx = gestor.registrar_cliente("",                   "vacio@correo.com",     "3001112233", "1122334455")
    fila_resultado("A-06", "Nombre vacío (inválido)",       "✗ ERROR", "Cod. 600")

    pie_tabla()

    # =========================================================================
    # BLOQUE B — CREACIÓN DE SERVICIOS
    # =========================================================================
    separador(" BLOQUE B: CREACIÓN DE SERVICIOS ")
    encabezado_tabla("Op.", "Descripción", "Estado", "Detalle")

    sala_a = equipo_lp = asesoria = None

    try:
        sala_a = ReservaSala("Sala Innovación A", capacidad=10,
                              precio_hora=80_000, tiene_audiovisual=True)
        gestor.agregar_servicio(sala_a)
        fila_resultado("B-01", "Sala con audiovisual", "✔ OK", f"ID: {sala_a.id}")
    except ErrorServicioInvalido as e:
        fila_resultado("B-01", "Sala con audiovisual", "✗ ERROR", str(e)[:18])

    try:
        equipo_lp = AlquilerEquipo("Alquiler Laptops HP", tipo_equipo="Laptop HP 15",
                                    cantidad_disponible=8, precio_hora=25_000)
        gestor.agregar_servicio(equipo_lp)
        fila_resultado("B-02", "Alquiler laptops HP",  "✔ OK", f"ID: {equipo_lp.id}")
    except ErrorServicioInvalido as e:
        fila_resultado("B-02", "Alquiler laptops HP",  "✗ ERROR", str(e)[:18])

    try:
        asesoria = AsesoriaEspecializada("Asesoría Legal", area="Legal",
                                          nivel_asesor="senior", precio_hora=120_000,
                                          horas_minimas=2.0)
        gestor.agregar_servicio(asesoria)
        fila_resultado("B-03", "Asesoría legal senior","✔ OK", f"ID: {asesoria.id}")
    except ErrorServicioInvalido as e:
        fila_resultado("B-03", "Asesoría legal senior","✗ ERROR", str(e)[:18])

    try:
        _ = ReservaSala("Sala Errónea", capacidad=5, precio_hora=-5_000)
        fila_resultado("B-04", "Sala precio negativo", "✔ OK", "—")
    except ErrorServicioInvalido:
        fila_resultado("B-04", "Sala precio negativo", "✗ ERROR", "Cod. 200")

    try:
        _ = AsesoriaEspecializada("Asesoría Mágica", area="Magia",
                                   nivel_asesor="mago", precio_hora=50_000)
        fila_resultado("B-05", "Asesoría nivel 'mago'","✔ OK", "—")
    except ErrorServicioInvalido:
        fila_resultado("B-05", "Asesoría nivel 'mago'","✗ ERROR", "Cod. 200")

    pie_tabla()

    # =========================================================================
    # BLOQUE C — RESERVAS: FLUJO COMPLETO
    # =========================================================================
    separador(" BLOQUE C: RESERVAS — FLUJO COMPLETO ")
    encabezado_tabla("Op.", "Descripción", "Estado", "Costo / Detalle")

    # Op. C-01: crear → confirmar → procesar (flujo exitoso)
    r1 = gestor.crear_reserva(c1, sala_a, horas=3, personas=8, descuento=0.10)
    fila_resultado("C-01", "Crear reserva sala (10% desc)", "✔ OK", f"ID: {r1.id}" if r1 else "—")

    costo1 = gestor.confirmar_reserva(r1, con_iva=True)
    fila_resultado("C-02", "Confirmar reserva sala",        "✔ OK", f"${costo1:,.0f}")

    gestor.procesar_reserva(r1)
    fila_resultado("C-03", "Procesar reserva sala",         "✔ OK", "PROCESADA")

    # Op. C-04: alquiler múltiple de equipos
    try:
        costo_mult = equipo_lp.calcular_costo_multiple(horas=4, cantidad=3, descuento=0.05)
        fila_resultado("C-04", "Costo múltiple 3 laptops×4h", "✔ OK", f"${costo_mult:,.0f}")
    except ErrorCalculoCosto as e:
        fila_resultado("C-04", "Costo múltiple laptops",       "✗ ERROR", str(e)[:18])

    r2 = gestor.crear_reserva(c2, equipo_lp, horas=4, personas=3)
    costo2 = gestor.confirmar_reserva(r2, con_iva=True)
    fila_resultado("C-05", "Confirmar alquiler 3 laptops",  "✔ OK", f"${costo2:,.0f}")

    # Op. C-06: asesoría → confirmar → cancelar
    r3 = gestor.crear_reserva(c3, asesoria, horas=3, personas=1, descuento=0.0)
    costo3 = gestor.confirmar_reserva(r3, con_iva=True)
    fila_resultado("C-06", "Confirmar asesoría legal",      "✔ OK", f"${costo3:,.0f}")

    gestor.cancelar_reserva(r3, "Cliente solicitó reprogramación")
    fila_resultado("C-07", "Cancelar asesoría confirmada",  "✔ OK", "CANCELADA")

    # Op. C-08: paquete de asesoría (sobrecarga)
    try:
        costo_paq = asesoria.calcular_costo_paquete(sesiones=4, horas_por_sesion=2.0, descuento=0.10)
        fila_resultado("C-08", "Paquete 4 sesiones asesoría",  "✔ OK", f"${costo_paq:,.0f}")
    except ErrorCalculoCosto as e:
        fila_resultado("C-08", "Paquete 4 sesiones asesoría",  "✗ ERROR", str(e)[:18])

    # Op. C-09: costo extendido con audiovisual y horas extra (sobrecarga ReservaSala)
    try:
        costo_ext = sala_a.calcular_costo_extendido(horas=2, descuento=0.0, horas_extra=1.0)
        fila_resultado("C-09", "Sala extendida +1h extra audio","✔ OK", f"${costo_ext:,.0f}")
    except ErrorCalculoCosto as e:
        fila_resultado("C-09", "Sala costo extendido",          "✗ ERROR", str(e)[:18])

    pie_tabla()

    # =========================================================================
    # BLOQUE D — OPERACIONES INVÁLIDAS (errores controlados)
    # =========================================================================
    separador(" BLOQUE D: OPERACIONES INVÁLIDAS ")
    encabezado_tabla("Op.", "Descripción", "Estado", "Error detectado")

    # D-01: demasiadas personas para la sala
    rx = gestor.crear_reserva(c1, sala_a, horas=2, personas=25)
    fila_resultado("D-01", "Reserva 25 pers. en sala×10",  "✗ ERROR", "Cod. 300")

    # D-02: cancelar reserva ya procesada
    ok = gestor.cancelar_reserva(r1, "Intento inválido")
    fila_resultado("D-02", "Cancelar reserva PROCESADA",   "✗ ERROR", "Cod. 400")

    # D-03: procesar reserva cancelada
    ok = gestor.procesar_reserva(r3)
    fila_resultado("D-03", "Procesar reserva CANCELADA",   "✗ ERROR", "Cod. 400")

    # D-04: confirmar reserva ya confirmada
    costo_x = gestor.confirmar_reserva(r2)
    fila_resultado("D-04", "Confirmar reserva ya CONFIRM.", "✗ ERROR", "Cod. 400")

    # D-05: servicio desactivado
    equipo_lp.disponible = False
    rx2 = gestor.crear_reserva(c2, equipo_lp, horas=2, personas=1)
    fila_resultado("D-05", "Reserva servicio inactivo",    "✗ ERROR", "Cod. 200")
    equipo_lp.disponible = True

    pie_tabla()

    # =========================================================================
    # BLOQUE E — POLIMORFISMO EN ACCIÓN
    # =========================================================================
    separador(" BLOQUE E: POLIMORFISMO — calcular_costo() ")
    print(f"\n  {'Servicio':<38} {'Tipo':<20} {'Costo 2h (IVA)'}")
    print(f"  {'─'*38} {'─'*20} {'─'*15}")
    for srv in gestor.obtener_servicios():
        try:
            costo = srv.calcular_costo(horas=2, descuento=0.0, con_iva=True)
            tipo  = srv.__class__.__name__
            print(f"  {srv.nombre:<38} {tipo:<20} ${costo:>12,.0f}")
        except ErrorCalculoCosto as e:
            print(f"  {srv.nombre:<38} {'Error':<20} {str(e)[:15]}")

    # =========================================================================
    # RESUMEN Y DETALLE FINAL
    # =========================================================================
    gestor.mostrar_resumen_final()

    separador(" DETALLE DE RESERVAS ACTIVAS ")
    for r in [r1, r2, r3]:
        if r:
            print(r.obtener_info())

    print(f"\n  📄 Log completo guardado en: {LOG_FILE}\n")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()