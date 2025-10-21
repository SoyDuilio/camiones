# app/models.py - Versión Extendida para Optimización

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum as SQLEnum, Date, Time, Text, Index
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum

# ========== ENUMS ==========

class EstadoEntrega(str, enum.Enum):
    PENDIENTE = "pendiente"
    ASIGNADO = "asignado"
    EN_RUTA = "en_ruta"
    ENTREGADO = "entregado"
    NO_ENTREGADO = "no_entregado"
    REPROGRAMADO = "reprogramado"

class TipoCliente(str, enum.Enum):
    VIP = "vip"
    REGULAR = "regular"
    NUEVO = "nuevo"
    OCASIONAL = "ocasional"

class EstadoMecanico(str, enum.Enum):
    EXCELENTE = "excelente"
    BUENO = "bueno"
    REGULAR = "regular"
    MANTENIMIENTO = "mantenimiento"
    FUERA_SERVICIO = "fuera_servicio"

class CondicionCamino(str, enum.Enum):
    EXCELENTE = "excelente"
    BUENO = "bueno"
    REGULAR = "regular"
    MALO = "malo"

class EstadoRuta(str, enum.Enum):
    PLANIFICADA = "planificada"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    PAUSADA = "pausada"

class AlgoritmoOptimizacion(str, enum.Enum):
    GREEDY = "greedy"
    NEAREST_NEIGHBOR = "nearest_neighbor"
    SAVINGS = "savings"
    GENETIC = "genetic"

# ========== MODELOS PRINCIPALES ==========

class Zona(Base):
    __tablename__ = "zonas"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255))
    color_hex = Column(String(7), default="#06b6d4")
    
    # Características de tráfico
    trafico_pico_manana = Column(Boolean, default=False)  # 7-9 AM
    trafico_pico_tarde = Column(Boolean, default=False)   # 5-7 PM
    factor_trafico = Column(Float, default=1.0)  # Multiplicador de tiempo 1.0-2.0
    
    # Condiciones de acceso
    condicion_caminos = Column(SQLEnum(CondicionCamino), default=CondicionCamino.BUENO)
    requiere_vehiculo_4x4 = Column(Boolean, default=False)
    problematico_lluvia = Column(Boolean, default=False)
    acceso_restringido_horario = Column(String(100))  # "08:00-18:00"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clientes = relationship("Cliente", back_populates="zona")


class Chofer(Base):
    __tablename__ = "choferes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    dni = Column(String(8), unique=True)
    telefono = Column(String(15))
    email = Column(String(100))
    
    # Credenciales
    password_hash = Column(String(255))
    
    # Experiencia y habilidades
    años_experiencia = Column(Integer, default=0)
    licencia_categoria = Column(String(10))  # A-IIb, A-IIIb, etc
    apto_caminos_dificiles = Column(Boolean, default=False)
    conoce_iquitos = Column(Boolean, default=True)
    
    # Disponibilidad
    activo = Column(Boolean, default=True)
    horario_inicio = Column(Time)
    horario_fin = Column(Time)
    
    # Performance
    rating_promedio = Column(Float, default=5.0)  # 1-5
    entregas_completadas_total = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    camiones = relationship("Camion", back_populates="chofer_asignado")
    rutas = relationship("Ruta", back_populates="chofer")

class Camion(Base):
    __tablename__ = "camiones"
    
    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(10), unique=True, nullable=False, index=True)
    marca = Column(String(50))
    modelo = Column(String(50))
    año = Column(Integer)
    
    # Chofer asignado
    chofer_id = Column(Integer, ForeignKey('choferes.id'))
    
    # Capacidades físicas
    capacidad_peso_kg = Column(Float, nullable=False, default=1000.0)
    capacidad_volumen_m3 = Column(Float, default=10.0)
    capacidad_items = Column(Integer, default=100)
    
    # Rendimiento y consumo
    consumo_combustible_km_vacio = Column(Float, default=0.15)  # litros/km
    consumo_combustible_km_cargado = Column(Float, default=0.25)  # litros/km
    velocidad_promedio_kmh = Column(Float, default=35.0)
    
    # Estado mecánico
    estado_mecanico = Column(SQLEnum(EstadoMecanico), default=EstadoMecanico.BUENO)
    ultimo_mantenimiento = Column(Date)
    km_actual = Column(Float, default=0.0)
    km_siguiente_mantenimiento = Column(Float)
    
    # Capacidades especiales
    tiene_refrigeracion = Column(Boolean, default=False)
    apto_lluvia_fuerte = Column(Boolean, default=True)
    apto_caminos_adversos = Column(Boolean, default=False)
    tiene_gps = Column(Boolean, default=True)
    
    # Tracking actual
    ultima_lat = Column(Float)
    ultima_lng = Column(Float)
    ultima_actualizacion = Column(DateTime)
    
    # Control operativo
    activo = Column(Boolean, default=True)
    en_ruta = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chofer_asignado = relationship("Chofer", back_populates="camiones")
    rutas = relationship("Ruta", back_populates="camion")
    historial_tracking = relationship("TrackingHistorial", back_populates="camion")


