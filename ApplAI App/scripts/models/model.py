import os
import asyncio
import pickle
import faiss
from sentence_transformers import SentenceTransformer, util
from .database_processing import append_to_csv, append_to_faiss, extract_cv_info
from .mainLinkeding import generate_linkedin_query, scrape_and_summarize, search_jobs_serpapi_verified, filter_url, extract_job_title

# Load the models
MODEL_SCORE = SentenceTransformer("sentence_transformer/mini_finetuned_Allmini")

MODEL_DB = SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")

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
    ai_embedding = MODEL_SCORE.encode(ai_text)
    job_description_embedding = MODEL_SCORE.encode(job_text)
    return util.cos_sim(ai_embedding, job_description_embedding)


def save_ai_in_db(ai_txt_path: str, cv_info_path: str, faiss_path: str, meta_path: str) -> None:
    """ 
    Save the AI text from a file into the database, including CSV and FAISS index.

    Parameters
    ----------
    ai_txt_path : str
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

    if not isinstance(ai_txt_path, str) or not ai_txt_path.strip():
        raise ValueError("Invalid file path provided.")
    if not os.path.isfile(ai_txt_path):
        raise FileNotFoundError(f"File not found: {ai_txt_path}")
    
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
    
    with open(ai_txt_path, "r", encoding="utf-8") as f:
        jd_text = f.read()
    
    result = asyncio.run(extract_cv_info(jd_text))
    cv_id = append_to_csv(result, cv_info_path)
    append_to_faiss(cv_id, result.cv_information, MODEL_DB, faiss_path, meta_path)


def get_best_candidates(job_description, faiss_path="cv_vector_db/cv_index.faiss", meta_path="cv_vector_db/cv_metadata.pkl", top_k=3):
    """
    FALTAAAA
    """
    try:
        index = faiss.read_index(faiss_path)

        with open(meta_path, "rb") as f:
            metadata = pickle.load(f)

        resume_ids = metadata["ids"]
        resume_texts = metadata["texts"]

        query_emb = MODEL_DB.encode([job_description], normalize_embeddings=True)
        D, I = index.search(query_emb, k=top_k)

        return [(resume_ids[idx], resume_texts[idx]) for idx in I[0]]
    
    except Exception as e:
        print(f"Error retrieving best candidates: {e}")
        return []


async def find_and_rank_linkedin_jobs(ai_txt_path: str, max_urls: int = 10):
    """
    Find and rank LinkedIn job postings based on the AI text provided.

    Parameters
    ----------
    ai_txt_path : str
        Path to the text file containing the AI or CV information.
    max_urls : int, optional
        Maximum number of job URLs to retrieve, by default 10.

    Returns
    -------
    tuple
        A tuple containing:
        - A list of job titles.
        - A list of job URLs.
        - A list of job summaries.
    """
    with open(ai_txt_path, "r", encoding="utf-8") as f:
        ai_text = f.read()
    
    area_job, cv_information = generate_linkedin_query(ai_text)

    links = search_jobs_serpapi_verified(area_job, max_urls=max_urls, antiguedad_maxima='mes')
   
    data_job, summary = [], []

    for url in links:
        cm = await scrape_and_summarize(url) # Await the coroutine to get the result
        data_job.append(cm.get("job", {}))
        summary.append(cm.get("summary", ""))

    summaries = filter_url(data_job)

    scores = [calculate_score(cv_information, s) for s in summaries]

    sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    # Sort the scores, summaries, and links based on the sorted indices
    sorted_summaries = [summaries[i] for i in sorted_indices]
    sorted_links = [links[i] for i in sorted_indices]

    titulos = []

    for summari_final in sorted_summaries:
        titulo = extract_job_title(summari_final)
        titulos.append(titulo)

    return titulos, sorted_links, sorted_summaries

def get_ideal_linkedin_jobs(ai_txt_path: str, max_urls: int = 10):

    # Agrega los chequeos de path 

    return asyncio.run(find_and_rank_linkedin_jobs(ai_txt_path, max_urls))