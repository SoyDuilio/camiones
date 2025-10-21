# app/routes/api.py - Actualizado con endpoints de optimización

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.services import gemini_ocr, pdf_parser
from app.services.route_optimizer import RouteOptimizer
from app.models import (
    Ruta, Entrega, Camion, Cliente, Zona, ParametrosOptimizacion,
    EstadoEntrega, EstadoRuta, Chofer
)
from datetime import date, datetime, timedelta
from typing import List, Optional
import shutil
from pathlib import Path
from pydantic import BaseModel

router = APIRouter()

# ========== SCHEMAS ==========

class EntregaCreate(BaseModel):
    numero_factura: str
    cliente_id: int
    peso_total_kg: float
    monto_total: float
    prioridad: int = 5

class RutaResponse(BaseModel):
    id: int
    codigo: str
    camion_placa: str
    chofer_nombre: str
    cantidad_entregas: int
    distancia_total_km: float
    tiempo_total_estimado_min: int
    costo_total_estimado: float
    score_optimizacion: float
    valor_total_facturas: float

class OptimizacionResponse(BaseModel):
    success: bool
    message: str
    rutas_creadas: int
    entregas_asignadas: int
    rutas: List[RutaResponse]
    metricas: dict

class ParametrosUpdate(BaseModel):
    peso_distancia: Optional[int] = None
    peso_prioridad_cliente: Optional[int] = None
    peso_costo_combustible: Optional[int] = None
    peso_tiempo: Optional[int] = None
    max_horas_ruta: Optional[float] = None
    max_entregas_por_ruta: Optional[int] = None

# ========== ENDPOINTS DE OPTIMIZACIÓN ==========

