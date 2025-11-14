import os
import requests
import sys
from pathlib import Path 

# --- CONFIGURACIÓN ---
# Las variables de entorno serán inyectadas por GitHub Actions.
JIRA_URL = os.getenv('JIRA_BASE_URL') # Ejemplo: 'https://tuempresa.atlassian.net'
JIRA_USER = os.getenv('JIRA_API_USER') # Email del usuario
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN') # Token de API generado en Atlassian

# La clave del ticket (ej: 'PROYECTO-123') viene como argumento de línea de comandos
try:
    JIRA_ISSUE_KEY = sys.argv[1]
except IndexError:
    print("Error: La clave del ticket de Jira no fue proporcionada como argumento.")
    sys.exit(1)

# --- FUNCIÓN PRINCIPAL ---

def get_issue_attachments():
    """
    Obtiene la lista de adjuntos de un ticket de Jira específico y los descarga en la carpeta Documentos.
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
        try:
            # 1. Obtenemos el directorio principal del usuario (C:\Users\TuUsuario).
            user_home = os.path.expanduser('~')
            
            # 2. Construimos la ruta segura a la carpeta 'Documents' del usuario de Windows.
            # Aunque se muestre en español, el nombre lógico del sistema suele ser 'Documents'.
            base_dir = Path(os.path.join(user_home, 'Documents'))
            
            # 3. Definimos la carpeta de destino: [Documentos]/[JIRA_ISSUE_KEY]
            target_dir = base_dir / JIRA_ISSUE_KEY
            
            # 4. Creamos la subcarpeta si no existe.
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"Carpeta de destino creada/verificada: {target_dir.resolve()}")

        except Exception as e:
            print(f"ERROR: No se pudo crear la carpeta en la ruta de Documentos del usuario. Error: {e}")
            sys.exit(1)
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
                # Se necesita la autenticación para la descarga del contenido
                att_response = requests.get(content_url, auth=auth, stream=True)
                att_response.raise_for_status()
                
                # Escribir el contenido en el archivo en modo binario ('wb')
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
                # Abrimos el archivo TXT para contar las líneas/registros
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
