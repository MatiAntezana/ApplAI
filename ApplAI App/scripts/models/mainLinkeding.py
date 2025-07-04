import os
from openai import AzureOpenAI
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util
from huggingface_hub import login
import json
import re
import requests
from .scrapeo import scrape_and_summarize
import asyncio
# from searchUrls import search_jobs_serpapi_verified
from .searchUrl import search_jobs_serpapi_verified

# ── Configuración de Azure OpenAI ──────────────────────────────────────────────
ENDPOINT = "https://fausp-mbmvwtiw-eastus2.cognitiveservices.azure.com/"
API_KEY = "8U02J0d4710ZcPDqs9J6cWj7l1CDWKv8Yg8sWRO4eLwLEtsIOfDSJQQJ99BFACHYHv6XJ3w3AAAAACOGRHrr"
DEPLOYMENT = "gpt-4o-mini-faus"

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=ENDPOINT,
    api_key=API_KEY
)

PROMPT_TEMPLATE = """
You will receive a resume in raw text format. Your task is to:

1. Extract the candidate’s name.
2. Extract the candidate’s email address.
3. Extract the candidate’s phone number.
4. Analyze the candidate’s background (education, skills, experience, roles, industries, etc.) and craft **one concise keyword search string** (single line) for LinkedIn Jobs.
5. Extract a cleaned and structured version of the resume that removes any personal contact information (name, email, phone, address, LinkedIn, etc.).

For de fourth part:
- Contain only the most relevant **job title(s)** plus 3-5 **key skills / industry terms**, all separated by single spaces.
- **DO NOT** use Boolean operators (AND, OR, NOT), parentheses, quotation marks, plus signs, or any other special characters.
- **DO NOT** include personal identifiers (name, email, phone, etc.).
- Write it in the same language that predominates in the résumé (Spanish or English).
- Remember: the calling function will later append `site:linkedin.com/jobs`; you only output the keywords.

For the fifth part:
- Do NOT summarize or omit key content.
- Instead, preserve as much of the original job-related information as possible.
- Reorganize and rephrase disconnected items into full sentences with proper structure and connectors (e.g., “The candidate worked at...”, “They were responsible for...”, “Their skills include...”).
- You may rewrite bullet points and lists as prose, but keep all relevant details intact.
- Do NOT include any personal identifiers or contact information.
- Imagine you are preparing the resume for analysis by an AI model - you want to keep the full context but make it more readable.

You may use the following fields **only if present** in the text:
- Career Objective
- Skills
- Institution
- Degree
- Results
- Field of Study
- Companies
- Job Skills
- Positions
- Responsibilities
- Organizations
- Roles
- Languages
- Proficiency
- Certifications

Respond **only** with a valid JSON object, without additional text or explanations


Exact structure of the output:

{{
"area_job":"...",
"cv_information":"..."
}}

CV TEXT:
{cv_text}
"""

# ── SerpApi Search ──────────────────────────────────────────────────────────────
SERPAPI_API_KEYS = [
    "1a992f2a6dbaed0c95203a2ed73768f29b4b7f423a5f218c4834e355c5c31918" # tizi
    # "e898c7f95cdb5692528a009eb2ee7d08d24a2f37c22f9623a065a96fd6072892", # mati
    # "141d74f945c81589527847238881362de5f08cc31dae86209dcb2c04d7e5ccc7", # faus
    # "c18acdb7b9b75162b53059cd6f094669c33323e898758841176351ac8a59e8c7" # giaco
]

def safe_json_load(content: str):
    opens = content.count('{')
    closes = content.count('}')
    if closes < opens:
        content = content + '"' + '}' * (opens - closes)
    return json.loads(content)


def generate_linkedin_query(cv_text: str) -> str:
    prompt = PROMPT_TEMPLATE.format(cv_text=cv_text)
    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=256
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```json"):
            content = content.removeprefix("```json").removesuffix("```").strip()
    elif content.startswith("```"):
            content = content.removeprefix("```").removesuffix("```").strip()

    data = safe_json_load(content)
    area_job = data.get("area_job", "")
    cv_information = data.get("cv_information", "")

    return [area_job, cv_information]

def pdf_a_string(ruta_pdf):
    doc = fitz.open(ruta_pdf)
    contenido = ""
    for pagina in doc:
        contenido += pagina.get_text()
    doc.close()
    return contenido

