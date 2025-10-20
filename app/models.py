from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum

class EstadoEntrega(str, enum.Enum):
    PENDIENTE = "pendiente"
    ASIGNADO = "asignado"
    EN_RUTA = "en_ruta"
    ENTREGADO = "entregado"
    NO_ENTREGADO = "no_entregado"

class Zona(Base):
    __tablename__ = "zonas"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255))
    color_hex = Column(String(7))
    created_at = Column(DateTime, default=datetime.utcnow)

class Camion(Base):
    __tablename__ = "camiones"
    
    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(10), unique=True, nullable=False)
    chofer_nombre = Column(String(100), nullable=False)
    chofer_telefono = Column(String(15))
    password_hash = Column(String(255))
    capacidad_kg = Column(Float, default=1000.0)
    activo = Column(Boolean, default=True)
    ultima_lat = Column(Float)
    ultima_lng = Column(Float)
    ultima_actualizacion = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    ruc = Column(String(11))
    nombre = Column(String(200), nullable=False)
    direccion = Column(String(255), nullable=False)
    referencia = Column(String(255))
    zona_id = Column(Integer, ForeignKey('zonas.id'))
    telefono = Column(String(15))
    lat = Column(Float)
    lng = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    zona = relationship("Zona")

class Entrega(Base):
    __tablename__ = "entregas"
    
    id = Column(Integer, primary_key=True, index=True)
    numero_factura = Column(String(50), nullable=False)
    fecha_factura = Column(DateTime)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    camion_id = Column(Integer, ForeignKey('camiones.id'))
    zona_id = Column(Integer, ForeignKey('zonas.id'))
    peso_kg = Column(Float)
    monto_total = Column(Float)
    cantidad_items = Column(Integer)
    observaciones = Column(String(500))
    estado = Column(SQLEnum(EstadoEntrega), default=EstadoEntrega.PENDIENTE)
    orden_ruta = Column(Integer)
    archivo_original_url = Column(String(500))
    foto_prueba_url = Column(String(500))
    firma_url = Column(String(500))
    fecha_asignacion = Column(DateTime)
    fecha_inicio_ruta = Column(DateTime)
    fecha_entrega = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    cliente = relationship("Cliente")
    camion = relationship("Camion")
    zona = relationship("Zona")

class TrackingHistorial(Base):
    __tablename__ = "tracking_historial"
    
    id = Column(Integer, primary_key=True, index=True)
    camion_id = Column(Integer, ForeignKey('camiones.id'))
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    velocidad_kmh = Column(Float)
    
    camion = relationship("Camion")
