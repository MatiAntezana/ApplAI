import pandas as pd
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import os
from utils import guardar_resultado, CleanedCV  # Asegurate de importar bien CleanedCV si está en otro módulo

# === Rutas
CSV_INPUT = "synthetic_data/abogados.csv"
VECTOR_DIR = "cv_db_giaco"
CSV_OUTPUT = os.path.join(VECTOR_DIR, "cv_data.csv")
FAISS_PATH = os.path.join(VECTOR_DIR, "cv_index.faiss")
META_PATH = os.path.join(VECTOR_DIR, "cv_metadata.pkl")

# Crear carpetas si no existen
os.makedirs(VECTOR_DIR, exist_ok=True)

# === Leer CSV
df = pd.read_csv(CSV_INPUT)


# === Iterar y guardar cada CV
for i, row in df.iterrows():
    try:
        result = CleanedCV(
            name=row.get("name", "Not provided"),
            email=row.get("email", "Not provided"),
            phone_number=str(row.get("phone_number", "Not provided")),
            cv_information=row.get("cv_information", "Not provided")
        )
        guardar_resultado(result, CSV_OUTPUT, FAISS_PATH, META_PATH)
    except Exception as e:
        print(f"❌ Error al procesar fila {i}: {e}")

