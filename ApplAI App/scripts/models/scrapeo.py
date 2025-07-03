import asyncio
import aiohttp
import re
import os
from typing import Dict, List, Optional
from openai import AzureOpenAI
import logging
import json
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Azure OpenAI Configuration
ENDPOINT   = "https://fausp-mbmvwtiw-eastus2.cognitiveservices.azure.com/"
API_KEY    = "8U02J0d4710ZcPDqs9J6cWj7l1CDWKv8Yg8sWRO4eLwLEtsIOfDSJQQJ99BFACHYHv6XJ3w3AAAAACOGRHrr"
DEPLOYMENT = "gpt-4o-mini-faus"

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=ENDPOINT,
    api_key=API_KEY
)

# Enrich Layer API Configuration
ENRICHLAYER_API_KEY = "gf50nq44VEekjpxCtx7ohQ"
ENRICHLAYER_ENDPOINT = "https://enrichlayer.com/api/v2/job"

# Keywords para clasificación
REMOTE_KEYWORDS = ["remote", "remoto", "teletrabajo", "work from home", "home office", "distributed", "anywhere"]
INACTIVE_KEYWORDS = [
    "no longer accepting applications", "job is no longer available",
    "position filled", "job expired", "vacante cerrada", "closed position"
]

def clean_linkedin_url(url: str) -> str:
    """
    Limpia y normaliza URLs de LinkedIn para extraer el job ID específico.
    """
    try:
        # Si es una URL de búsqueda, extraer el currentJobId
        if '/jobs/search/' in url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            if 'currentJobId' in params:
                job_id = params['currentJobId'][0]
                return f"https://www.linkedin.com/jobs/view/{job_id}/"
        
        # Si es una URL de view directa, limpiarla
        elif '/jobs/view/' in url:
            # Extraer solo el job ID
            match = re.search(r'/jobs/view/(\d+)', url)
            if match:
                job_id = match.group(1)
                return f"https://www.linkedin.com/jobs/view/{job_id}/"
        
        # Si ya es una URL limpia, devolverla tal como está
        return url
        
    except Exception as e:
        logger.warning(f"Error al limpiar URL {url}: {e}")
        return url

def extract_keywords(text: str, keyword_list: List[str]) -> bool:
    """
    Verifica si alguna palabra clave está presente en el texto.
    """
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keyword_list)

def extract_responsibilities(text: str) -> List[str]:
    """
    Extrae responsabilidades de texto con viñetas.
    """
    if not text:
        return []
    
    lines = text.split('\n')
    bullets = []
    
    for line in lines:
        # Buscar líneas que empiecen con viñetas o guiones
        if re.search(r'^\s*[-•*]\s+', line) or re.search(r'^\s*\d+\.\s+', line):
            clean_line = re.sub(r'^\s*[-•*\d.]\s*', '', line).strip()
            if len(clean_line) > 20:  # Solo responsabilidades sustanciales
                bullets.append(clean_line)
    
    return bullets[:10]  # Máximo 10 responsabilidades

def extract_skills_advanced(text: str) -> List[str]:
    """
    Extrae skills técnicos usando patrones más sofisticados.
    """
    if not text:
        return []
    
    # Patrones mejorados para detectar skills
    skills_patterns = [
        # Lenguajes de programación
        r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin|Scala|R|MATLAB|SQL|HTML|CSS)\b',
        # Frameworks y librerías
        r'\b(React|Angular|Vue|Node\.js|Django|Flask|Spring|Laravel|Rails|Express|FastAPI|TensorFlow|PyTorch|Pandas|NumPy)\b',
        # Bases de datos
        r'\b(MySQL|PostgreSQL|MongoDB|Redis|SQLite|Oracle|SQL Server|Elasticsearch|Cassandra|DynamoDB)\b',
        # Cloud y DevOps
        r'\b(AWS|Azure|GCP|Google Cloud|Docker|Kubernetes|Jenkins|GitLab|GitHub|Terraform|Ansible)\b',
        # Herramientas de desarrollo
        r'\b(Git|Jira|Confluence|Postman|Swagger|Visual Studio|IntelliJ|Eclipse)\b',
        # Metodologías
        r'\b(Agile|Scrum|Kanban|DevOps|CI/CD|TDD|BDD|REST|GraphQL|Microservices|Machine Learning|AI|Data Science)\b',
        # Skills de cocina (para el caso específico)
        r'\b(cocina|cocinero|chef|gastronomía|panadería|repostería|servicio|restaurante|menú|ingredientes)\b'
    ]
    
    skills = set()
    for pattern in skills_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        skills.update(matches)
    
    return sorted(list(skills))

