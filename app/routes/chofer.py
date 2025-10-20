from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/{camion_id}")
async def chofer_panel(request: Request, camion_id: int, db: Session = Depends(get_db)):
    return templates.TemplateResponse("chofer_panel.html", {
        "request": request,
        "camion_id": camion_id,
        "title": "Panel Chofer"
    })
