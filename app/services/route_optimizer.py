from sqlalchemy.orm import Session
from app.models import Entrega, Camion, Zona

def asignar_facturas_a_camiones(db: Session, fecha: str):
    '''
    Asigna facturas pendientes a camiones según zona
    Algoritmo simple para demo
    '''
    entregas_pendientes = db.query(Entrega).filter(
        Entrega.estado == "pendiente"
    ).all()
    
    camiones_activos = db.query(Camion).filter(
        Camion.activo == True
    ).all()
    
    # Agrupar por zona
    entregas_por_zona = {}
    for entrega in entregas_pendientes:
        zona_id = entrega.zona_id
        if zona_id not in entregas_por_zona:
            entregas_por_zona[zona_id] = []
        entregas_por_zona[zona_id].append(entrega)
    
    # Asignar balanceadamente
    camion_idx = 0
    for zona_id, entregas in entregas_por_zona.items():
        for entrega in entregas:
            entrega.camion_id = camiones_activos[camion_idx].id
            entrega.estado = "asignado"
            camion_idx = (camion_idx + 1) % len(camiones_activos)
    
    db.commit()
    return True