class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    ruc = Column(String(11), index=True)
    nombre = Column(String(200), nullable=False)
    nombre_comercial = Column(String(200))
    
    # Ubicación
    direccion = Column(String(255), nullable=False)
    referencia = Column(String(255))  # "Al costado de la farmacia San Juan"
    zona_id = Column(Integer, ForeignKey('zonas.id'), nullable=False)
    distrito = Column(String(100))
    lat = Column(Float, index=True)
    lng = Column(Float, index=True)
    
    # Contacto
    telefono = Column(String(15))
    email = Column(String(100))
    contacto_nombre = Column(String(100))
    
    # Clasificación y prioridad
    tipo_cliente = Column(SQLEnum(TipoCliente), default=TipoCliente.REGULAR)
    prioridad_base = Column(Integer, default=5)  # 1-10 (10=máxima)
    
    # Restricciones de entrega
    horario_atencion_inicio = Column(Time)
    horario_atencion_fin = Column(Time)
    dias_atencion = Column(String(50))  # "lun,mar,mie,jue,vie"
    requiere_cita_previa = Column(Boolean, default=False)
    tiempo_descarga_estimado_min = Column(Integer, default=15)
    
    # Historial
    total_pedidos = Column(Integer, default=0)
    total_valor_compras = Column(Float, default=0.0)
    fecha_ultimo_pedido = Column(Date)
    
    # Notas
    observaciones = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    zona = relationship("Zona", back_populates="clientes")
    entregas = relationship("Entrega", back_populates="cliente")


class Entrega(Base):
    __tablename__ = "entregas"
    
    id = Column(Integer, primary_key=True, index=True)
    numero_factura = Column(String(50), nullable=False, unique=True, index=True)
    fecha_factura = Column(Date)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Cliente y destino
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    zona_id = Column(Integer, ForeignKey('zonas.id'))
    
    # Asignación
    ruta_id = Column(Integer, ForeignKey('rutas.id'))
    orden_en_ruta = Column(Integer)  # Secuencia: 1, 2, 3...
    
    # Dimensiones y características físicas
    peso_total_kg = Column(Float, nullable=False, default=0.0)
    volumen_total_m3 = Column(Float, default=0.0)
    cantidad_bultos = Column(Integer, default=1)
    cantidad_items = Column(Integer, default=1)
    
    # Características especiales
    requiere_refrigeracion = Column(Boolean, default=False)
    es_fragil = Column(Boolean, default=False)
    requiere_ayudante = Column(Boolean, default=False)
    requiere_factura_fisica = Column(Boolean, default=True)
    
    # Valor y prioridad
    monto_total = Column(Float, default=0.0)
    prioridad = Column(Integer, default=5)  # 1-10 (10=urgente)
    es_urgente = Column(Boolean, default=False)
    fecha_maxima_entrega = Column(Date)
    
    # Restricciones de entrega
    horario_entrega_desde = Column(Time)
    horario_entrega_hasta = Column(Time)
    
    # Datos calculados (por optimizador)
    distancia_desde_almacen_km = Column(Float)
    tiempo_estimado_entrega_min = Column(Integer, default=15)
    costo_entrega_estimado = Column(Float)
    
    # Estado y seguimiento
    estado = Column(SQLEnum(EstadoEntrega), default=EstadoEntrega.PENDIENTE)
    
    # Archivos y evidencias
    archivo_original_url = Column(String(500))  # PDF/foto original
    foto_prueba_entrega_url = Column(String(500))  # Foto del chofer
    firma_digital_url = Column(String(500))
    
    # Timestamps de seguimiento
    fecha_asignacion = Column(DateTime)
    fecha_inicio_ruta = Column(DateTime)
    fecha_entrega_real = Column(DateTime)
    
    # Información de no entrega
    motivo_no_entrega = Column(String(255))
    fecha_reprogramacion = Column(Date)
    
    # Notas
    observaciones = Column(Text)
    notas_chofer = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cliente = relationship("Cliente", back_populates="entregas")
    zona = relationship("Zona")
    ruta = relationship("Ruta", back_populates="entregas")


