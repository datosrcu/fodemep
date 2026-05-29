from flask import Flask, request, jsonify, send_from_directory
import os
import datetime
import generar_tablero

app = Flask(__name__, static_folder='.')

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    # Servir el dashboard generado tablero_incidencias.html
    return send_from_directory('.', 'tablero_incidencias.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo en la petición.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío.'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Formato de archivo no permitido. Solo se aceptan archivos .xlsx o .xls.'}), 400
    
    try:
        # Guardar archivo con un prefijo de timestamp para evitar sobreescribir físicamente
        # los archivos cargados previamente en la carpeta uploads
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, safe_filename)
        file.save(filepath)
        print(f"Archivo guardado: {filepath}")
        
        # Procesar todos los archivos en la carpeta de uploads para consolidarlos
        records = generar_tablero.procesar_directorio(UPLOAD_FOLDER)
        
        # Regenerar tablero_incidencias.html
        generar_tablero.generar_html(records, 'tablero_incidencias.html')
        
        return jsonify({
            'success': True,
            'message': '¡Datos actualizados con éxito!',
            'count': len(records),
            'filename': safe_filename
        })
    except Exception as e:
        print(f"Error procesando carga: {e}")
        return jsonify({'error': f'Ocurrió un error al procesar el archivo: {str(e)}'}), 500

# Consolidación inicial al iniciar el servidor (asegura sincronización con volumen persistente)
if __name__ != '__main__':
    # Esto corre si es importado por gunicorn u otro wsgi
    try:
        if os.path.exists(UPLOAD_FOLDER) and os.listdir(UPLOAD_FOLDER):
            print("Iniciando consolidación de archivos existentes en volumen...")
            records = generar_tablero.procesar_directorio(UPLOAD_FOLDER)
            generar_tablero.generar_html(records, 'tablero_incidencias.html')
    except Exception as err:
        print(f"Error en consolidación inicial: {err}")

if __name__ == '__main__':
    # Consolidación al iniciar de forma directa
    try:
        if os.path.exists(UPLOAD_FOLDER) and os.listdir(UPLOAD_FOLDER):
            print("Iniciando consolidación de archivos existentes...")
            records = generar_tablero.procesar_directorio(UPLOAD_FOLDER)
            generar_tablero.generar_html(records, 'tablero_incidencias.html')
    except Exception as err:
        print(f"Error en consolidación inicial: {err}")
        
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
