import os
import secrets
from dotenv import load_dotenv

# Cargar el .env si existe
load_dotenv()

# Ruta del archivo .env
ENV_PATH = '.env'

# Nombre de la variable
KEY_NAME = 'API_KEY'

# Ver si ya existe una clave
current_key = os.getenv(KEY_NAME)

# Si no existe, la generamos y la escribimos
if not current_key:
    new_key = secrets.token_urlsafe(32)
    print(f'Generando nueva API key: {new_key}')

    # Agregamos al .env
    with open(ENV_PATH, 'a') as env_file:
        env_file.write(f'\n{KEY_NAME}={new_key}')
    print(f'{KEY_NAME} guardada en {ENV_PATH}')
else:
    print(f'{KEY_NAME} ya existe en el archivo .env')