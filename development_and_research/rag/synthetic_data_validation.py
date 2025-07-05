import os
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from scipy.stats import spearmanr
from sklearn.metrics import ndcg_score
import numpy as np

def mean_reciprocal_rank(ranks):
    reciprocal_ranks = [1.0 / rank for rank in ranks]
    return np.mean(reciprocal_ranks)



def get_best_cvs(
    job_description,
    faiss_path="cv_vector_db/cv_index.faiss",
    meta_path="cv_vector_db/cv_metadata.pkl",
    top_k=5
):
    """
    Busca los CVs más similares a una descripción de trabajo dada utilizando FAISS y un modelo de embeddings.
    Devuelve los scores de similaridad coseno.
    """
    
    # === Paso 1: Cargar modelo de embeddings ===
    print("🔄 Cargando modelo de embeddings...")
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    #model = SentenceTransformer("Qwen/Qwen3-Embedding-4B", device="cpu")
    #model = SentenceTransformer("Qwen/Qwen3-Embedding-4B", device="cpu")

    # === Paso 2: Cargar FAISS index y metadatos ===
    print("📁 Cargando índice y metadatos...")
    index = faiss.read_index(faiss_path)

    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)

    resume_ids = metadata["ids"]
    resume_texts = metadata["texts"]

    if not resume_ids or not resume_texts:
        print("⚠️ No se encontraron CVs en la base de datos.")
        return []

    # === Paso 3: Codificar la JD y hacer búsqueda ===
    print("🔍 Buscando CVs más similares...")
    query_emb = model.encode([job_description], normalize_embeddings=True)
    
    D, I = index.search(query_emb, k=top_k)

    # D son las similitudes coseno porque embeddings están normalizados
    similarities = D[0]

    retrieved = []
    print(f"\n🎯 Top {top_k} CVs más similares:\n")
    for rank, (idx, score) in enumerate(zip(I[0], similarities), start=1):
        cv_id = resume_ids[idx]
        text = resume_texts[idx]
        print(f"#{rank} → CV ID: {cv_id} | Similaridad coseno: {score:.4f}")
        retrieved.append((cv_id, text, score))

    return retrieved
def read_txt(file_path: str) -> str:
    """Lee un archivo de texto y devuelve su contenido como una cadena."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def main() -> None:
    JDs = [
        "synthetic_data/JD_abogados.txt",
        "synthetic_data/JD_arquitectos.txt",
        "synthetic_data/JD_economistas.txt",
        "synthetic_data/JD_medicos.txt",
        "synthetic_data/JD_profesores.txt"
    ]

    titles = ["Abogados", "Arquitectos", "Economistas", "Médicos", "Profesores"]

    faiss_paths = [
        "cv_db_abog/cv_index.faiss",
        "cv_db_arq/cv_index.faiss",
        "cv_db_eco/cv_index.faiss",
        "cv_db_med/cv_index.faiss",
        "cv_db_prof/cv_index.faiss"
    ]

    meta_paths = [
        "cv_db_abog/cv_metadata.pkl",
        "cv_db_arq/cv_metadata.pkl",
        "cv_db_eco/cv_metadata.pkl",
        "cv_db_med/cv_metadata.pkl",
        "cv_db_prof/cv_metadata.pkl"
    ]

    for jd, title, faiss_path, meta_path in zip(JDs, titles, faiss_paths, meta_paths):
        print(f"\n🔍 Buscando CVs para el puesto de {title}...")
        job_description = read_txt(jd)
        best_cvs = get_best_cvs(
            job_description=job_description,
            faiss_path=faiss_path,
            meta_path=meta_path,
            top_k=5
        )
        if best_cvs:
            print(f"\nResultados para {title}:")
            for cv_id, text, score in best_cvs:
                print(f"CV ID: {cv_id} | Similaridad: {score:.4f}")
        else:
            print(f"No se encontraron CVs para el puesto de {title}.")

if __name__ == "__main__":
    main()