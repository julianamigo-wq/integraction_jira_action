import os
import requests
import sys
from pathlib import Path # Importación necesaria para el manejo de rutas

# --- CONFIGURACIÓN ---
# Las variables de entorno serán inyectadas por GitHub Actions.
# Estas son necesarias para autenticarse con la API de Jira.
JIRA_URL = os.getenv('JIRA_BASE_URL') # Ejemplo: 'https://tuempresa.atlassian.net'
JIRA_USER = os.getenv('JIRA_API_USER') # Email del usuario
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN') # Token de API generado en Atlassian

# La clave del ticket (ej: 'PROYECTO-123') viene como argumento de línea de comandos
# que será proporcionado por el flujo de trabajo de GitHub Action.
try:
    JIRA_ISSUE_KEY = sys.argv[1]
except IndexError:
    print("Error: La clave del ticket de Jira no fue proporcionada como argumento.")
    sys.exit(1)

# --- FUNCIÓN PRINCIPAL ---

def get_issue_attachments():
    """
    Obtiene la lista de adjuntos de un ticket de Jira específico y los descarga.
    """
    print(f"Buscando adjuntos para el ticket: {JIRA_ISSUE_KEY}...")

    # Endpoint de la API de Jira para obtener la información del ticket
    api_url = f"{JIRA_URL}/rest/api/3/issue/{JIRA_ISSUE_KEY}"
    
    # Parámetros para limitar los campos de la respuesta, solo necesitamos los attachments.
    params = {
        'fields': 'attachment'
    }

    # Autenticación usando Basic Auth con Email y Token de API
    auth = (JIRA_USER, JIRA_TOKEN)

    try:
        response = requests.get(api_url, auth=auth, params=params)
        response.raise_for_status() # Lanza un error para códigos de estado 4xx/5xx

        issue_data = response.json()
        
        # Acceder a la lista de adjuntos en la estructura JSON
        attachments = issue_data['fields']['attachment']
        
        if not attachments:
            print(f"El ticket {JIRA_ISSUE_KEY} no tiene adjuntos. Finalizando.")
            # Si no hay adjuntos, salimos sin error
            return 

        print(f"Se encontraron {len(attachments)} adjuntos.")

        # Crear carpeta si no existe ****
        # Definimos la ruta base relativa, intentando primero con 'Documentos' para Windows.
        # Si la carpeta principal 'Documentos' no existe, se creará también.
        
        # Path('../..') sube dos niveles desde la ubicación actual (donde se ejecuta el script)
        # luego entra a 'Documentos' o 'Documents', y finalmente crea la carpeta con la clave.
        base_dir = Path('../Documentos') # Intenta con la versión en español
        
        # Si la ruta en español no existe (y en un entorno GitHub Actions podría no existir ninguna de las dos)
        # se crea la carpeta 'Documentos' si no existe.
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # La carpeta final de destino
        target_dir = base_dir / JIRA_ISSUE_KEY
        
        # Crea la subcarpeta usando el valor de JIRA_ISSUE_KEY si no existe.
        # parents=True crea el directorio base si fuera necesario.
        # exist_ok=True evita errores si ya existe.
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Carpeta de destino creada/verificada: {target_dir.resolve()}")
        # Fin de 'Crear carpeta si no existe ****'


        # Verificar cuantos archivos tiene la carpeta e imprimir ****
        # Listamos solo archivos (usando iterdir y is_file)
        files_before = [f for f in target_dir.iterdir() if f.is_file()]
        print(f"La carpeta '{JIRA_ISSUE_KEY}' tiene {len(files_before)} archivos ANTES de la descarga.")
        # Fin de 'Verificar cuantos archivos tiene la carpeta e imprimir ****'
        
        
        # Aquí puedes agregar la lógica para procesar los adjuntos,
        # por ejemplo, descargarlos o subir su metadata a un archivo.
        
        # Ejemplo: Imprimir el nombre y URL de cada adjunto
        downloaded_count = 0
        for i, att in enumerate(attachments):
            filename = att['filename']
            content_url = att['content']
            
            print(f"  - Adjunto {i+1}:")
            print(f"    - Nombre: {filename}")
            
            # copiar adjunto a carpeta correspondiente ****
            
            file_path = target_dir / filename
            
            try:
                # Usamos stream=True para descargas grandes y lo hacemos con el mismo 'auth'
                att_response = requests.get(content_url, auth=auth, stream=True)
                att_response.raise_for_status()
                
                # Escribir el contenido en el archivo de destino en modo binario ('wb')
                with open(file_path, 'wb') as f:
                    for chunk in att_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"    - DESCARGA EXITOSA en: {file_path.name}")
                downloaded_count += 1
                
            except requests.exceptions.HTTPError as e:
                print(f"    - ERROR: No se pudo descargar {filename}. Error HTTP: {e.response.status_code}")
                # El token debe tener permisos de descarga.
            except Exception as e:
                print(f"    - ERROR: Ocurrió un error inesperado durante la descarga de {filename}: {e}")
            # Fin de 'copiar adjunto a carpeta correspondiente ****'


        # Verificar nuevamente cuantos archivos debe tener la carpeta ****
        files_after = [f for f in target_dir.iterdir() if f.is_file()]
        print("-" * 30)
        print(f"PROCESO DE DESCARGA FINALIZADO.")
        print(f"Archivos descargados correctamente según el conteo: {downloaded_count}")
        print(f"Archivos totales en la carpeta '{JIRA_ISSUE_KEY}': {len(files_after)}")
        # Fin de 'Verificar nuevamente cuantos archivos debe tener la carpeta ****'


        # Si la carpeta tiene un archivo txt leer y contar registros ****
        
        # Buscamos el primer archivo que termine en .txt
        txt_files = [f for f in files_after if f.suffix.lower() == '.txt']
        
        if txt_files:
            txt_file_path = txt_files[0]
            try:
                with open(txt_file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for line in f)
                print(f"  > Archivo TXT encontrado: {txt_file_path.name}")
                print(f"  > El archivo TXT tiene {line_count} registros (líneas).")
            except Exception as e:
                print(f"  > ERROR al leer el archivo TXT '{txt_file_path.name}': {e}")
        else:
            print("  > No se encontraron archivos .txt para contar registros.")
        
        # Fin de 'Si la carpeta tiene un archivo txt leer y contar registros ****'


    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP al llamar a la API de Jira: {e}")
        print(f"Respuesta de Jira: {e.response.text}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al llamar a la API de Jira: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    get_issue_attachments()
