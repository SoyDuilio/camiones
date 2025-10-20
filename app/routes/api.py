from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import gemini_ocr, pdf_parser
import shutil
from pathlib import Path

router = APIRouter()

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Guardar archivo
    upload_dir = Path("app/uploads/pdfs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Procesar PDF
    data = await pdf_parser.extract_invoice_data(str(file_path))
    
    return {"success": True, "data": data}

@router.post("/upload-photo")
async def upload_photo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Guardar imagen
    upload_dir = Path("app/uploads/photos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Procesar con Gemini Vision
    data = await gemini_ocr.extract_from_image(str(file_path))
    
    return {"success": True, "data": data}

@router.post("/actualizar-tracking/{camion_id}")
async def actualizar_tracking(camion_id: int, lat: float, lng: float, db: Session = Depends(get_db)):
    # Aquí actualizarías la posición del camión
    return {"success": True}
