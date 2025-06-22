import tqdm
import pandas as pd
import asyncio
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from openai import AsyncAzureOpenAI

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



def get_cvs_and_recomendations(job_description, faiss_path="../rag/cv_vector_db/cv_index.faiss", 
                               meta_path="../rag/cv_vector_db/cv_metadata.pkl", top_k=3,
                               opinion_csv_path="../rag/cv_vector_db/reviews_of_candidates.csv",
                        candidates_db_path="../rag/cvs.csv"):
    """
    Busca los CVs más similares a una descripción de trabajo dada utilizando FAISS y un modelo de embeddings. Luego, genera recomendaciones 
    mediante un modelo de lenguaje para determinar si los candidatos son adecuados para el trabajo y por qué razones. Estas recomendaciones 
    se guardan en un archivo .csv
    
    Args:
        job_description (str): Descripción del trabajo para la cual se buscan CVs.
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

    # Obtener los mejores CVs
    best_cvs = get_best_cvs(job_description, faiss_path, meta_path, top_k)
    print(f"🔍 Encontrados {len(best_cvs)} CVs similares a la descripción del trabajo.")

    # Generar recomendaciones para cada CV
    recommendations = []
    for cv_id, candidate_text in tqdm.tqdm(best_cvs, desc="Generando recomendaciones", unit="CV"):
        recommendation = asyncio.run(generate_recommendation(job_description, candidate_text))
        name, email, phone = get_contact_info(cv_id, candidates_db_path)
        recommendations.append({
            "cv_id": cv_id,
            "candidate_name": name,
            "email": email,
            "phone": phone,
            "candidate_text": candidate_text,
            "recommendation": recommendation
        })
    # Guardar las recomendaciones en un archivo CSV
    save_recommendations_to_csv(recommendations, opinion_csv_path)
    print(f"✅ Recomendaciones guardadas en {opinion_csv_path}")



async def generate_recommendation(job_description, candidate_text):
    """
    Genera una recomendación sobre si un candidato es adecuado para un trabajo basado en la descripción del trabajo y el texto del candidato.
    
    Args:
        job_description (str): Descripción del trabajo.
        candidate_text (str): Texto del candidato.
    
    Returns:
        str: Recomendación sobre si el candidato es adecuado para el trabajo.
    """

    
    API_KEY = "8U02J0d4710ZcPDqs9J6cWj7l1CDWKv8Yg8sWRO4eLwLEtsIOfDSJQQJ99BFACHYHv6XJ3w3AAAAACOGRHrr"
    ENDPOINT = "https://fausp-mbmvwtiw-eastus2.cognitiveservices.azure.com/"
    DEPLOYMENT = "gpt-4o-mini-faus"
    VERSION = "2024-12-01-preview"

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

    client = AsyncAzureOpenAI(
        api_key=API_KEY,
        api_version=VERSION,
        azure_endpoint=ENDPOINT
    )

    user_message = f"""Job Description:\n{job_description}\n\nCandidate Text:\n{candidate_text}"""

    response = await client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.3,
        max_tokens=800
    )

    # Extraer el contenido de la respuesta
    recommendation = response.choices[0].message.content.strip()
    return recommendation


def get_contact_info(candidate_id, candidates_db_path):
    """
    Obtiene la información de contacto de un candidato dado su ID.
    
    Args:
        candidate_id (str): ID del candidato.
        candidates_db_path (str): Ruta al archivo CSV que contiene la base de datos de candidatos.
    
    Returns:
        tuple: Nombre, email y teléfono del candidato.
    """
    df = pd.read_csv(candidates_db_path)
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


if __name__ == "__main__":
    job_description = "We are looking for an IT Support Specialist with experience in healthcare environments, " \
    "particularly with Epic Systems. The role involves providing technical assistance to clinical staff, supporting " \
    "and maintaining EMR systems, resolving hardware and software issues, and training end-users. Strong communication " \
    "skills, knowledge of networks and databases, and prior experience in hospitals or government institutions are highly valued."
    top_k_candidates = 3
    get_cvs_and_recomendations(job_description, top_k=top_k_candidates)
    