def scrape_job_pages(urls: list) -> dict:
    scraped = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            scraped[url] = text
        except Exception as e:
            scraped[url] = f"Error: {e}"
    return scraped

def build_job_description_prompt(job):
    """Builds a prompt that generates a professional job description from job data."""
    return f"""
    You are given the following job information:

    - Job Position: "{job.get('title', '')}"
    - Company: "{job.get('company', '')}"
    - Location: "{job.get('location', '')}"
    - Education: "{job.get('education', '')}"
    - Responsibilities: {', '.join(job.get('responsibilities', []))}
    - Skills: {', '.join(job.get('skills', []))}

    Task:
    Generate a SINGLE, well-written `job_description` in plain, professional English.
    - Use the position, company, location, education, responsibilities, and skills provided.
    - Maintain a natural, human-readable style.
    - Do NOT invent any details beyond what's given.

    Example format:
    "The position is for a [Job Position] at [Company], located in [Location], requiring a candidate with an educational background in [Education]. The role involves key responsibilities such as [Responsibility 1], [Responsibility 2], and [Responsibility N]. The required skills for this role include [Skill 1], [Skill 2], and [Skill N]."

    Now generate the `job_description`.
    """

def filter_url(list_jobs):
  N = len(list_jobs)
  list_results = []
  for idx in range(N):
    response = client.chat.completions.create(
      model=DEPLOYMENT,  # o el modelo que tengas en Azure
      temperature=0.3,
      max_tokens=800,
      messages=[
          {"role": "system", "content": "You are a job filtering and summarizing assistant."},
          {"role": "user", "content": build_job_description_prompt(list_jobs[idx])}
      ]
    )
    result = response.choices[0].message.content
    list_results.append(result)

  return list_results


def predict(cv_desc, jb_desc, model):
    embedding1 = model.encode(cv_desc, convert_to_tensor=True)
    embedding2 = model.encode(jb_desc, convert_to_tensor=True)

    return util.cos_sim(embedding1, embedding2)

def extract_job_title(description: str) -> str:
    """
    Llama al modelo para extraer un título de puesto en pocas palabras
    a partir de la descripción completa.
    """
    system_prompt = (
        "Eres un asistente que extrae, de forma muy concisa, "
        "el título de un puesto a partir de su descripción completa."
    )
    user_prompt = (
        "Dada la siguiente descripción de puesto, devuelve SOLO el título en pocas palabras:\n\n"
        f"{description}"
    )

    response = client.chat.completions.create(
        model=DEPLOYMENT,       # <— aquí va el nombre/deployment id del modelo
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        temperature=0.0,
        max_tokens=16,
    )

    title = response.choices[0].message.content.strip()
    return title


# Test workflow completo
async def test_all(cv_path: str, modelPath: str, max_urls: int = 10):
    model = SentenceTransformer(modelPath)

    cv_text = pdf_a_string(cv_path)
    
    area_job, cv_information = generate_linkedin_query(cv_text)

    links = search_jobs_serpapi_verified(area_job, max_urls=max_urls, antiguedad_maxima='mes')
   
    data_job, summary = [], []
    for url in links:
        cm = await scrape_and_summarize(url) # Await the coroutine to get the result
        data_job.append(cm.get("job", {}))
        summary.append(cm.get("summary", ""))

    summaries = filter_url(data_job)
    scores = [predict(cv_information, s, model) for s in summaries]
    sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    sorted_scores   = [scores[i]     for i in sorted_indices]
    sorted_summaries= [summaries[i]  for i in sorted_indices]
    
    print(sorted_scores)

    sorted_links = [links[i]   for i in sorted_indices]

    titulos = []
    for summari_final in sorted_summaries:
        titulo = extract_job_title(summari_final)
        titulos.append(titulo)

    print("Titulos:", titulos)

    return titulos, sorted_links, sorted_summaries



# if __name__ == '__main__':
#     # Ejemplo de ejecución
#     # a, b, c = asyncio.run(test_all('/Users/matias/4°AÑO/NLP/ApplAI/cvs/tizi_cv.pdf', '/Users/matias/4°AÑO/NLP/ApplAI/fineTuningAllMiniFinal', max_urls=3))
