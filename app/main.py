from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, Base
from app.routes import admin, chofer, api

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Rutas - CAMIONES")

# Static files y templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Rutas
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(chofer.router, prefix="/chofer", tags=["chofer"])
app.include_router(api.router, prefix="/api", tags=["api"])

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
