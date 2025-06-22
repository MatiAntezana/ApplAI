import asyncio
from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field
import json
import re
import fitz
import os
import csv
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from utils import extract_cv_info, guardar_resultado

# === CONFIGURACIÓN ===
CSV_PATH = "cvs.csv"
VECTOR_DIR = "cv_vector_db"
FAISS_PATH = os.path.join(VECTOR_DIR, "cv_index.faiss")
META_PATH = os.path.join(VECTOR_DIR, "cv_metadata.pkl")

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

    guardar_resultado(result)
   
     
if __name__ == "__main__":
    main("a")