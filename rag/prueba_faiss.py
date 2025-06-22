import faiss
import pickle
import os
from sentence_transformers import SentenceTransformer

# === Paths ===
faiss_path = "cv_vector_db/cv_index.faiss"
meta_path = "cv_vector_db/cv_metadata.pkl"

# === Paso 1: Cargar modelo de embeddings ===
print("🔄 Cargando modelo de embeddings...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# === Paso 2: Cargar FAISS index y metadatos ===
print("📁 Cargando índice y metadatos...")
index = faiss.read_index(faiss_path)

with open(meta_path, "rb") as f:
    metadata = pickle.load(f)

resume_ids = metadata["ids"]
resume_texts = metadata["texts"]

# === Paso 3: Definir la Job Description (JD) ===
job_description = """
We are seeking an experienced Staff Accountant with strong knowledge in GAAP, financial reporting, and month-end reconciliation. 
Proficiency in QuickBooks, Excel, and ADP is a plus. Ideal candidate has prior experience in managing payroll and preparing tax reports.
"""

# === Paso 4: Codificar la JD y hacer búsqueda ===
print("🔍 Buscando CVs más similares...")
query_emb = model.encode([job_description], normalize_embeddings=True)
D, I = index.search(query_emb, k=1)

# === Paso 5: Mostrar resultados ===
print("\n🎯 Top 1 CVs más similares:\n")
for rank, idx in enumerate(I[0]):
    print(f"#{rank + 1} 📌 CV ID: {resume_ids[idx]}")
    print(resume_texts[idx][:500], "...\n")
