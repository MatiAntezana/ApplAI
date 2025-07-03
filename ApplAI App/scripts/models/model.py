import os
import asyncio
import pickle
import faiss
from sentence_transformers import SentenceTransformer, util
from .database_processing import append_to_csv, append_to_faiss, extract_cv_info

# Load the model
model = SentenceTransformer("sentence_transformer/mini_finetuned_Allmini")

# Function that uses the model
def calculate_score(ai_text: str, job_text: str) -> float:
    """
    Calculate the similarity score between the AI text and job description text.

    Parameters
    ----------
    ai_text : str
        The text of the AI or CV.
    job_text : str
        The text of the job description.

    Returns
    -------
    float
        The similarity score between the AI text and job description text.
    """
    cv_embedding = model.encode(ai_text, convert_to_tensor=True)
    job_description_embedding = model.encode(job_text, convert_to_tensor=True)
    return util.cos_sim(cv_embedding, job_description_embedding)


def save_ai_in_db(ai_txt_file: str, cv_info_path: str, faiss_path: str, meta_path: str) -> None:
    """ 
    Save the AI text from a file into the database, including CSV and FAISS index.

    Parameters
    ----------
    ai_txt_file : str
        Path to the text file containing the AI or CV information.
    cv_info_path : str
        Path to the CSV file where the AI information will be saved.
    faiss_path : str
        Path to the FAISS index file where the AI embeddings will be stored.
    meta_path : str
        Path to the metadata file for the FAISS index.

    Returns
    -------
    None
    """

    if not isinstance(ai_txt_file, str) or not ai_txt_file.strip():
        raise ValueError("Invalid file path provided.")
    if not os.path.isfile(ai_txt_file):
        raise FileNotFoundError(f"File not found: {ai_txt_file}")
    
    if not isinstance(cv_info_path, str) or not cv_info_path.strip():
        raise ValueError("Invalid file path provided.")
    if not os.path.isfile(cv_info_path):
        raise FileNotFoundError(f"File not found: {cv_info_path}")

    if not isinstance(faiss_path, str) or not faiss_path.strip():
        raise ValueError("Invalid file path provided.")
    if not os.path.isfile(faiss_path):
        raise FileNotFoundError(f"File not found: {faiss_path}")
    
    if not isinstance(meta_path, str) or not meta_path.strip():
        raise ValueError("Invalid file path provided.")
    if not os.path.isfile(meta_path):
        raise FileNotFoundError(f"File not found: {meta_path}")
    
    with open(ai_txt_file, "r", encoding="utf-8") as f:
        jd_text = f.read()
    
    result = asyncio.run(extract_cv_info(jd_text))
    cv_id = append_to_csv(result, cv_info_path)
    append_to_faiss(cv_id, result.cv_information, model, faiss_path, meta_path)


def get_best_candidates(job_description, faiss_path="cv_vector_db/cv_index.faiss", meta_path="cv_vector_db/cv_metadata.pkl", top_k=3):
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

    # model = SentenceTransformer("all-MiniLM-L6-v2")

    index = faiss.read_index(faiss_path)

    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)

    resume_ids = metadata["ids"]
    resume_texts = metadata["texts"]

    query_emb = model.encode([job_description], normalize_embeddings=True)
    D, I = index.search(query_emb, k=top_k)

    return [(resume_ids[idx], resume_texts[idx]) for idx in I[0]]