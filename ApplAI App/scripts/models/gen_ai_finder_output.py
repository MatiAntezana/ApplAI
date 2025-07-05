import pandas as pd
import asyncio
from openai import AsyncAzureOpenAI
from .model import get_best_candidates

# Configuration for Azure OpenAI
API_KEY = "8U02J0d4710ZcPDqs9J6cWj7l1CDWKv8Yg8sWRO4eLwLEtsIOfDSJQQJ99BFACHYHv6XJ3w3AAAAACOGRHrr"
ENDPOINT = "https://fausp-mbmvwtiw-eastus2.cognitiveservices.azure.com/"
DEPLOYMENT = "gpt-4o-mini-faus"
VERSION = "2024-12-01-preview"

client = AsyncAzureOpenAI(
    api_key=API_KEY,
    api_version=VERSION,
    azure_endpoint=ENDPOINT
)

async def generate_recommendation(job_description_txt_text: str, candidate_text: str) -> str:
    """
    Generates a recommendation for a candidate based on the job description and the candidate's text.

    Parameters
    ----------
    job_description_txt_text : str
        The job description text to evaluate against.
    candidate_text : str
        The candidate's text, which may include their resume, experience, skills, education, etc

    Returns
    -------
    str
        A formatted evaluation report that includes the candidate's fit level, strengths, and missing areas.
    """

    SYSTEM_PROMPT = """
    You are an expert in human resources and talent acquisition. Your task is to evaluate whether a candidate is a good fit for a given job description.

    You will be provided with:
    1. A job description.
    2. The candidate’s text (which may contain their resume, experience, skills, education, etc.).

    Your response should include:
    - A clear evaluation of how well the candidate matches the job description.
    - A list of the main strengths: what parts of the job description the candidate satisfies or excels at.
    - A list of key gaps or missing elements that would be important to fulfill the role.

    Be specific. Do not make vague statements like "the candidate is good." Base your reasoning directly on the content.

    Format your response like this:

    --- Evaluation Report ---
    Job Title: [detected from job description, or inferred]
    Candidate Fit Level: [Strong Fit / Partial Fit / Not a Good Fit]

    Strengths:
    - ...
    - ...

    Missing or Weak Areas:
    - ...
    - ...

    ---------------------------

    Now evaluate the following candidate:
    """

    user_message = f"""Job Description:\n{job_description_txt_text}\n\nCandidate Text:\n{candidate_text}"""

    response = await client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.3,
        max_tokens=800
    )

    recommendation = response.choices[0].message.content.strip()
    return recommendation


def get_contact_info(candidate_id: str, cv_info_path: str) -> tuple:
    """
    Gets the contact information of a candidate from a CSV file based on their ID.

    Parameters
    ----------
    candidate_id : str
        The ID of the candidate whose contact information is to be retrieved.
    cv_info_path : str
        The path to the CSV file containing candidate information.

    Returns
    -------
    tuple
        A tuple containing the candidate's name, email, and phone number. If the candidate is not found, returns "Not Found" for each field.
    """
    df = pd.read_csv(cv_info_path)
    candidate_row = df[df['id'] == candidate_id]
    
    if not candidate_row.empty:
        name = candidate_row['name'].values[0]
        email = candidate_row['email'].values[0]
        phone = candidate_row['phone_number'].values[0]
        return name, email, phone
    else:
        return "Not Found", "Not Found", "Not Found"


def save_recommendations_to_csv(recommendations: list, csv_path: str) -> None:
    """
    Saves the recommendations to a CSV file.
    
    Parameters
    ----------
    recommendations : list
        A list of dictionaries containing the recommendations for each candidate.
    csv_path : str
        The path where the CSV file will be saved.

    Returns
    -------
    None
    """
    df = pd.DataFrame(recommendations)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')


def get_candidates_and_recomendations(job_description_txt: str, 
                                      cv_info_path: str, 
                                      faiss_path: str, 
                                      meta_path: str, 
                                      rank_and_recom_path: str, 
                                      top_k: int = 5) -> None:
    """
    Finds the best candidates for a job description and generates recommendations for each candidate. 

    Parameters
    ----------
    job_description_txt : str
        The job description text to evaluate against.
    cv_info_path : str
        The path to the CSV file containing candidate information.
    faiss_path : str
        The path to the FAISS index file where the AI embeddings are stored.
    meta_path : str
        The path to the metadata file for the FAISS index.
    rank_and_recom_path : str
        The path where the recommendations will be saved as a CSV file.
    top_k : int, optional
        The number of top candidates to retrieve, by default 5.

    Returns
    -------
    None
    """
    # Get the best candidates based on the job description
    best_cvs = get_best_candidates(job_description_txt, faiss_path, meta_path, top_k)
  
    # Generate recommendations for each candidate
    recommendations = []
    for cv_id, candidate_text in best_cvs:
        recommendation = asyncio.run(generate_recommendation(job_description_txt, candidate_text))
        name, email, phone = get_contact_info(cv_id, cv_info_path)
        recommendations.append({
            "cv_id": cv_id,
            "candidate_name": name,
            "email": email,
            "phone": phone,
            "candidate_text": candidate_text,
            "recommendation": recommendation
        })

    # Save the recommendations to a CSV file
    save_recommendations_to_csv(recommendations, rank_and_recom_path)
    