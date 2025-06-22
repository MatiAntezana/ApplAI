import faiss
import pickle
from sentence_transformers import SentenceTransformer


def get_best_cvs(job_description, faiss_path="cv_vector_db/cv_index.faiss", meta_path="cv_vector_db/cv_metadata.pkl", top_k=3):
    """
    Busca los CVs más similares a una descripción de trabajo dada utilizando FAISS y un modelo de embeddings.
    
    Args:
        job_description (str): Descripción del trabajo para la cual se buscan CVs.
        faiss_path (str): Ruta al índice FAISS.
        meta_path (str): Ruta al archivo de metadatos.
        top_k (int): Número de CVs a retornar.
    
    Returns:
        list: Lista de tuplas con los IDs del CV y el texto del CV más similar.
    """

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
    # job_description = """ We are looking for someone with experience in the field of healthcare, environment, or agriculture. """

    # === Paso 4: Codificar la JD y hacer búsqueda ===
    print("🔍 Buscando CVs más similares...")
    query_emb = model.encode([job_description], normalize_embeddings=True)
    D, I = index.search(query_emb, k=top_k)

    # === Paso 5: Mostrar resultados ===
    print(f"\n🎯 Top {top_k} CVs más similares:\n")
    for rank, idx in enumerate(I[0]):
        print(f"#{rank + 1} 📌 CV ID: {resume_ids[idx]}")
        # print(resume_texts[idx][:500], "...\n")

    return [(resume_ids[idx], resume_texts[idx]) for idx in I[0]]