@router.post("/optimizar-rutas")
async def optimizar_rutas(
    fecha: Optional[str] = Query(None, description="Fecha en formato YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    Optimiza las rutas para un día específico
    """
    try:
        # Usar fecha de hoy si no se proporciona
        if fecha:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        else:
            fecha_obj = date.today()
        
        # Crear instancia del optimizador
        optimizer = RouteOptimizer(db)
        
        # Ejecutar optimización
        inicio = datetime.now()
        rutas = optimizer.optimizar_dia(fecha_obj)
        tiempo_calculo = (datetime.now() - inicio).total_seconds()
        
        if not rutas:
            return JSONResponse({
                "success": False,
                "message": "No se pudieron crear rutas. Verifica que haya entregas pendientes y camiones disponibles.",
                "rutas_creadas": 0,
                "entregas_asignadas": 0
            })
        
        # Calcular métricas agregadas
        total_entregas = sum(r.cantidad_entregas for r in rutas)
        total_km = sum(r.distancia_total_km for r in rutas)
        total_costo = sum(r.costo_total_estimado for r in rutas)
        total_valor = sum(r.valor_total_facturas for r in rutas)
        score_promedio = sum(r.score_optimizacion for r in rutas) / len(rutas)
        
        # Formatear respuesta
        rutas_response = [
            RutaResponse(
                id=r.id,
                codigo=r.codigo,
                camion_placa=r.camion.placa,
                chofer_nombre=r.chofer.nombre if r.chofer else "Sin asignar",
                cantidad_entregas=r.cantidad_entregas,
                distancia_total_km=round(r.distancia_total_km, 2),
                tiempo_total_estimado_min=r.tiempo_total_estimado_min,
                costo_total_estimado=round(r.costo_total_estimado, 2),
                score_optimizacion=r.score_optimizacion,
                valor_total_facturas=round(r.valor_total_facturas, 2)
            )
            for r in rutas
        ]
        
        return {
            "success": True,
            "message": f"Rutas optimizadas exitosamente para {fecha_obj}",
            "rutas_creadas": len(rutas),
            "entregas_asignadas": total_entregas,
            "rutas": rutas_response,
            "metricas": {
                "distancia_total_km": round(total_km, 2),
                "costo_total_estimado": round(total_costo, 2),
                "valor_total_facturas": round(total_valor, 2),
                "score_promedio": round(score_promedio, 1),
                "tiempo_calculo_segundos": round(tiempo_calculo, 2),
                "km_promedio_por_ruta": round(total_km / len(rutas), 2),
                "entregas_promedio_por_ruta": round(total_entregas / len(rutas), 1)
            }
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error en optimización: {str(e)}",
                "rutas_creadas": 0,
                "entregas_asignadas": 0
            }
        )

@router.get("/rutas")
async def listar_rutas(
    fecha: Optional[str] = None,
    estado: Optional[str] = None,
    camion_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Lista rutas con filtros opcionales
    """
    query = db.query(Ruta)
    
    if fecha:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        query = query.filter(Ruta.fecha == fecha_obj)
    
    if estado:
        query = query.filter(Ruta.estado == estado)
    
    if camion_id:
        query = query.filter(Ruta.camion_id == camion_id)
    
    rutas = query.order_by(Ruta.created_at.desc()).all()
    
    return {
        "total": len(rutas),
        "rutas": [
            {
                "id": r.id,
                "codigo": r.codigo,
                "fecha": r.fecha.isoformat(),
                "camion_placa": r.camion.placa,
                "chofer_nombre": r.chofer.nombre if r.chofer else None,
                "cantidad_entregas": r.cantidad_entregas,
                "distancia_total_km": r.distancia_total_km,
                "tiempo_estimado_min": r.tiempo_total_estimado_min,
                "costo_total": r.costo_total_estimado,
                "score": r.score_optimizacion,
                "estado": r.estado.value if r.estado else None,
                "valor_facturas": r.valor_total_facturas
            }
            for r in rutas
        ]
    }

@router.get("/rutas/{ruta_id}")
async def detalle_ruta(ruta_id: int, db: Session = Depends(get_db)):
    """
    Obtiene detalles completos de una ruta
    """
    ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
    
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    entregas_detalle = [
        {
            "id": e.id,
            "numero_factura": e.numero_factura,
            "orden": e.orden_en_ruta,
            "cliente": {
                "nombre": e.cliente.nombre,
                "direccion": e.cliente.direccion,
                "lat": e.cliente.lat,
                "lng": e.cliente.lng,
                "zona": e.cliente.zona.nombre if e.cliente.zona else None
            },
            "peso_kg": e.peso_total_kg,
            "monto": e.monto_total,
            "estado": e.estado.value if e.estado else None,
            "prioridad": e.prioridad,
            "tiempo_estimado_min": e.tiempo_estimado_entrega_min
        }
        for e in sorted(ruta.entregas, key=lambda x: x.orden_en_ruta or 0)
    ]
    
    return {
        "id": ruta.id,
        "codigo": ruta.codigo,
        "fecha": ruta.fecha.isoformat(),
        "camion": {
            "id": ruta.camion.id,
            "placa": ruta.camion.placa,
            "capacidad_kg": ruta.camion.capacidad_peso_kg,
            "consumo_km": ruta.camion.consumo_combustible_km_cargado
        },
        "chofer": {
            "id": ruta.chofer.id,
            "nombre": ruta.chofer.nombre + " " + ruta.chofer.apellido,
            "telefono": ruta.chofer.telefono
        } if ruta.chofer else None,
        "metricas": {
            "cantidad_entregas": ruta.cantidad_entregas,
            "peso_total_kg": ruta.peso_total_kg,
            "distancia_total_km": ruta.distancia_total_km,
            "tiempo_total_min": ruta.tiempo_total_estimado_min,
            "costo_combustible": ruta.costo_combustible_estimado,
            "costo_total": ruta.costo_total_estimado,
            "valor_facturas": ruta.valor_total_facturas,
            "score_optimizacion": ruta.score_optimizacion
        },
        "estado": ruta.estado.value if ruta.estado else None,
        "algoritmo": ruta.algoritmo_usado.value if ruta.algoritmo_usado else None,
        "entregas": entregas_detalle
    }

@router.post("/rutas/{ruta_id}/iniciar")
async def iniciar_ruta(ruta_id: int, db: Session = Depends(get_db)):
    """
    Marca una ruta como iniciada
    """
    ruta = db.query(Ruta).filter(Ruta.id == ruta_id).first()
    
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    ruta.estado = EstadoRuta.EN_CURSO
    ruta.hora_inicio_real = datetime.now()
    
    # Actualizar estado de entregas
    for entrega in ruta.entregas:
        entrega.estado = EstadoEntrega.EN_RUTA
        entrega.fecha_inicio_ruta = datetime.now()
    
    # Marcar camión como en ruta
    ruta.camion.en_ruta = True
    
    db.commit()
    
    return {"success": True, "message": "Ruta iniciada"}

@router.post("/reasignar-entrega")
async def reasignar_entrega(
    entrega_id: int,
    nueva_ruta_id: int,
    db: Session = Depends(get_db)
):
    """
    Reasigna una entrega a otra ruta
    """
    optimizer = RouteOptimizer(db)
    
    if optimizer.reasignar_entrega(entrega_id, nueva_ruta_id):
        return {"success": True, "message": "Entrega reasignada exitosamente"}
    else:
        raise HTTPException(
            status_code=400, 
            detail="No se pudo reasignar la entrega. Verifica capacidad disponible."
        )

# ========== PARÁMETROS DE OPTIMIZACIÓN ==========

@router.get("/parametros-optimizacion")
async def obtener_parametros(db: Session = Depends(get_db)):
    """
    Obtiene los parámetros de optimización actuales
    """
    params = db.query(ParametrosOptimizacion).filter(
        ParametrosOptimizacion.activo == True
    ).first()
    
    if not params:
        # Crear parámetros por defecto
        params = ParametrosOptimizacion(
            nombre="Configuración Por Defecto",
            activo=True
        )
        db.add(params)
        db.commit()
        db.refresh(params)
    
    return {
        "id": params.id,
        "nombre": params.nombre,
        "pesos": {
            "distancia": params.peso_distancia,
            "prioridad_cliente": params.peso_prioridad_cliente,
            "costo_combustible": params.peso_costo_combustible,
            "tiempo": params.peso_tiempo
        },
        "restricciones": {
            "max_horas_ruta": params.max_horas_ruta,
            "max_entregas_por_ruta": params.max_entregas_por_ruta,
            "max_km_por_ruta": params.max_km_por_ruta,
            "tiempo_carga_inicial_min": params.tiempo_carga_inicial_min
        },
        "costos": {
            "combustible_litro": params.costo_combustible_litro,
            "hora_operacion": params.costo_hora_operacion,
            "km_mantenimiento": params.costo_km_mantenimiento
        },
        "algoritmo_preferido": params.algoritmo_preferido.value if params.algoritmo_preferido else None
    }

@router.put("/parametros-optimizacion")
async def actualizar_parametros(
    parametros: ParametrosUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza parámetros de optimización
    """
    params = db.query(ParametrosOptimizacion).filter(
        ParametrosOptimizacion.activo == True
    ).first()
    
    if not params:
        raise HTTPException(status_code=404, detail="Parámetros no encontrados")
    
    # Actualizar solo los campos proporcionados
    if parametros.peso_distancia is not None:
        params.peso_distancia = parametros.peso_distancia
    if parametros.peso_prioridad_cliente is not None:
        params.peso_prioridad_cliente = parametros.peso_prioridad_cliente
    if parametros.peso_costo_combustible is not None:
        params.peso_costo_combustible = parametros.peso_costo_combustible
    if parametros.peso_tiempo is not None:
        params.peso_tiempo = parametros.peso_tiempo
    if parametros.max_horas_ruta is not None:
        params.max_horas_ruta = parametros.max_horas_ruta
    if parametros.max_entregas_por_ruta is not None:
        params.max_entregas_por_ruta = parametros.max_entregas_por_ruta
    
    params.updated_at = datetime.now()
    
    db.commit()
    
    return {"success": True, "message": "Parámetros actualizados"}

# ========== ESTADÍSTICAS Y DASHBOARD ==========

@router.get("/dashboard/stats")
async def dashboard_stats(db: Session = Depends(get_db)):
    """
    Estadísticas para el dashboard principal
    """
    hoy = date.today()
    
    # Entregas de hoy
    entregas_hoy = db.query(Entrega).filter(
        func.date(Entrega.fecha_factura) == hoy
    ).count()
    
    # Completadas
    completadas = db.query(Entrega).filter(
        func.date(Entrega.fecha_factura) == hoy,
        Entrega.estado == EstadoEntrega.ENTREGADO
    ).count()
    
    # Valor entregado
    valor_entregado = db.query(func.sum(Entrega.monto_total)).filter(
        func.date(Entrega.fecha_factura) == hoy,
        Entrega.estado == EstadoEntrega.ENTREGADO
    ).scalar() or 0
    
    # Valor total
    valor_total = db.query(func.sum(Entrega.monto_total)).filter(
        func.date(Entrega.fecha_factura) == hoy
    ).scalar() or 0
    
    # Pendientes
    pendientes = entregas_hoy - completadas
    valor_pendiente = valor_total - valor_entregado
    
    # Rutas activas
    rutas_activas = db.query(Ruta).filter(
        Ruta.fecha == hoy,
        Ruta.estado == EstadoRuta.EN_CURSO
    ).count()
    
    return {
        "entregas_total": entregas_hoy,
        "entregas_completadas": completadas,
        "entregas_pendientes": pendientes,
        "valor_entregado": round(valor_entregado, 2),
        "valor_pendiente": round(valor_pendiente, 2),
        "valor_total": round(valor_total, 2),
        "rutas_activas": rutas_activas,
        "porcentaje_completado": round((completadas / entregas_hoy * 100) if entregas_hoy > 0 else 0, 1)
    }

# ========== ENDPOINTS EXISTENTES (mantener) ==========

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Procesar PDF de factura"""
    upload_dir = Path("app/uploads/pdfs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    data = await pdf_parser.extract_invoice_data(str(file_path))
    
    return {"success": True, "data": data}

@router.post("/upload-photo")
async def upload_photo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Procesar foto de factura con Gemini Vision"""
    upload_dir = Path("app/uploads/photos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    data = await gemini_ocr.extract_from_image(str(file_path))
    
    return {"success": True, "data": data}

@router.post("/actualizar-tracking/{camion_id}")
async def actualizar_tracking(
    camion_id: int, 
    lat: float, 
    lng: float, 
    db: Session = Depends(get_db)
):
    """Actualizar posición de camión"""
    camion = db.query(Camion).filter(Camion.id == camion_id).first()
    
    if not camion:
        raise HTTPException(status_code=404, detail="Camión no encontrado")
    
    camion.ultima_lat = lat
    camion.ultima_lng = lng
    camion.ultima_actualizacion = datetime.now()
    
    db.commit()
    
    return {"success": True}


@router.post("/resetear-rutas")
async def resetear_rutas(db: Session = Depends(get_db)):
    """Elimina rutas del día y resetea entregas a pendiente"""
    try:
        hoy = date.today()
        
        # Resetear entregas
        db.query(Entrega).filter(
            func.date(Entrega.fecha_factura) == hoy
        ).update({
            "estado": EstadoEntrega.PENDIENTE,
            "ruta_id": None,
            "orden_en_ruta": None,
            "fecha_asignacion": None
        })
        
        # Eliminar rutas de hoy
        db.query(Ruta).filter(Ruta.fecha == hoy).delete()
        
        # Resetear camiones
        db.query(Camion).update({"en_ruta": False})
        
        db.commit()
        
        return {"success": True, "message": "Sistema reseteado"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}