def extract_education_requirements(text: str) -> Optional[str]:
    """
    Extrae requisitos educativos del texto.
    """
    if not text:
        return None
    
    edu_patterns = [
        r'\b(Bachelor|Master|PhD|Doctorate|Degree|Diploma|Certificate)\b.*?(?:in\s+)?([A-Za-z\s]+)',
        r'\b(Computer Science|Engineering|Mathematics|Statistics|Business|Marketing|Finance|Economics)\b',
        r'\b(licenciatura|ingeniería|maestría|doctorado|grado|título|secundaria|primaria|bachillerato)\b',
        r'\b(culinary|gastronomía|hotelería|turismo|administración)\b'
    ]
    
    for pattern in edu_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    
    return None

def extract_experience_level(text: str, seniority_level: str = None) -> str:
    """
    Extrae nivel de experiencia requerido.
    """
    if seniority_level:
        return seniority_level
    
    if not text:
        return "Not specified"
    
    experience_patterns = [
        (r'(\d+)\+?\s*(?:years?|años?)\s*(?:of\s*)?(?:experience|experiencia)', 'numeric'),
        (r'\b(entry|junior|mid|senior|lead|principal|director)\b', 'level'),
        (r'\b(trainee|intern|graduate|experienced|expert|principiante|experimentado)\b', 'level')
    ]
    
    for pattern, pattern_type in experience_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1) if pattern_type == 'numeric' else match.group(0)
    
    return "Not specified"