class Ruta(Base):
    __tablename__ = "rutas"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    codigo = Column(String(50), unique=True)  # RUT-20251020-001
    
    # Asignación
    camion_id = Column(Integer, ForeignKey('camiones.id'), nullable=False)
    chofer_id = Column(Integer, ForeignKey('choferes.id'), nullable=False)
    
    # Métricas de carga
    peso_total_kg = Column(Float, default=0.0)
    volumen_total_m3 = Column(Float, default=0.0)
    cantidad_entregas = Column(Integer, default=0)
    cantidad_items_total = Column(Integer, default=0)
    
    # Métricas de distancia y tiempo
    distancia_total_km = Column(Float, default=0.0)
    tiempo_total_estimado_min = Column(Integer, default=0)
    tiempo_total_real_min = Column(Integer)
    
    # Costos calculados
    costo_combustible_estimado = Column(Float, default=0.0)
    costo_tiempo_estimado = Column(Float, default=0.0)
    costo_total_estimado = Column(Float, default=0.0)
    costo_total_real = Column(Float)
    
    # Optimización
    score_optimizacion = Column(Float)  # 0-100 (qué tan óptima es)
    algoritmo_usado = Column(SQLEnum(AlgoritmoOptimizacion))
    iteraciones_optimizacion = Column(Integer)
    tiempo_calculo_ms = Column(Integer)
    
    # Valor monetario transportado
    valor_total_facturas = Column(Float, default=0.0)
    
    # Estado y control
    estado = Column(SQLEnum(EstadoRuta), default=EstadoRuta.PLANIFICADA)
    hora_inicio_planificada = Column(Time)
    hora_fin_estimada = Column(Time)
    hora_inicio_real = Column(DateTime)
    hora_fin_real = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))  # Usuario que creó la ruta
    
    # Relationships
    camion = relationship("Camion", back_populates="rutas")
    chofer = relationship("Chofer", back_populates="rutas")
    entregas = relationship("Entrega", back_populates="ruta", order_by="Entrega.orden_en_ruta")


class MatrizDistancia(Base):
    """Cache de distancias calculadas para evitar consultas repetidas a APIs"""
    __tablename__ = "matriz_distancias"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Coordenadas (redondeadas a 4 decimales para cache)
    origen_lat = Column(Float, nullable=False)
    origen_lng = Column(Float, nullable=False)
    destino_lat = Column(Float, nullable=False)
    destino_lng = Column(Float, nullable=False)
    
    # Resultados
    distancia_km = Column(Float, nullable=False)
    distancia_lineal_km = Column(Float)  # Distancia en línea recta
    tiempo_min = Column(Integer, nullable=False)
    
    # Contexto
    con_trafico = Column(Boolean, default=False)
    hora_calculo = Column(Time)
    
    # Cache control
    fecha_calculo = Column(DateTime, default=datetime.utcnow)
    expira_en = Column(DateTime)  # Para invalidar cache antiguo
    hits = Column(Integer, default=0)  # Cuántas veces se usó
    
    # Índices compuestos para búsqueda rápida
    __table_args__ = (
        Index('idx_origen_destino', 'origen_lat', 'origen_lng', 'destino_lat', 'destino_lng'),
    )


class TrackingHistorial(Base):
    """Registro histórico de posiciones de camiones"""
    __tablename__ = "tracking_historial"
    
    id = Column(Integer, primary_key=True, index=True)
    camion_id = Column(Integer, ForeignKey('camiones.id'), nullable=False, index=True)
    ruta_id = Column(Integer, ForeignKey('rutas.id'), index=True)
    
    # Posición
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    velocidad_kmh = Column(Float)
    rumbo_grados = Column(Float)  # 0-360
    precision_metros = Column(Float)
    
    # Relationships
    camion = relationship("Camion", back_populates="historial_tracking")


class ParametrosOptimizacion(Base):
    """Configuración del motor de optimización"""
    __tablename__ = "parametros_optimizacion"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    
    # Pesos de factores (suman 100)
    peso_distancia = Column(Integer, default=40)  # Minimizar km
    peso_prioridad_cliente = Column(Integer, default=25)  # Atender VIPs primero
    peso_costo_combustible = Column(Integer, default=20)  # Minimizar consumo
    peso_tiempo = Column(Integer, default=15)  # Minimizar horas
    
    # Restricciones operativas
    max_horas_ruta = Column(Float, default=8.0)
    max_entregas_por_ruta = Column(Integer, default=25)
    max_km_por_ruta = Column(Float, default=150.0)
    tiempo_carga_inicial_min = Column(Integer, default=45)
    tiempo_retorno_almacen_min = Column(Integer, default=30)
    
    # Margen de capacidad (%)
    margen_seguridad_peso = Column(Float, default=0.9)  # Usar 90% capacidad max
    margen_seguridad_volumen = Column(Float, default=0.85)
    
    # Costos (en soles)
    costo_combustible_litro = Column(Float, default=4.50)
    costo_hora_operacion = Column(Float, default=25.00)
    costo_km_mantenimiento = Column(Float, default=0.50)
    
    # Configuración de algoritmo
    algoritmo_preferido = Column(SQLEnum(AlgoritmoOptimizacion), default=AlgoritmoOptimizacion.GREEDY)
    max_iteraciones = Column(Integer, default=1000)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EventoSistema(Base):
    """Log de eventos importantes del sistema"""
    __tablename__ = "eventos_sistema"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    tipo = Column(String(50), index=True)  # optimizacion, entrega, error, etc
    
    # Contexto
    ruta_id = Column(Integer, ForeignKey('rutas.id'))
    camion_id = Column(Integer, ForeignKey('camiones.id'))
    entrega_id = Column(Integer, ForeignKey('entregas.id'))
    usuario = Column(String(100))
    
    # Detalles
    descripcion = Column(Text)
    datos_json = Column(Text)  # JSON con información adicional
    
    # Severidad
    nivel = Column(String(20))  # info, warning, error, critical