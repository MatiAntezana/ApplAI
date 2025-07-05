import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
from sentence_transformers import SentenceTransformer, util
import torch

def load_data(path):
    """Carga el dataset desde un CSV y retorna listas de textos y etiquetas."""
    df = pd.read_csv(path)
    cvs = df['CV'].tolist()
    jds = df['JD'].tolist()
    scores = df['score'].values
    return cvs, jds, scores


def compute_embeddings(model, sentences, batch_size=32):
    """Computa embeddings para una lista de oraciones usando batching."""
    embeddings = []
    for start in range(0, len(sentences), batch_size):
        batch = sentences[start:start + batch_size]
        emb = model.encode(batch, convert_to_tensor=True)
        embeddings.append(emb)
    return torch.cat(embeddings, dim=0).cpu()
# ...existing code...

def compute_similarity_scores(cv_embs, jd_embs):
    """Computa la similitud coseno entre pares de embeddings correspondientes."""
    scores = util.cos_sim(cv_embs, jd_embs)
    # Solo diagonales, donde cada CV con su JD correspondiente
    return scores.diagonal().cpu().numpy()


def plot_roc(y_true, y_scores, save_path=None):
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr, tpr)
    plt.figure()
    plt.plot(fpr, tpr, label=f'ROC curve (AUC = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc='best')
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()
    plt.close()


def plot_regression_scatter(y_true, y_pred, save_path=None):
    plt.figure(figsize=(6, 6))
    plt.scatter(y_true, y_pred, alpha=0.5, label="Puntos")
    plt.plot([min(y_true), max(y_true)], [min(y_true), max(y_true)], 'r--', label="y = x")
    plt.xlabel("Valor real")
    plt.ylabel("Valor predicho")
    plt.title("Dispersión: Valor real vs. Valor predicho")
    plt.legend()
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()
    plt.close()

def plot_regression_scatter(y_true, y_pred, save_path=None):
    plt.figure(figsize=(6, 6))
    plt.scatter(y_true, y_pred, alpha=0.5, label="Puntos")
    # Línea de identidad
    plt.plot([min(y_true), max(y_true)], [min(y_true), max(y_true)], 'r--', label="y = x")
    # Línea de tendencia (opcional)
    m, b = np.polyfit(y_true, y_pred, 1)
    plt.plot(y_true, m*y_true + b, color='green', label='Tendencia')
    plt.xlabel("Valor real")
    plt.ylabel("Valor predicho")
    plt.title("Dispersión: Valor real vs. Valor predicho")
    plt.legend()
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()
    plt.close()

def main():
    # Ruta al dataset y al modelo finetuneado
    dataset_path = "/Users/matias/4°AÑO/NLP/ApplAI/my_dataset/plain_text_resume_data.csv"
    model_path = "/Users/matias/4°AÑO/NLP/ApplAI/fineTuningAllMiniFinal"

    # Cargar datos
    cvs, jds, scores = load_data(dataset_path)
    cv_train, cv_val, jd_train, jd_val, y_train, y_val = train_test_split(
        cvs, jds, scores, test_size=0.1, random_state=42
    )

    # Cargar modelo
    model = SentenceTransformer(model_path)

    # Computar embeddings de validación
    print("Computing embeddings for CVs...")
    cv_embs_val = compute_embeddings(model, cv_val)
    print("Computing embeddings for JDs...")
    jd_embs_val = compute_embeddings(model, jd_val)

    # Calcular similitud
    print("Computing similarity scores...")
    y_pred = compute_similarity_scores(cv_embs_val, jd_embs_val)

    np.savetxt("y_pred.txt", y_pred)
    np.savetxt("y_val.txt", y_val)

    # Gráficas de evaluación
    print("Plotting Precision-Recall curve...")
    plot_regression_scatter(y_val, y_pred, save_path="regression_scatter.png")

    print("Plotting regression scatter (y real vs. y predicho)...")
    plot_regression_scatter(y_val, y_pred, save_path="regression_scatter.png")

    print("Done. Curvas guardadas como 'roc_curve.png' y 'precision_recall_curve.png'.")

if __name__ == "__main__":
    main()
