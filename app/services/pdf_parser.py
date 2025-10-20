from PyPDF2 import PdfReader
import re

async def extract_invoice_data(pdf_path: str) -> dict:
    '''
    Extrae datos de una factura PDF
    '''
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        # Patrones comunes en facturas peruanas
        numero_factura = re.search(r'F\d{3}-\d{7}', text)
        ruc = re.search(r'RUC[:\s]*(\d{11})', text)
        monto = re.search(r'TOTAL[:\s]*S/\.?\s*([\d,]+\.\d{2})', text)
        
        return {
            "numero_factura": numero_factura.group(0) if numero_factura else "",
            "ruc_cliente": ruc.group(1) if ruc else "",
            "nombre_cliente": "",  # Requiere lógica más compleja
            "direccion": "",
            "monto_total": float(monto.group(1).replace(',', '')) if monto else 0.0,
            "fecha": ""
        }
    except Exception as e:
        print(f"Error parseando PDF: {e}")
        return {}
