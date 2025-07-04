import os
import matplotlib.pyplot as plt
import faiss
import pickle
import numpy as np
from tqdm import tqdm
from scipy.stats import spearmanr
from sentence_transformers import SentenceTransformer

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
    #model = SentenceTransformer("../mini_finetuned_Allmini")
    model = SentenceTransformer("all-MiniLM-L6-v2")

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

    
    spearman_scores = []
    mrr = []
    ndcg = []
    #for jd, title, faiss_path, meta_path in zip(JDs, titles, faiss_paths, meta_paths):
    for jd, title, faiss_path, meta_path in tqdm(zip(JDs, titles, faiss_paths, meta_paths), desc="Procesando JDs", total=len(JDs)):
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
            puntajes = []
            rankings = []
            for cv_id, text, score in best_cvs:
                print(f"CV ID: {cv_id} | Similaridad: {score:.4f}")
                puntajes.append(score)
                rankings.append(cv_id)
            spearman_scores, mrr, ndcg = calculate_scores(rankings, spearman_scores, mrr, ndcg, [1, 2, 3, 4, 5])  
        else:
            print(f"No se encontraron CVs para el puesto de {title}.")

    # calcular promedios de Spearman, MRR y DCG
    if spearman_scores:
        avg_spearman = np.mean(spearman_scores)
        avg_mrr = np.mean(mrr)
        avg_ndcg = np.mean(ndcg)
        print(f"\nResultados finales:")
        print(f"Spearman promedio: {avg_spearman:.4f}, MRR promedio: {avg_mrr:.4f}, DCG promedio: {avg_ndcg:.4f}")

    # Hacer un gráfico de barras de Spearman, MRR y DCG
    plt.figure(figsize=(6, 6))
    # en negrita lo que este escrito en los ejes
    plt.bar(['Spearman', 'MRR', 'nDCG'], [avg_spearman, avg_mrr, avg_ndcg], color=['red', 'red', 'red'], alpha=1)
    plt.ylabel('Score')
    plt.ylim(0, 1)
    plt.grid(axis='y', linestyle='--', alpha=1)
    plt.savefig('synthetic_data_validation_results.png')
    plt.show()

            
    """        
    print("Prof")
    get_best_cvs(
        job_description = read_txt("synthetic_data/JD_profesores.txt") ,
        faiss_path="cv_db_prof/cv_index.faiss",
        meta_path="cv_db_prof/cv_metadata.pkl",
        top_k=5
    )"""

def calculate_scores(ranking_ids, spearman_scores, mrr, ndcg, ground_truth_ids):
    """
    Calcula Spearman, MRR y nDCG para los rankings y puntajes dados.
    """
    # Spearman
    try:
        spearman_corr, _ = spearmanr(ranking_ids, ground_truth_ids)
        spearman_scores.append(spearman_corr)
    except Exception as e:
        print("Error en Spearman:", e)
        spearman_scores.append(0)

    # MRR (asumiendo ground_truth_ids[0] es el más relevante)
    first_relevant = ground_truth_ids[0]
    try:
        rank = ranking_ids.index(first_relevant)
        mrr.append(1 / (rank + 1))
    except ValueError:
        mrr.append(0)

    # nDCG
    ndcg_val = ndcg_from_rankings(ground_truth_ids, ranking_ids)
    ndcg.append(ndcg_val)

    print(f"Spearman: {spearman_scores[-1]:.4f}, MRR: {mrr[-1]:.4f}, nDCG: {ndcg[-1]:.4f}")
    return spearman_scores, mrr, ndcg


def dcg(relevances):
    return sum(rel / np.log2(idx + 2) for idx, rel in enumerate(relevances))

def ndcg_from_rankings(ground_truth_ids, rankings):
    """
    Calcula nDCG dado un ranking de IDs y el orden correcto de ground_truth_ids.
    La relevancia se asigna en orden decreciente: 5, 4, 3, 2, 1.
    """
    # Relevancia esperada en orden correcto
    ideal_relevances = [5, 4, 3, 2, 1]
    id_to_relevance = dict(zip(ground_truth_ids, ideal_relevances))

    # Relevancias según el orden predicho por el modelo
    predicted_relevances = [id_to_relevance.get(cv_id, 0) for cv_id in rankings]

    # DCG y IDCG
    dcg_score = dcg(predicted_relevances)
    idcg_score = dcg(ideal_relevances)

    if idcg_score == 0:
        return 0.0
    return dcg_score / idcg_score



if __name__ == "__main__":
    main()