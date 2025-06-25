from sentence_transformers import SentenceTransformer, util

# Load the model
model = SentenceTransformer("sentence_transformer/mini_finetuned_Allmini")

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