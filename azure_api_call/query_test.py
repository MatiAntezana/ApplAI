import faiss
import pickle
from sentence_transformers import SentenceTransformer
import os
import pandas as pd

def main() -> None:
    # 1. Cargar índice FAISS y metadatos
    index_path = "vector_db/cv_index.faiss"
    metadata_path = "vector_db/cv_metadata.pkl"

    print("📂 Cargando índice FAISS...")
    index = faiss.read_index(index_path)

    print("📂 Cargando metadatos (IDs y textos)...")
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)

    resume_ids = metadata["ids"]
    resume_texts = metadata["texts"]

    # 2. Cargar modelo de embeddings
    print("🧠 Cargando modelo de embeddings...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # 3. Crear Job Description para IT
    query = """
    We are looking for a Junior Software Developer with experience in Python and web development. 
    Responsibilities include developing backend APIs, maintaining databases, and collaborating with frontend engineers. 
    Familiarity with Git, RESTful services, and SQL is required. Experience with cloud services such as AWS or Azure is a plus.
    """

    # 4. Embedding + búsqueda
    query_emb = model.encode([query], normalize_embeddings=True)
    k = 5
    D, I = index.search(query_emb, k)

    # 5. Mostrar resultados
    print(f"\n🔍 Resultados top {k} para JD relacionado a Information-Technology:\n")
    for rank, idx in enumerate(I[0], start=1):
        print(f"🔹 Rank {rank} | 📌 CV ID: {resume_ids[idx]}")
        print(resume_texts[idx][:300].strip(), "...\n")

    # ahora quiero tomar los IDs de los CVs que traje, buscarlos en el CSV original y mostrar la columna Category, para ver si son IT o no

    # 6. Cargar CSV original para verificar categorías
    csv_path = "Resume.csv"
    print("📂 Cargando CSV original para verificar categorías...")
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["ID", "Category"])
    df["ID"] = df["ID"].astype(str)
    df = df.set_index("ID")
    print("🔍 Verificando categorías de los CVs encontrados...")
    for idx in I[0]:
        cv_id = resume_ids[idx]
        category = df.loc[cv_id, "Category"] if cv_id in df.index else "Unknown"
        print(f"📌 CV ID: {cv_id} | Category: {category}")
    
    print("✅ Proceso completado exitosamente.")


if __name__ == "__main__":
    main()

