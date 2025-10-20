// Funciones principales del frontend

console.log('CAMIONES App cargada');

// Upload PDF
document.addEventListener('DOMContentLoaded', () => {
    const pdfInput = document.getElementById('pdf-input');
    if (pdfInput) {
        pdfInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) {
                await uploadFile(file, '/api/upload-pdf');
            }
        });
    }
    
    const photoInput = document.getElementById('photo-input');
    if (photoInput) {
        photoInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) {
                await uploadFile(file, '/api/upload-photo');
            }
        });
    }
});

async function uploadFile(file, endpoint) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        console.log('Resultado:', result);
        alert('Archivo procesado exitosamente');
    } catch (error) {
        console.error('Error:', error);
        alert('Error al procesar archivo');
    }
}