async def scrape_linkedin_job_with_enrichlayer(link: str, api_key: str = None) -> Dict:
    """
    Scrape job usando Enrich Layer API de forma asíncrona con manejo mejorado de errores.
    """
    if not api_key:
        api_key = ENRICHLAYER_API_KEY
    
    # Limpiar y normalizar la URL
    clean_url = clean_linkedin_url(link)
    logger.info(f"URL original: {link}")
    logger.info(f"URL limpia: {clean_url}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    params = {"url": clean_url}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                ENRICHLAYER_ENDPOINT, 
                headers=headers, 
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                response_text = await response.text()
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                if response.status == 400:
                    logger.error(f"Bad Request (400) para URL: {clean_url}")
                    logger.error(f"Response body: {response_text}")
                    return {
                        "error": f"Bad Request: La URL {clean_url} no es válida o no está disponible",
                        "status_code": 400,
                        "details": response_text
                    }
                
                if response.status == 401:
                    logger.error("API key inválida o expirada")
                    return {
                        "error": "API key inválida o expirada",
                        "status_code": 401
                    }
                
                if response.status == 429:
                    logger.error("Rate limit excedido")
                    return {
                        "error": "Rate limit excedido. Intenta más tarde",
                        "status_code": 429
                    }
                
                if response.status != 200:
                    logger.error(f"API request failed with status {response.status}")
                    return {
                        "error": f"API request failed with status {response.status}",
                        "status_code": response.status,
                        "details": response_text
                    }
                
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    return {
                        "error": f"Invalid JSON response: {str(e)}",
                        "raw_response": response_text
                    }
                
                # Extraer información relevante
                job_description = data.get('job_description', '')
                company_info = data.get('company', {})
                location_info = data.get('location', {})
                salary_info = data.get('salary', {})
                
                # Procesar información
                is_remote = (
                    data.get('remote_allowed', False) or 
                    extract_keywords(job_description, REMOTE_KEYWORDS) or
                    extract_keywords(data.get('work_arrangement', ''), REMOTE_KEYWORDS)
                )
                
                is_active = not extract_keywords(job_description, INACTIVE_KEYWORDS)
                
                responsibilities = extract_responsibilities(job_description)
                skills = extract_skills_advanced(job_description)
                education = extract_education_requirements(job_description)
                experience_level = extract_experience_level(job_description, data.get('seniority_level'))
                
                # Formatear ubicación
                location_parts = [
                    location_info.get('city', ''),
                    location_info.get('state', ''),
                    location_info.get('country', '')
                ]
                location = ', '.join(filter(None, location_parts)) or location_info.get('name', '')
                
                # Formatear salario
                salary_text = "Not specified"
                if salary_info:
                    min_sal = salary_info.get('min')
                    max_sal = salary_info.get('max')
                    currency = salary_info.get('currency', '')
                    period = salary_info.get('period', '')
                    
                    if min_sal and max_sal:
                        salary_text = f"{currency} {min_sal:,} - {max_sal:,} per {period}"
                    elif min_sal:
                        salary_text = f"{currency} {min_sal:,}+ per {period}"
                
                return {
                    "title": data.get('job_title', ''),
                    "company": company_info.get('name', ''),
                    "location": location,
                    "description": job_description,
                    "is_remote": is_remote,
                    "is_active": is_active,
                    "responsibilities": responsibilities,
                    "skills": skills,
                    "education": education,
                    "experience_level": experience_level,
                    "employment_type": data.get('employment_type', ''),
                    "salary": salary_text,
                    "total_applicants": data.get('total_applicants', 0),
                    "posted_date": data.get('posted_date', ''),
                    "easy_apply": data.get('easy_apply', False),
                    "job_url": data.get('job_url', clean_url),
                    "company_size": company_info.get('company_size', ''),
                    "industry": company_info.get('industry', ''),
                    "original_url": link,
                    "cleaned_url": clean_url,
                    "raw_data": data  # Para debugging
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error al acceder a {clean_url}: {e}")
            return {"error": f"Network error: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {"error": f"JSON decode error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error inesperado al procesar {clean_url}: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

def build_summary_prompt(job: Dict) -> str:
    """
    Construye prompt para generar resumen del trabajo.
    """
    # Formatear información para el prompt
    remote_status = "Remote" if job.get('is_remote') else "On-site"
    skills_text = ', '.join(job.get('skills', [])[:8])  # Máximo 8 skills
    responsibilities_text = '. '.join(job.get('responsibilities', [])[:3])  # Máximo 3 responsabilidades
    
    return f"""
You are an assistant that reads a job posting and produces a concise single-paragraph summary covering the key highlights.

Job details:
• Title: {job.get('title', 'N/A')}
• Company: {job.get('company', 'N/A')}
• Location: {job.get('location', 'N/A')}
• Work arrangement: {remote_status}
• Employment type: {job.get('employment_type', 'N/A')}
• Experience level: {job.get('experience_level', 'N/A')}
• Salary: {job.get('salary', 'N/A')}
• Key responsibilities: {responsibilities_text or 'N/A'}
• Required skills: {skills_text or 'N/A'}
• Education: {job.get('education', 'N/A')}
• Total applicants: {job.get('total_applicants', 'N/A')}

Task:
Write one brief paragraph (2-3 sentences) that summarizes the role, highlighting the company, location/remote status, key responsibilities, required skills, and any standout details like salary or experience level. Use plain, professional English without bullet points.
""".strip()

def summarize_job_with_azure(job: Dict) -> str:
    """
    Genera resumen del trabajo usando Azure OpenAI.
    """
    try:
        prompt = build_summary_prompt(job)
        
        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes job postings concisely and professionally."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error al generar resumen: {e}")
        return f"Error generating summary: {str(e)}"

async def scrape_and_summarize(link: str, api_key: str = None) -> Dict:
    """
    Scrape job information y genera resumen con manejo mejorado de errores.
    """
    try:
        # Scrape job data
        job_data = await scrape_linkedin_job_with_enrichlayer(link, api_key)
        
        # Verificar si hay error
        if "error" in job_data:
            return {
                "job": {},
                "summary": f"Error: {job_data['error']}",
                "error": job_data['error'],
                "status_code": job_data.get('status_code'),
                "original_url": link
            }
        
        # Validar datos mínimos
        if not job_data.get('title') and not job_data.get('company'):
            logger.warning(f"Datos insuficientes extraídos de {link}")
            return {
                "job": job_data,
                "summary": "Información limitada disponible para esta oferta de trabajo.",
                "warning": "Insufficient data extracted",
                "original_url": link
            }
        
        # Generar resumen
        try:
            summary = summarize_job_with_azure(job_data)
        except Exception as e:
            logger.error(f"Error al generar resumen para {link}: {e}")
            summary = f"Error generating summary: {str(e)}"
        
        # Limpiar datos sensibles antes de retornar
        job_data_clean = job_data.copy()
        if 'raw_data' in job_data_clean:
            del job_data_clean['raw_data']
        if 'description' in job_data_clean and len(job_data_clean['description']) > 500:
            job_data_clean['description'] = job_data_clean['description'][:500] + "..."
        
        return {
            "job": job_data_clean,
            "summary": summary,
            "status": "success",
            "original_url": link
        }
        
    except Exception as e:
        logger.error(f"Error general al procesar {link}: {e}")
        return {
            "job": {},
            "summary": f"Error procesando la oferta: {str(e)}",
            "error": str(e),
            "original_url": link
        }

# Función auxiliar para procesar múltiples URLs
async def scrape_multiple_jobs(urls: List[str], api_key: str = None) -> List[Dict]:
    """
    Procesa múltiples URLs de trabajos de forma concurrente.
    """
    tasks = [scrape_and_summarize(url, api_key) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                "job": {},
                "summary": f"Error processing URL {urls[i]}: {str(result)}",
                "error": str(result),
                "original_url": urls[i]
            })
        else:
            processed_results.append(result)
    
    return processed_results