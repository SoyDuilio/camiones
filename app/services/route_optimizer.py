# app/services/route_optimizer.py
"""
Motor de Optimización de Rutas
Considera: capacidad, distancia, prioridad, costos, restricciones
"""

from sqlalchemy.orm import Session
from app.models import (
    Ruta, Entrega, Camion, Cliente, Zona, ParametrosOptimizacion,
    EstadoEntrega, EstadoRuta, AlgoritmoOptimizacion, MatrizDistancia
)
from datetime import date, datetime, time, timedelta
from typing import List, Dict, Tuple, Optional
import math
import logging

logger = logging.getLogger(__name__)


class RouteOptimizer:
    """Motor de optimización de rutas"""
    
    # Coordenadas del almacén/base en Iquitos
    ALMACEN_LAT = -3.7437
    ALMACEN_LNG = -73.2516
    
    def __init__(self, db: Session):
        self.db = db
        self.params = self._get_parametros()
    
    def _get_parametros(self) -> ParametrosOptimizacion:
        """Obtiene parámetros de optimización activos"""
        params = self.db.query(ParametrosOptimizacion).filter(
            ParametrosOptimizacion.activo == True
        ).first()
        
        if not params:
            # Crear parámetros por defecto
            params = ParametrosOptimizacion(
                nombre="Configuración Por Defecto",
                activo=True
            )
            self.db.add(params)
            self.db.commit()
        
        return params
    
    def optimizar_dia(self, fecha: date) -> List[Ruta]:
        """
        Optimiza todas las entregas de un día
        
        Returns:
            Lista de rutas optimizadas
        """
        logger.info(f"🔄 Iniciando optimización para {fecha}")
        
        # 1. Obtener entregas pendientes
        entregas = self._get_entregas_pendientes(fecha)
        if not entregas:
            logger.warning("No hay entregas pendientes")
            return []
        
        logger.info(f"📦 {len(entregas)} entregas a asignar")
        
        # 2. Obtener camiones disponibles
        camiones = self._get_camiones_disponibles()
        if not camiones:
            logger.error("No hay camiones disponibles")
            return []
        
        logger.info(f"🚚 {len(camiones)} camiones disponibles")
        
        # 3. Agrupar entregas por zona
        entregas_por_zona = self._agrupar_por_zona(entregas)
        
        # 4. Aplicar algoritmo de asignación
        rutas = self._asignar_algoritmo_greedy(
            entregas_por_zona, 
            camiones, 
            fecha
        )
        
        # 5. Calcular métricas y costos
        for ruta in rutas:
            self._calcular_metricas_ruta(ruta)
        
        logger.info(f"✅ {len(rutas)} rutas optimizadas generadas")
        
        return rutas
    
    def _get_entregas_pendientes(self, fecha: date) -> List[Entrega]:
        """Obtiene entregas pendientes o para una fecha específica"""
        return self.db.query(Entrega).filter(
            Entrega.estado == EstadoEntrega.PENDIENTE,
            Entrega.fecha_factura <= fecha
        ).all()
    
    def _get_camiones_disponibles(self) -> List[Camion]:
        """Obtiene camiones activos y disponibles"""
        camiones = self.db.query(Camion).filter(
            Camion.activo == True
        ).all()
        
        print(f"DEBUG: Total camiones activos: {len(camiones)}")
        for c in camiones:
            print(f"  - {c.placa}: en_ruta={c.en_ruta}, estado={c.estado_mecanico}, chofer_id={c.chofer_id}")
        
        # Filtrar manualmente
        disponibles = [c for c in camiones 
                    if (c.en_ruta == False or c.en_ruta is None)
                    and (c.estado_mecanico in ['excelente', 'bueno'] or c.estado_mecanico is None)]
        
        print(f"DEBUG: Camiones disponibles después de filtros: {len(disponibles)}")
        return disponibles
    
    def _agrupar_por_zona(self, entregas: List[Entrega]) -> Dict[int, List[Entrega]]:
        """Agrupa entregas por zona"""
        grupos = {}
        for entrega in entregas:
            zona_id = entrega.zona_id or entrega.cliente.zona_id
            if zona_id not in grupos:
                grupos[zona_id] = []
            grupos[zona_id].append(entrega)
        return grupos
    
    def _asignar_algoritmo_greedy(
        self, 
        entregas_por_zona: Dict[int, List[Entrega]], 
        camiones: List[Camion],
        fecha: date
    ) -> List[Ruta]:
        """
        Algoritmo Greedy:
        1. Ordena entregas por prioridad
        2. Asigna a camión con más capacidad disponible
        3. Agrupa por zona para minimizar distancia
        """
        rutas = []
        entregas_asignadas = set()
        
        # Crear una ruta por camión
        for camion in camiones:
            ruta = Ruta(
                fecha=fecha,
                codigo=f"RUT-{fecha.strftime('%Y%m%d')}-{camion.id:03d}",
                camion_id=camion.id,
                chofer_id=camion.chofer_id,
                algoritmo_usado=AlgoritmoOptimizacion.GREEDY,
                estado=EstadoRuta.PLANIFICADA
            )
            
            # Variables de control de capacidad
            peso_actual = 0.0
            volumen_actual = 0.0
            entregas_en_ruta = []
            
            # Para cada zona, intentar asignar entregas
            for zona_id, entregas_zona in entregas_por_zona.items():
                # Ordenar por prioridad (descendente)
                entregas_ordenadas = sorted(
                    [e for e in entregas_zona if e.id not in entregas_asignadas],
                    key=lambda x: (x.prioridad, x.es_urgente),
                    reverse=True
                )
                
                for entrega in entregas_ordenadas:
                    # Validar capacidad
                    if not self._validar_capacidad(
                        camion, 
                        peso_actual + entrega.peso_total_kg,
                        volumen_actual + (entrega.volumen_total_m3 or 0)
                    ):
                        continue
                    
                    # Validar restricciones especiales
                    if entrega.requiere_refrigeracion and not camion.tiene_refrigeracion:
                        continue
                    
                    # Asignar entrega a ruta
                    entrega.ruta_id = ruta.id
                    entrega.estado = EstadoEntrega.ASIGNADO
                    entrega.fecha_asignacion = datetime.now()
                    entrega.orden_en_ruta = len(entregas_en_ruta) + 1
                    
                    entregas_en_ruta.append(entrega)
                    entregas_asignadas.add(entrega.id)
                    
                    peso_actual += entrega.peso_total_kg
                    volumen_actual += (entrega.volumen_total_m3 or 0)
                    
                    # Validar límite de entregas
                    if len(entregas_en_ruta) >= self.params.max_entregas_por_ruta:
                        break
                
                if len(entregas_en_ruta) >= self.params.max_entregas_por_ruta:
                    break
            
            # Solo agregar ruta si tiene entregas
            if entregas_en_ruta:
                ruta.entregas = entregas_en_ruta
                ruta.cantidad_entregas = len(entregas_en_ruta)
                ruta.peso_total_kg = peso_actual
                ruta.volumen_total_m3 = volumen_actual
                
                self.db.add(ruta)
                rutas.append(ruta)
        
        self.db.commit()
        return rutas
    
    def _validar_capacidad(
        self, 
        camion: Camion, 
        peso_total: float, 
        volumen_total: float
    ) -> bool:
        """Valida si el camión puede cargar más"""
        margen_peso = self.params.margen_seguridad_peso
        margen_volumen = self.params.margen_seguridad_volumen
        
        peso_ok = peso_total <= (camion.capacidad_peso_kg * margen_peso)
        volumen_ok = volumen_total <= (camion.capacidad_volumen_m3 * margen_volumen)
        
        return peso_ok and volumen_ok
    
    def _calcular_metricas_ruta(self, ruta: Ruta):
        """Calcula distancia, tiempo y costos de una ruta"""
        
        if not ruta.entregas:
            return
        
        # Ordenar entregas por zona y proximidad
        entregas_ordenadas = self._optimizar_secuencia(ruta.entregas)
        
        # Actualizar orden
        for i, entrega in enumerate(entregas_ordenadas, 1):
            entrega.orden_en_ruta = i
        
        # Calcular distancia total
        distancia_total = 0.0
        tiempo_total = self.params.tiempo_carga_inicial_min
        
        # Desde almacén a primera entrega
        primera = entregas_ordenadas[0]
        dist = self._calcular_distancia(
            self.ALMACEN_LAT, 
            self.ALMACEN_LNG,
            primera.cliente.lat,
            primera.cliente.lng
        )
        distancia_total += dist
        tiempo_total += self._estimar_tiempo(dist, ruta.camion)
        
        # Entre entregas
        for i in range(len(entregas_ordenadas) - 1):
            actual = entregas_ordenadas[i]
            siguiente = entregas_ordenadas[i + 1]
            
            dist = self._calcular_distancia(
                actual.cliente.lat,
                actual.cliente.lng,
                siguiente.cliente.lat,
                siguiente.cliente.lng
            )
            distancia_total += dist
            tiempo_total += self._estimar_tiempo(dist, ruta.camion)
            tiempo_total += actual.tiempo_estimado_entrega_min
        
        # Última entrega a almacén
        ultima = entregas_ordenadas[-1]
        dist = self._calcular_distancia(
            ultima.cliente.lat,
            ultima.cliente.lng,
            self.ALMACEN_LAT,
            self.ALMACEN_LNG
        )
        distancia_total += dist
        tiempo_total += self._estimar_tiempo(dist, ruta.camion)
        tiempo_total += ultima.tiempo_estimado_entrega_min
        
        # Calcular costos
        peso_promedio = ruta.peso_total_kg / 2  # Asumimos descarga gradual
        consumo_promedio = (
            ruta.camion.consumo_combustible_km_vacio + 
            ruta.camion.consumo_combustible_km_cargado
        ) / 2
        
        litros_combustible = distancia_total * consumo_promedio
        costo_combustible = litros_combustible * self.params.costo_combustible_litro
        
        horas_operacion = tiempo_total / 60.0
        costo_tiempo = horas_operacion * self.params.costo_hora_operacion
        
        costo_mantenimiento = distancia_total * self.params.costo_km_mantenimiento
        
        # Actualizar ruta
        ruta.distancia_total_km = round(distancia_total, 2)
        ruta.tiempo_total_estimado_min = int(tiempo_total)
        ruta.costo_combustible_estimado = round(costo_combustible, 2)
        ruta.costo_tiempo_estimado = round(costo_tiempo, 2)
        ruta.costo_total_estimado = round(
            costo_combustible + costo_tiempo + costo_mantenimiento, 
            2
        )
        
        # Calcular score de optimización (0-100)
        ruta.score_optimizacion = self._calcular_score(ruta)
        
        # Sumar valores de facturas
        ruta.valor_total_facturas = sum(
            e.monto_total for e in ruta.entregas if e.monto_total
        )
        
        self.db.commit()
    
    def _optimizar_secuencia(self, entregas: List[Entrega]) -> List[Entrega]:
        """
        Optimiza secuencia de entregas usando Nearest Neighbor
        """
        if len(entregas) <= 1:
            return entregas
        
        # Agrupar por zona primero
        por_zona = {}
        for e in entregas:
            zona_id = e.zona_id or e.cliente.zona_id
            if zona_id not in por_zona:
                por_zona[zona_id] = []
            por_zona[zona_id].append(e)
        
        secuencia_final = []
        
        # Para cada zona, aplicar nearest neighbor
        for zona_id, entregas_zona in por_zona.items():
            if len(entregas_zona) == 1:
                secuencia_final.extend(entregas_zona)
                continue
            
            # Nearest Neighbor desde almacén
            no_visitadas = list(entregas_zona)
            actual_lat, actual_lng = self.ALMACEN_LAT, self.ALMACEN_LNG
            
            while no_visitadas:
                # Encontrar la más cercana
                mas_cercana = min(
                    no_visitadas,
                    key=lambda e: self._calcular_distancia(
                        actual_lat, actual_lng,
                        e.cliente.lat, e.cliente.lng
                    )
                )
                
                secuencia_final.append(mas_cercana)
                no_visitadas.remove(mas_cercana)
                actual_lat = mas_cercana.cliente.lat
                actual_lng = mas_cercana.cliente.lng
        
        return secuencia_final
    
    def _calcular_distancia(
        self, 
        lat1: float, 
        lng1: float, 
        lat2: float, 
        lng2: float
    ) -> float:
        """
        Calcula distancia usando fórmula de Haversine
        Returns: distancia en kilómetros
        """
        R = 6371  # Radio de la Tierra en km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(dlng/2) * math.sin(dlng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distancia = R * c
        
        # Factor de corrección (calles no son línea recta)
        return distancia * 1.3
    
    def _estimar_tiempo(self, distancia_km: float, camion: Camion) -> float:
        """
        Estima tiempo de viaje en minutos
        """
        velocidad = camion.velocidad_promedio_kmh
        tiempo_min = (distancia_km / velocidad) * 60
        return tiempo_min
    
    def _calcular_score(self, ruta: Ruta) -> float:
        """
        Calcula score de optimización (0-100)
        Considera: eficiencia de distancia, uso de capacidad, balance de carga
        """
        if not ruta.entregas:
            return 0.0
        
        # 1. Eficiencia de capacidad (peso)
        uso_capacidad = (ruta.peso_total_kg / ruta.camion.capacidad_peso_kg) * 100
        score_capacidad = min(uso_capacidad, 100)  # Max 100
        
        # 2. Eficiencia de distancia (vs distancia lineal)
        distancia_lineal_total = sum(
            self._calcular_distancia(
                self.ALMACEN_LAT, self.ALMACEN_LNG,
                e.cliente.lat, e.cliente.lng
            ) * 2  # Ida y vuelta
            for e in ruta.entregas
        )
        
        if distancia_lineal_total > 0:
            eficiencia_dist = (distancia_lineal_total / ruta.distancia_total_km) * 100
            score_distancia = min(eficiencia_dist, 100)
        else:
            score_distancia = 50
        
        # 3. Cantidad de entregas (más es mejor hasta el límite)
        score_entregas = (len(ruta.entregas) / self.params.max_entregas_por_ruta) * 100
        
        # Score ponderado
        score_final = (
            score_capacidad * 0.4 +
            score_distancia * 0.4 +
            score_entregas * 0.2
        )
        
        return round(min(score_final, 100), 1)
    
    def reasignar_entrega(
        self, 
        entrega_id: int, 
        nueva_ruta_id: int
    ) -> bool:
        """Reasigna manualmente una entrega a otra ruta"""
        entrega = self.db.query(Entrega).get(entrega_id)
        nueva_ruta = self.db.query(Ruta).get(nueva_ruta_id)
        
        if not entrega or not nueva_ruta:
            return False
        
        # Validar capacidad de la nueva ruta
        peso_actual = nueva_ruta.peso_total_kg + entrega.peso_total_kg
        if not self._validar_capacidad(
            nueva_ruta.camion,
            peso_actual,
            nueva_ruta.volumen_total_m3 + (entrega.volumen_total_m3 or 0)
        ):
            logger.warning("No hay capacidad en la nueva ruta")
            return False
        
        # Remover de ruta anterior
        if entrega.ruta_id:
            ruta_anterior = self.db.query(Ruta).get(entrega.ruta_id)
            if ruta_anterior:
                self._calcular_metricas_ruta(ruta_anterior)
        
        # Asignar a nueva ruta
        entrega.ruta_id = nueva_ruta_id
        entrega.orden_en_ruta = len(nueva_ruta.entregas) + 1
        
        # Recalcular métricas
        self._calcular_metricas_ruta(nueva_ruta)
        
        self.db.commit()
        logger.info(f"Entrega {entrega_id} reasignada a ruta {nueva_ruta_id}")
        return True