import tqdm
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

async def generate_recommendation(job_description_txt_text: str, candidate_text: str):
    """
    Genera una recomendación sobre si un candidato es adecuado para un trabajo basado en la descripción del trabajo y el texto del candidato.
    
    Args:
        job_description_txt_text (str): Descripción del trabajo.
        candidate_text (str): Texto del candidato.
    
    Returns:
        str: Recomendación sobre si el candidato es adecuado para el trabajo.
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


def get_contact_info(candidate_id, cv_info_path):
    """
    Obtiene la información de contacto de un candidato dado su ID.
    
    Args:
        candidate_id (str): ID del candidato.
        cv_info_path (str): Ruta al archivo CSV que contiene la base de datos de candidatos.
    
    Returns:
        tuple: Nombre, email y teléfono del candidato.
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


def save_recommendations_to_csv(recommendations, csv_path):
    """
    Guarda las recomendaciones en un archivo csv
    
    Args:
        recommendations (list): Lista de diccionarios con las recomendaciones.
        csv_path (str): Ruta donde se guardará el archivo csv.
    """
    df = pd.DataFrame(recommendations)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"Recomendaciones guardadas en {csv_path}")


def get_candidates_and_recomendations(job_description_txt, cv_info_path, faiss_path, meta_path, rank_and_recom_path, top_k=3):
    """
    Busca los CVs más similares a una descripción de trabajo dada utilizando FAISS y un modelo de embeddings. Luego, genera recomendaciones 
    mediante un modelo de lenguaje para determinar si los candidatos son adecuados para el trabajo y por qué razones. Estas recomendaciones 
    se guardan en un archivo .csv
    
    Args:
        job_description_txt (str): Descripción del trabajo para la cual se buscan CVs.
        faiss_path (str): Ruta al índice FAISS.
        meta_path (str): Ruta al archivo de metadatos.
        top_k (int): Número de CVs a retornar.
    
    Returns:
        CREATES a csv file with the top_k candidates and opinions about if they are suitable for the job or not.
        The csv file will contain the following columns:
        - cv_id
        - candidate_name
        - candidate_text
        - recommendation
    """
    print("Starting candidate search and recommendation generation...")
    # Obtener los mejores CVs
    best_cvs = get_best_candidates(job_description_txt, faiss_path, meta_path, top_k)
    print(f"Top {top_k} candidates found for the job description.")
    # Generar recomendaciones para cada CV
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
    # Guardar las recomendaciones en un archivo CSV
    save_recommendations_to_csv(recommendations, rank_and_recom_path)






# if __name__ == "__main__":
#     job_description_txt = "We are looking for an IT Support Specialist with experience in healthcare environments, " \
#     "particularly with Epic Systems. The role involves providing technical assistance to clinical staff, supporting " \
#     "and maintaining EMR systems, resolving hardware and software issues, and training end-users. Strong communication " \
#     "skills, knowledge of networks and databases, and prior experience in hospitals or government institutions are highly valued."
#     top_k_candidates = 3
#     get_candidates_and_recomendations(job_description_txt, top_k=top_k_candidates)
    