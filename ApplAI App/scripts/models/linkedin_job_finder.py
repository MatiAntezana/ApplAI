from openai import AzureOpenAI
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util
from huggingface_hub import login
import json
import requests
from .linkedin_job_info import scrape_and_summarize
from .search_linkedin_jobs_urls import search_jobs_serpapi_verified

# Configure the Azure OpenAI client
ENDPOINT = "https://fausp-mbmvwtiw-eastus2.cognitiveservices.azure.com/"
API_KEY = "8U02J0d4710ZcPDqs9J6cWj7l1CDWKv8Yg8sWRO4eLwLEtsIOfDSJQQJ99BFACHYHv6XJ3w3AAAAACOGRHrr"
DEPLOYMENT = "gpt-4o-mini-faus"

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=ENDPOINT,
    api_key=API_KEY
)

# Define the deployment for the SentenceTransformer model
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

def safe_json_load(content: str) -> dict:
    """
    Safely loads a JSON string, ensuring it has balanced braces.
    If the string has unbalanced braces, it appends the necessary closing braces.

    Parameters
    ----------
    content : str
        The JSON string to be loaded.
    
    Returns
    -------
    dict
        The parsed JSON object.
    """
    opens = content.count('{')
    closes = content.count('}')
    if closes < opens:
        content = content + '"' + '}' * (opens - closes)
    return json.loads(content)


def generate_linkedin_query(cv_text: str) -> str:
    """
    Generates a LinkedIn search query and structured CV information from the provided CV text.

    Parameters
    ----------
    cv_text : str
        The raw text of the CV to analyze.
    
    Returns
    -------
    list
        A list containing:
        - area_job: A keyword search string for LinkedIn Jobs.
        - cv_information: A cleaned and structured version of the CV text.
    """
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


def scrape_job_pages(urls: list) -> dict:
    """
    Scrapes the text content from a list of job URLs.
    
    Parameters
    ----------
    urls : list
        A list of URLs to scrape.

    Returns
    -------
    dict
        A dictionary where keys are URLs and values are the scraped text content.
    """
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


def build_job_description_prompt(job: dict) -> str:
    """
    Builds a prompt that generates a professional job description from job data.
    
    Parameters
    ----------
    job : dict
        A dictionary containing job information with keys like 'title', 'company', 'location', etc
        and their corresponding values.
    
    Returns
    -------
    str
        A formatted string that serves as a prompt for generating a job description.
    """
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


def filter_url(list_jobs: list) -> list:
    """
    Filters the job URLs to ensure they are valid and contain job postings.
    
    Parameters
    ----------
    list_jobs : list
        A list of dictionaries containing job information, each with a 'url' key.
    
    Returns
    -------
    list
        A filtered list of job URLs that are valid and contain job postings.
    """
    N = len(list_jobs)
    list_results = []
    for idx in range(N):
        response = client.chat.completions.create(
        model=DEPLOYMENT,  
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


def extract_job_title(description: str) -> str:
    """
    Extracts the job title from a given job description using an AI model.

    Parameters
    ----------
    description : str
        The job description from which to extract the title.

    Returns
    -------
    str
        The extracted job title, formatted as a concise string.
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
        model=DEPLOYMENT,      
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        temperature=0.0,
        max_tokens=16,
    )

    title = response.choices[0].message.content.strip()
    return title
