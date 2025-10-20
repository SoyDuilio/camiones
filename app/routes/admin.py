from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "title": "Dashboard Admin"
    })
