import os
import asyncio
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


def save_ai_in_db(ai_txt_file: str, ai_personal_info_path: str, faiss_path: str, meta_path: str) -> None:
    """ 
    Save the AI text from a file into the database, including CSV and FAISS index.

    Parameters
    ----------
    ai_txt_file : str
        Path to the text file containing the AI or CV information.
    ai_personal_info_path : str
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
    
    if not isinstance(ai_personal_info_path, str) or not ai_personal_info_path.strip():
        raise ValueError("Invalid file path provided.")
    if not os.path.isfile(ai_personal_info_path):
        raise FileNotFoundError(f"File not found: {ai_personal_info_path}")

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
    cv_id = append_to_csv(result, ai_personal_info_path)
    append_to_faiss(cv_id, result.cv_information, model, faiss_path, meta_path)