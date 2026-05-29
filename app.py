from flask import Flask, request, jsonify, send_from_directory
import os
import datetime
import generar_tablero

app = Flask(__name__, static_folder='.')

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/app/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    # Estrategia ultra-robusta de persistencia: 
    # Intentar servir el HTML consolidado desde el volumen persistente (UPLOAD_FOLDER)
    persist_html = os.path.join(UPLOAD_FOLDER, 'tablero_incidencias.html')
    if os.path.exists(persist_html):
        print("Sirviendo tablero consolidado desde volumen persistente.")
        response = send_from_directory(UPLOAD_FOLDER, 'tablero_incidencias.html')
    else:
        print("Sirviendo tablero base (sin cargas previas).")
        response = send_from_directory('.', 'tablero_incidencias.html')
    
    # Deshabilitar por completo el caché del navegador y proxies intermedios
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

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
        print(f"Archivo guardado en volumen: {filepath}")
        
        # Procesar todos los archivos en la carpeta de uploads para consolidarlos
        records = generar_tablero.procesar_directorio(UPLOAD_FOLDER, os.path.join(UPLOAD_FOLDER, 'tablero_incidencias.html'))
        
        # Guardar el HTML regenerado tanto en la raíz como en la carpeta persistente
        generar_tablero.generar_html(records, 'tablero_incidencias.html')
        generar_tablero.generar_html(records, os.path.join(UPLOAD_FOLDER, 'tablero_incidencias.html'))
        
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
            records = generar_tablero.procesar_directorio(UPLOAD_FOLDER, os.path.join(UPLOAD_FOLDER, 'tablero_incidencias.html'))
            generar_tablero.generar_html(records, 'tablero_incidencias.html')
            generar_tablero.generar_html(records, os.path.join(UPLOAD_FOLDER, 'tablero_incidencias.html'))
    except Exception as err:
        print(f"Error en consolidación inicial: {err}")

if __name__ == '__main__':
    # Consolidación al iniciar de forma directa
    try:
        if os.path.exists(UPLOAD_FOLDER) and os.listdir(UPLOAD_FOLDER):
            print("Iniciando consolidación de archivos existentes...")
            records = generar_tablero.procesar_directorio(UPLOAD_FOLDER, os.path.join(UPLOAD_FOLDER, 'tablero_incidencias.html'))
            generar_tablero.generar_html(records, 'tablero_incidencias.html')
            generar_tablero.generar_html(records, os.path.join(UPLOAD_FOLDER, 'tablero_incidencias.html'))
    except Exception as err:
        print(f"Error en consolidación inicial: {err}")
        
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)
