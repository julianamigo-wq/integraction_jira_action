import os
import requests
import sys
from pathlib import Path 

# --- CONFIGURACIÓN ---
JIRA_URL = os.getenv('JIRA_BASE_URL')
JIRA_USER = os.getenv('JIRA_API_USER')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')

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

    api_url = f"{JIRA_URL}/rest/api/3/issue/{JIRA_ISSUE_KEY}"
    params = {'fields': 'attachment'}
    auth = (JIRA_USER, JIRA_TOKEN)

    try:
        response = requests.get(api_url, auth=auth, params=params)
        response.raise_for_status()

        issue_data = response.json()
        attachments = issue_data['fields']['attachment']
        
        if not attachments:
            print(f"El ticket {JIRA_ISSUE_KEY} no tiene adjuntos. Finalizando.")
            return 

        print(f"Se encontraron {len(attachments)} adjuntos.")

        # Crear carpeta si no existe ****
        # '..' sube un nivel de la raíz del repositorio
        
        # Primero intentamos con 'Documentos' (típico en Windows ES)
        base_dir = Path('../Documentos')
        
        # Si 'Documentos' no es la carpeta, intentamos con 'Documents' (típico en Windows EN)
        # NOTA: Esto solo tiene sentido si el directorio de trabajo es la raíz del repositorio.
        if not base_dir.exists():
             base_dir = Path('../Documents')
        
        # Creamos la carpeta base si no existe (parents=True maneja ../)
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # La carpeta final de destino dentro de la carpeta base (e.g., ../Documentos/PROYECTO-123)
        target_dir = base_dir / JIRA_ISSUE_KEY
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Carpeta de destino creada/verificada: {target_dir.resolve()}")
        # Fin de 'Crear carpeta si no existe ****'


        # Verificar cuantos archivos tiene la carpeta e imprimir ****
        files_before = [f for f in target_dir.iterdir() if f.is_file()]
        print(f"La carpeta '{JIRA_ISSUE_KEY}' tiene {len(files_before)} archivos ANTES de la descarga.")
        # Fin de 'Verificar cuantos archivos tiene la carpeta e imprimir ****'
        
        
        downloaded_count = 0
        for i, att in enumerate(attachments):
            filename = att['filename']
            content_url = att['content']
            
            print(f"  - Adjunto {i+1}:")
            print(f"    - Nombre: {filename}")
            
            # copiar adjunto a carpeta correspondiente ****
            file_path = target_dir / filename
            
            try:
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
        txt_files = [f for f in files_after if f.suffix.lower() == '.txt']
        
        if txt_files:
            txt_file_path = txt_files[0]
            try:
                # Usamos el modo de lectura con codificación UTF-8
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
