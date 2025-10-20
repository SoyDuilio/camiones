#!/usr/bin/env python3
'''
Script para poblar la base de datos con datos realistas de Iquitos
'''

from app.database import SessionLocal, engine
from app.models import Base, Zona, Camion, Cliente
from datetime import datetime

# Crear tablas
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Zonas de Iquitos (corregidas)
zonas = [
    {"nombre": "Centro", "descripcion": "Plaza de Armas, Malecón, Jr. Próspero", "color_hex": "#FF6B6B"},
    {"nombre": "Punchana", "descripcion": "Zona norte de Iquitos", "color_hex": "#4ECDC4"},
    {"nombre": "Carretera Iquitos-Nauta", "descripcion": "Km 0 al 15", "color_hex": "#45B7D1"},
    {"nombre": "Belén", "descripcion": "Puerto Belén, Pasaje Paquito", "color_hex": "#FFA07A"},
    {"nombre": "San Juan", "descripcion": "Zona San Juan Bautista", "color_hex": "#98D8C8"},
    {"nombre": "Moronacocha", "descripcion": "Zona lago Moronacocha", "color_hex": "#F7DC6F"},
    {"nombre": "Av. La Marina", "descripcion": "Avenida La Marina", "color_hex": "#BB8FCE"},
    {"nombre": "Aeropuerto", "descripcion": "Zona aeropuerto, Av. Abelardo Quiñones", "color_hex": "#85C1E2"},
]

print("Creando zonas...")
for zona_data in zonas:
    zona = Zona(**zona_data)
    db.add(zona)
db.commit()

# Camiones
camiones = [
    {"placa": "AQP-123", "chofer_nombre": "Juan Pérez", "chofer_telefono": "965123456"},
    {"placa": "IQT-456", "chofer_nombre": "Carlos Ruiz", "chofer_telefono": "965234567"},
    {"placa": "TRU-789", "chofer_nombre": "Miguel Torres", "chofer_telefono": "965345678"},
    {"placa": "LIM-012", "chofer_nombre": "Roberto Sánchez", "chofer_telefono": "965456789"},
    {"placa": "CUS-345", "chofer_nombre": "José García", "chofer_telefono": "965567890"},
    {"placa": "PIU-678", "chofer_nombre": "Luis Ramírez", "chofer_telefono": "965678901"},
    {"placa": "CHI-901", "chofer_nombre": "Pedro Vásquez", "chofer_telefono": "965789012"},
    {"placa": "TAC-234", "chofer_nombre": "Antonio Flores", "chofer_telefono": "965890123"},
    {"placa": "HUA-567", "chofer_nombre": "Manuel Díaz", "chofer_telefono": "965901234"},
    {"placa": "ARE-890", "chofer_nombre": "Francisco Castro", "chofer_telefono": "965012345"},
]

print("Creando camiones...")
for camion_data in camiones:
    camion = Camion(**camion_data)
    db.add(camion)
db.commit()

# Clientes realistas de Iquitos
clientes = [
    # Centro
    {"nombre": "Bodega El Paisano", "direccion": "Jr. Próspero 456", "zona_id": 1, "lat": -3.7437, "lng": -73.2516, "telefono": "965111222"},
    {"nombre": "Minimarket San José", "direccion": "Jr. Moore 234", "zona_id": 1, "lat": -3.7447, "lng": -73.2526, "telefono": "965222333"},
    {"nombre": "Bodega Doña Rosa", "direccion": "Malecón Tarapacá 123", "zona_id": 1, "lat": -3.7427, "lng": -73.2506, "telefono": "965333444"},
    
    # Punchana
    {"nombre": "Bodega Mi Esperanza", "direccion": "Calle Los Sauces 789", "zona_id": 2, "lat": -3.7300, "lng": -73.2400, "telefono": "965444555"},
    {"nombre": "Minimarket El Paraíso", "direccion": "Av. Punchana 567", "zona_id": 2, "lat": -3.7320, "lng": -73.2420, "telefono": "965555666"},
    
    # Carretera Iquitos-Nauta
    {"nombre": "Bodega Los Andes", "direccion": "Carretera Iquitos-Nauta Km 3.5", "zona_id": 3, "lat": -3.7650, "lng": -73.2350, "telefono": "965666777"},
    {"nombre": "Comercial Santa Rosa", "direccion": "Carretera Iquitos-Nauta Km 7", "zona_id": 3, "lat": -3.7800, "lng": -73.2200, "telefono": "965777888"},
    {"nombre": "Bodega El Triunfo", "direccion": "Carretera Iquitos-Nauta Km 10", "zona_id": 3, "lat": -3.7950, "lng": -73.2050, "telefono": "965888999"},
    
    # Belén
    {"nombre": "Bodega Doña María", "direccion": "Pasaje Paquito 234", "zona_id": 4, "lat": -3.7500, "lng": -73.2600, "telefono": "965999000"},
    {"nombre": "Tienda El Puerto", "direccion": "Jr. 9 de Diciembre 456", "zona_id": 4, "lat": -3.7520, "lng": -73.2620, "telefono": "965000111"},
    
    # San Juan
    {"nombre": "Bodega San Juanito", "direccion": "Av. Participación 890", "zona_id": 5, "lat": -3.7600, "lng": -73.2700, "telefono": "965111000"},
    {"nombre": "Minimarket Buen Precio", "direccion": "Jr. Comercio 345", "zona_id": 5, "lat": -3.7620, "lng": -73.2720, "telefono": "965222111"},
    
    # Moronacocha
    {"nombre": "Bodega El Lago", "direccion": "Calle Las Palmeras 123", "zona_id": 6, "lat": -3.7350, "lng": -73.2300, "telefono": "965333222"},
    {"nombre": "Comercial Moronacocha", "direccion": "Jr. Los Pinos 678", "zona_id": 6, "lat": -3.7370, "lng": -73.2320, "telefono": "965444333"},
    
    # Av. La Marina
    {"nombre": "Bodega La Marina", "direccion": "Av. La Marina 456", "zona_id": 7, "lat": -3.7380, "lng": -73.2280, "telefono": "965555444"},
    {"nombre": "Minimarket Costa Azul", "direccion": "Av. La Marina 789", "zona_id": 7, "lat": -3.7390, "lng": -73.2270, "telefono": "965666555"},
    
    # Aeropuerto
    {"nombre": "Bodega Aeropuerto", "direccion": "Av. Abelardo Quiñones 234", "zona_id": 8, "lat": -3.7850, "lng": -73.3100, "telefono": "965777666"},
    {"nombre": "Comercial El Vuelo", "direccion": "Av. Abelardo Quiñones 567", "zona_id": 8, "lat": -3.7870, "lng": -73.3120, "telefono": "965888777"},
]

print("Creando clientes...")
for cliente_data in clientes:
    cliente = Cliente(**cliente_data)
    db.add(cliente)
db.commit()

print("✅ Base de datos poblada exitosamente!")
print(f"   - {len(zonas)} zonas")
print(f"   - {len(camiones)} camiones")
print(f"   - {len(clientes)} clientes")

db.close()
