import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os

# 1. Cargar datos
csv_path = "Resume.csv"
df = pd.read_csv(csv_path)
df = df.dropna(subset=["Resume_str"])
resume_texts = df["Resume_str"].astype(str).tolist()
resume_ids = df["ID"].astype(str).tolist()

print(f"🧾 Total de CVs a procesar: {len(resume_texts)}")

# printear el primer CV
print("📄 Primer CV:")
print(resume_texts[0])

# 2. Cargar modelo de embeddings
print("🧠 Cargando modelo 'all-MiniLM-L6-v2'...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# 3. Generar embeddings
print("🔄 Generando embeddings...")
embeddings = model.encode(resume_texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)

# 4. Crear índice FAISS
embedding_dim = embeddings.shape[1]
index = faiss.IndexFlatIP(embedding_dim)  # Usamos producto interno porque ya normalizamos
index.add(embeddings)
print(f"✅ Embeddings indexados en FAISS: {index.ntotal}")

# 5. Guardar el índice y los metadatos
output_dir = "vector_db"
os.makedirs(output_dir, exist_ok=True)

faiss.write_index(index, os.path.join(output_dir, "cv_index.faiss"))

# Guardamos los metadatos en paralelo (IDs y textos)
with open(os.path.join(output_dir, "cv_metadata.pkl"), "wb") as f:
    pickle.dump({
        "ids": resume_ids,
        "texts": resume_texts
    }, f)

print("📦 Vector database guardada exitosamente.")
