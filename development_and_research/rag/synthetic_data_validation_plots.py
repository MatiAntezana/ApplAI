import numpy as np
from sentence_transformers import SentenceTransformer
import matplotlib.pyplot as plt
import faiss
import pickle
from scipy.stats import spearmanr
from sklearn.metrics import ndcg_score
from typing import List, Tuple

# ===============================
# Ground truth rankings por JD
# ===============================

# Ejemplo: para cada JD tenés el orden correcto de CV IDs
# Ejemplo: [1, 2, 3, 4, 5] significa que el mejor es CV 1, después el 2, etc.
GROUND_TRUTH_RANKINGS = {
    "Abogados": [1, 2, 3, 4, 5],
    "Arquitectos": [1, 2, 3, 4, 5],
    "Economistas": [1, 2, 3, 4, 5],
    "Médicos": [1, 2, 3, 4, 5],
    "Profesores": [1, 2, 3, 4, 5],
}

# ===============================
# Funciones métricas
# ===============================

def compute_mrr(true_ranking: List[int], predicted_ranking: List[int]) -> float:
    """
    Compute Mean Reciprocal Rank for a single query.
    """
    for rank, pred_id in enumerate(predicted_ranking, start=1):
        if pred_id == true_ranking[0]:
            return 1.0 / rank
    return 0.0

def compute_spearman(true_ranking: List[int], predicted_ranking: List[int]) -> float:
    """
    Spearman rank correlation between two rankings.
    """
    # Map true ids to their positions
    true_pos = {cv_id: i for i, cv_id in enumerate(true_ranking)}
    pred_positions = [true_pos.get(cv_id, len(true_ranking)) for cv_id in predicted_ranking]
    true_positions = list(range(len(predicted_ranking)))
    corr, _ = spearmanr(true_positions, pred_positions)
    return corr if not np.isnan(corr) else 0.0

def compute_ndcg(true_ranking: List[int], predicted_ranking: List[int]) -> float:
    """
    Compute NDCG@k for one query.
    """
    k = len(predicted_ranking)
    relevance = np.zeros(k)
    for i, cv_id in enumerate(predicted_ranking):
        if cv_id in true_ranking:
            relevance[i] = k - true_ranking.index(cv_id)  # más alto si está antes en el ranking real
    return ndcg_score([relevance], [relevance])

# ===============================
# Código principal
# ===============================

def read_txt(file_path: str) -> str:
    """Lee un archivo de texto y devuelve su contenido."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def get_best_cvs(
    job_description: str,
    faiss_path: str,
    meta_path: str,
    top_k: int = 5
) -> List[Tuple[int, str, float]]:
    """
    Busca los CVs más similares a una descripción de trabajo dada utilizando FAISS y un modelo de embeddings.
    """
    model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", device="cpu")
    #model = SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1", device="cpu")

    # Load FAISS index
    index = faiss.read_index(faiss_path)

    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)

    resume_ids = metadata["ids"]
    resume_texts = metadata["texts"]

    # Encode JD
    query_emb = model.encode([job_description], normalize_embeddings=True)
    D, I = index.search(query_emb, k=top_k)

    # Higher similarity → closer to 1
    scores = D[0]

    return [(resume_ids[idx], resume_texts[idx], scores[i]) for i, idx in enumerate(I[0])]

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
        "cv_db_abog_alto/cv_index.faiss",
        "cv_db_arq_alto/cv_index.faiss",
        "cv_db_eco_alto/cv_index.faiss",
        "cv_db_med_alto/cv_index.faiss",
        "cv_db_prof_alto/cv_index.faiss"
    ]

    meta_paths = [
        "cv_db_abog_alto/cv_metadata.pkl",
        "cv_db_arq_alto/cv_metadata.pkl",
        "cv_db_eco_alto/cv_metadata.pkl",
        "cv_db_med_alto/cv_metadata.pkl",
        "cv_db_prof_alto/cv_metadata.pkl"
    ]

    all_mrr = []
    all_ndcg = []
    all_spearman = []

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
            predicted_ids = [cv_id for cv_id, _, _ in best_cvs]
            true_ranking = GROUND_TRUTH_RANKINGS[title]

            mrr = compute_mrr(true_ranking, predicted_ids)
            ndcg = compute_ndcg(true_ranking, predicted_ids)
            spearman_corr = compute_spearman(true_ranking, predicted_ids)

            all_mrr.append(mrr)
            all_ndcg.append(ndcg)
            all_spearman.append(spearman_corr)

            print(f"\nResultados para {title}:")
            for rank, (cv_id, _, score) in enumerate(best_cvs, start=1):
                print(f"#{rank} → CV ID: {cv_id} | Similaridad: {score:.4f}")

            print(f"✅ MRR: {mrr:.4f}")
            print(f"✅ NDCG: {ndcg:.4f}")
            print(f"✅ Spearman: {spearman_corr:.4f}")

        else:
            print(f"No se encontraron CVs para el puesto de {title}.")

    if all_mrr:
        print("\n===== MÉTRICAS PROMEDIO =====")
        print(f"🔹 MRR promedio: {np.mean(all_mrr):.4f}")
        print(f"🔹 NDCG promedio: {np.mean(all_ndcg):.4f}")
        print(f"🔹 Spearman promedio: {np.mean(all_spearman):.4f}")

        # Hacer un gráfico de barras de Spearman, MRR y DCG
        plt.figure(figsize=(6, 6))
        # en negrita lo que este escrito en los ejes
        plt.bar(['Spearman', 'MRR', 'nDCG'], [np.mean(all_spearman), np.mean(all_mrr), np.mean(all_ndcg)], color=['green', 'green', 'green'], alpha=1)
        plt.ylabel('Score')
        plt.ylim(0, 1)
        plt.grid(axis='y', linestyle='--', alpha=1)
        plt.savefig('synthetic_data_validation_results_alto.png')
        plt.show()

if __name__ == "__main__":
    main()
