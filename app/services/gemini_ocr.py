import google.generativeai as genai
from app.config import settings
from PIL import Image

genai.configure(api_key=settings.GEMINI_API_KEY)

async def extract_from_image(image_path: str) -> dict:
    '''
    Extrae datos de factura usando Gemini Vision
    '''
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(image_path)
        
        prompt = '''
        Analiza esta factura y extrae la siguiente información en formato JSON:
        {
            "numero_factura": "",
            "ruc_cliente": "",
            "nombre_cliente": "",
            "direccion": "",
            "monto_total": 0.0,
            "fecha": ""
        }
        
        Si algún dato no está visible, deja el campo vacío o en 0.
        '''
        
        response = model.generate_content([prompt, img])
        
        # Aquí procesarías la respuesta para extraer el JSON
        # Por ahora retornamos un mock
        return {
            "numero_factura": "F001-0001234",
            "ruc_cliente": "20123456789",
            "nombre_cliente": "Bodega El Paisano",
            "direccion": "Jr. Próspero 456, Iquitos",
            "monto_total": 850.50,
            "fecha": "2025-10-20"
        }
    except Exception as e:
        print(f"Error en Gemini OCR: {e}")
        return {}
