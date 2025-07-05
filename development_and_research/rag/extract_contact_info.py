import asyncio
from openai import AsyncAzureOpenAI
import os
from utils import extract_cv_info, guardar_resultado

# === CONFIGURACIÓN ===
VECTOR_DIR = "cv_db_giaco"
FAISS_PATH = os.path.join(VECTOR_DIR, "cv_index.faiss")
META_PATH = os.path.join(VECTOR_DIR, "cv_metadata.pkl")
CSV_PATH = os.path.join(VECTOR_DIR, "cv_data.csv")


# Crear carpetas si no existen
os.makedirs(VECTOR_DIR, exist_ok=True)

def read_txt(file_path: str) -> str:
    """Lee un archivo de texto y devuelve su contenido como una cadena."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def main(cv_file_path: str):
    API_KEY = "4u9eeKTcKNBvzIqH8PdwKGPcFt0oOIrVg03KDrRdshQBthudt701JQQJ99BEACHYHv6XJ3w3AAAAACOGdOzM"
    ENDPOINT = "https://tizia-maebl6ih-eastus2.cognitiveservices.azure.com/"
    DEPLOYMENT = "gpt-4o-mini-tiziano"
    azure_client = AsyncAzureOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint=ENDPOINT,
        api_key=API_KEY
    )
    cv_text = read_txt(cv_file_path)

    result = asyncio.run(extract_cv_info(cv_text, azure_client, DEPLOYMENT))

    print("Resultado de la extracción:", result)

    guardar_resultado(result, CSV_PATH, FAISS_PATH, META_PATH)

if __name__ == "__main__":
    cv_file_path = "synthetic_data/linkedin_profile_content.txt"  # Ruta al archivo de CV
    main(cv_file_path)
    print("Extracción de información de CV completada.")
    print(f"Resultados guardados en {CSV_PATH}, {FAISS_PATH} y {META_PATH}.")
