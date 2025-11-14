import os
import requests
import sys

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
    Obtiene la lista de adjuntos de un ticket de Jira específico.
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
            print(f"El ticket {JIRA_ISSUE_KEY} no tiene adjuntos.")
            # Si no hay adjuntos, salimos sin error
            return 

        print(f"Se encontraron {len(attachments)} adjuntos.")

        # Crear carpeta si no existe ****


        # Verificar cuantos archivos tiene la carpeta e imprimir ****
        
        # Aquí puedes agregar la lógica para procesar los adjuntos,
        # por ejemplo, descargarlos o subir su metadata a un archivo.
        
        # Ejemplo: Imprimir el nombre y URL de cada adjunto
        for i, att in enumerate(attachments):
            print(f"  - Adjunto {i+1}:")
            print(f"    - Nombre: {att['filename']}")
            print(f"    - URL de Contenido: {att['content']}") # Esta URL requiere autenticación
            print(f"    - Autor: {att['author']['displayName']}")
            # copiar adjunto a carpeta correspondiente ****


        # Verificar nuevamente cuantos archivos debe tener la carpeta ****

        # Si la carpeta tiene un archivo txt leer y contar registros ****
        
        # usando `requests.get(att['content'], auth=auth, stream=True)`

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
